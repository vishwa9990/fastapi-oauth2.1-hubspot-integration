# Redis Local Setup Guide

## Prerequisites
- Docker Desktop installed
- Python 3.11.9 (already installed)
- Node.js (to be installed)

## Step 1: Setup Docker Desktop

### Download and Install Docker Desktop
1. Download Docker Desktop from [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)
2. Install and start Docker Desktop

### Enable Virtualization (if needed)
If you encounter virtualization issues, run these commands in **Command Prompt as Administrator**:

#### For Windows with WSL 2:
```cmd
wsl --update
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
```

**Restart your computer after running these commands.**

## Step 2: Run Redis with Docker

### Start Redis Container
```bash
docker run -d -p 6379:6379 --name redis-local redis
```

### Verify Redis is Running
```bash
# Check if container is running
docker ps

# Test Redis connection
docker exec -it redis-local redis-cli ping
```

You should see `PONG` as response.

### Useful Redis Docker Commands
```bash
# Stop Redis
docker stop redis-local

# Start Redis (if stopped)
docker start redis-local

# Remove Redis container
docker rm redis-local

# View Redis logs
docker logs redis-local
```

## Step 3: Python Environment Setup

### Create Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Install Python Dependencies
```bash
# Install from requirements file
pip install -r requirements.txt

# Install FastAPI specifically (if not in requirements.txt)
pip install fastapi uvicorn
```

### Verify Python Setup
```bash
python --version  # Should show 3.11.9
pip list | grep fastapi
```

## Step 4: Node.js Setup

### Download and Install Node.js
1. Go to [https://nodejs.org/](https://nodejs.org/)
2. Download the LTS version
3. Install Node.js

### Install Node Dependencies
```bash
# Install packages from package.json
npm install

# Or if you prefer yarn
npm install -g yarn
yarn install
```

### Verify Node.js Setup
```bash
node --version
npm --version
```

## Troubleshooting

### Docker Issues
```bash
# Restart Docker Desktop
# Check Docker status
docker info

# Pull Redis image manually
docker pull redis

# Check port availability
netstat -an | findstr :6379
```

### Redis Connection Issues
- Ensure Docker container is running: `docker ps`
- Check if port 6379 is available
- Verify firewall settings
- Try connecting to `127.0.0.1:6379` instead of `localhost:6379`

## Quick Start Commands Summary
```bash
# 1. Start Redis
docker run -d -p 6379:6379 --name redis-local redis

# 2. Setup Python environment
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
pip install fastapi uvicorn

# 3. Install Node.js dependencies
npm install
```