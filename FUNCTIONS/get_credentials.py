"""
Module to authenticate with the YouTube Data API (v3).
Provides a typed YouTube service resource.
"""

from __future__ import annotations

from typing import cast

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import (
    Resource,
    build,  # pyright: ignore[reportUnknownVariableType]
)

from constants import CLIENT_SECRETS_FILE, TOKEN_FILE
from FUNCTIONS.HELPERS.logger import setup_logger, CustomLogger

logger = setup_logger(__name__)

SCOPES: list[str] = ["https://www.googleapis.com/auth/youtube.force-ssl"]
API_SERVICE_NAME: str = "youtube"
API_VERSION: str = "v3"


def get_authenticated_service(info: bool = True) -> Resource:
    """
    Authenticate with the YouTube Data API and return a typed service object.

    Handles refreshing and saving tokens automatically.
    Returns:
        YouTubeResource: a type-safe YouTube API client.
    """
    creds: Credentials | None = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(  # pyright: ignore[reportUnknownMemberType]
            filename=TOKEN_FILE, scopes=SCOPES
        )

    if not CLIENT_SECRETS_FILE.exists():
        exit(f"[Get Credentials] Please provide a secret file in {CLIENT_SECRETS_FILE}")

    # Refresh or re-authenticate if needed
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:  # pyright: ignore[reportUnknownMemberType]
            try:
                creds.refresh(Request())  # pyright: ignore[reportUnknownMemberType]
            except RefreshError:
                if info:
                    print("[Get Credentials] Token expired, please reconnect")
                logger.warning("[Get Credentials] Token expired, please reconnect")
                TOKEN_FILE.unlink(missing_ok=True)
                flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
                creds = flow.run_local_server(
                    port=0
                )
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save refreshed credentials
        if creds:
            _ = TOKEN_FILE.write_text(
                creds.to_json(),  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
                encoding="utf-8",
            )

    print("[Get Credentials] Successfully logged in")
    logger.info("[Get Credentials] Successfully logged in")

    # Return fully typed YouTube service
    return build(
        serviceName=API_SERVICE_NAME,
        version=API_VERSION,
        credentials=creds,
    )
