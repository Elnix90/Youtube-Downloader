from __future__ import annotations

import os
from typing import Optional, Any
from google.oauth2.credentials import Credentials  # type: ignore
from google.auth.exceptions import RefreshError  # type: ignore
from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore
from google.auth.transport.requests import Request  # type: ignore
from googleapiclient.discovery import build  # type: ignore

from CONSTANTS import TOKEN_FILE, CLIENT_SECRETS_FILE

SCOPES: list[str] = ["https://www.googleapis.com/auth/youtube.force-ssl"]
API_SERVICE_NAME: str = "youtube"
API_VERSION: str = "v3"


def get_authenticated_service() -> Any:
    """
    Authenticate with the YouTube API and return a service resource.
    Handles refreshing and saving tokens automatically.
    """
    creds: Optional[Any] = None  # Use Any due to missing stubs

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES) # type: ignore

    if not creds or not getattr(creds, "valid", False):
        if creds and getattr(creds, "expired", False) and getattr(creds, "refresh_token", None):
            try:
                creds.refresh(Request())
            except RefreshError:
                print("Token expired, please reconnect")
                os.remove(TOKEN_FILE)
                flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES) # type: ignore
                creds = flow.run_local_server(port=0) # type: ignore
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES) # type: ignore
            creds = flow.run_local_server(port=0) # type: ignore

        with open(TOKEN_FILE, "w", encoding="utf-8") as token:
            token.write(creds.to_json())

    return build(API_SERVICE_NAME, API_VERSION, credentials=creds) # type: ignore
