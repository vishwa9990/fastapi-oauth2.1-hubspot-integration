from datetime import datetime
from typing import Optional, List

class IntegrationItem:
    def __init__(
        self,
        metadata: Optional[dict] = None,
        source: Optional[str] = None,
        id: Optional[str] = None,
        type: Optional[str] = None,
        directory: bool = False,
        parent_path_or_name: Optional[str] = None,
        parent_id: Optional[str] = None,
        name: Optional[str] = None,
        creation_time: Optional[datetime] = None,
        last_modified_time: Optional[datetime] = None,
        url: Optional[str] = None,
        children: Optional[List[str]] = None,
        title: Optional[str] = None,
        visibility: Optional[bool] = True,
        external_id: Optional[str] = None
    ):
        self.title = title
        self.external_id = external_id
        self.source = source
        self.id = id
        self.type = type
        self.metadata = metadata
        self.directory = directory
        self.parent_path_or_name = parent_path_or_name
        self.parent_id = parent_id
        self.name = name
        self.creation_time = creation_time
        self.last_modified_time = last_modified_time
        self.url = url
        self.children = children
        self.visibility = visibility
