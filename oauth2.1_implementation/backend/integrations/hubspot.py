import json
import secrets
import time
import hashlib
from typing import Dict
from fastapi import Request, HTTPException, APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from redis_client import add_key_value_redis, get_value_redis, delete_key_redis
import httpx
import asyncio
import base64
import requests
from integrations.integration_item import IntegrationItem
from loguru import logger
from typing import Any, List
from urllib.parse import urlencode
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration from environment variables
CLIENT_ID = os.getenv('HUBSPOT_CLIENT_ID')
CLIENT_SECRET = os.getenv('HUBSPOT_CLIENT_SECRET')
HUBSPOT_BASE_URL = os.getenv('HUBSPOT_BASE_URL', 'https://api.hubapi.com')
HUBSPOT_TOKEN_URL = os.getenv('HUBSPOT_TOKEN_URL', 'https://api.hubapi.com/oauth/v1/token')
authorization_url = os.getenv('HUBSPOT_AUTH_URL', 'https://app.hubspot.com/oauth/authorize')
REDIRECT_URI = os.getenv('HUBSPOT_REDIRECT_URI', 'http://localhost:8000/integrations/hubspot/oauth2callback')
scope = os.getenv('HUBSPOT_SCOPES', 'crm.objects.contacts.read').split(',')
required_vars = ['HUBSPOT_CLIENT_ID', 'HUBSPOT_CLIENT_SECRET']

missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")


def generate_pkce_parameters() -> Dict[str, str]:
    """Generate PKCE code_verifier and code_challenge"""

    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode('utf-8')).digest()
    ).decode('utf-8').rstrip('=')
    
    return {
        'code_verifier': code_verifier,
        'code_challenge': code_challenge
    }

async def refresh_access_token(user_id: str) -> Dict[str, Any]:
    tokens_raw = await get_value_redis(f"hubspot:tokens:{user_id}")
    if not tokens_raw:
        raise HTTPException(401, "No HubSpot credentials stored")
    tokens = json.loads(tokens_raw)
    logger.debug(f"Retrieved tokens for user {user_id}: {tokens}")
    now = int(time.time())
    if tokens.get("expires_at", 0) <= now:
        refresh_token = tokens.get("refresh_token")
        if not refresh_token:
            raise HTTPException(401, "Missing refresh_token")

        async with httpx.AsyncClient(timeout=30) as client:
            data = {
                "grant_type": "refresh_token",
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "refresh_token": refresh_token,
            }
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            resp = await client.post(HUBSPOT_TOKEN_URL, data=data, headers=headers)
            if resp.status_code != 200:
                raise HTTPException(resp.status_code, f"Refresh failed: {resp.text}")
            new_tokens = resp.json()
            if "refresh_token" not in new_tokens:
                new_tokens["refresh_token"] = refresh_token
            expires_in = int(new_tokens.get("expires_in", 3600))
            new_tokens["obtained_at"] = now
            new_tokens["expires_at"] = now + expires_in - 60
            await add_key_value_redis(
                f"hubspot:tokens:{user_id}",
                json.dumps(new_tokens),
                expire=expires_in + 300,
            )
            tokens = new_tokens
    return tokens


async def authorize_hubspot(user_id: str, org_id: str):
    pkce_params = generate_pkce_parameters()
    await add_key_value_redis(
        f"hubspot:pkce:{user_id}", 
        pkce_params['code_verifier'], 
        expire=600
    )
    logger.debug(f"Stored PKCE code_verifier for user {user_id}")
    
    params = {
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'scope': ' '.join(scope),
        'response_type': 'code',
        'state': user_id,
        'code_challenge': pkce_params['code_challenge'],
        'code_challenge_method': 'S256'
    }
    logger.debug(f"Authorization URL params with PKCE: {params}")
    url = f"{authorization_url}?{urlencode(params)}"
    return JSONResponse({"auth_url": url})

    
async def oauth2callback_hubspot(code: str, state: str = ''):
    logger.info(f"Received code: {code}, state: {state}")
    user_id = state or "default-user"
    code_verifier = await get_value_redis(f"hubspot:pkce:{user_id}")
    if not code_verifier:
        logger.error(f"PKCE code_verifier not found for user {user_id}")
        raise HTTPException(400, "PKCE code_verifier not found or expired")
    logger.debug(f"Retrieved PKCE code_verifier for user {user_id}")
    async with httpx.AsyncClient(timeout=30) as client:
        data = {
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "code": code,
            "code_verifier": code_verifier,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        resp = await client.post(HUBSPOT_TOKEN_URL, data=data, headers=headers)
        if resp.status_code != 200:
            logger.error(f"Token exchange failed: {resp.text}")
            raise HTTPException(resp.status_code, f"Token exchange failed: {resp.text}")
        
        tokens = resp.json()
        now = int(time.time())
        if tokens:
            tokens["obtained_at"] = now
        if "expires_in" in tokens:
            tokens["expires_at"] = now + int(tokens["expires_in"]) - 60
        token_str = json.dumps(tokens)
        await add_key_value_redis(f"hubspot:tokens:{user_id}", token_str, expire=3600)
        logger.info(f"Successfully stored tokens for user {user_id}")
    await delete_key_redis(f"hubspot:pkce:{user_id}")
    html_content = """
    <html>
        <head><title>HubSpot Connected</title></head>
        <body>
            <script>
                window.close();
            </script>
            <p>You can close this window now.</p>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

async def get_hubspot_credentials(user_id: str, org_id: str):
    tokens = await get_value_redis(f"hubspot:tokens:{user_id}")
    if not tokens:
        raise HTTPException(401, "No HubSpot credentials stored")
    tokens = json.loads(tokens)
    response_data = {
        "user_id": user_id,
        "connected": True,
    }
    return JSONResponse(content=response_data)


async def create_integration_item_metadata_object(user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    tokens = await refresh_access_token(user_id)
    access_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    items: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=30, base_url=HUBSPOT_BASE_URL) as client:
        contacts = await client.get(
            "/crm/v3/objects/contacts",
            params={"limit": min(limit, 100), "properties": "firstname,lastname,email"},
            headers=headers,
        )
        if contacts.status_code == 200:
            for c in contacts.json().get("results", []):
                props = c.get("properties", {})
                items.append(
                    IntegrationItem(
                        source="hubspot",
                        type="contact",
                        external_id=c.get("id"),
                        title=f"{props.get('firstname','')} {props.get('lastname','')}".strip() or props.get("email"),
                        url=f"https://app.hubspot.com/contacts/{c.get('id')}",
                        metadata=props,
                    )
                )
    print(json.dumps([vars(item) for item in items], indent=2, default=str))
    return items

async def get_items_hubspot(user_id: str):
    return await create_integration_item_metadata_object(user_id)