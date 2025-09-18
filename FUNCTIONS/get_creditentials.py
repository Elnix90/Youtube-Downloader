from google.oauth2.credentials import Credentials
from google.auth.exceptions import RefreshError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build, Resource  # pyright: ignore[reportUnknownVariableType]

from CONSTANTS import TOKEN_FILE, CLIENT_SECRETS_FILE
from logger import setup_logger

logger = setup_logger(__name__)

SCOPES: list[str] = ["https://www.googleapis.com/auth/youtube.force-ssl"]
API_SERVICE_NAME: str = "youtube"
API_VERSION: str = "v3"


def get_authenticated_service(info: bool = True) -> Resource:
    """
    Authenticate with the YouTube API and return a service resource.
    Handles refreshing and saving tokens automatically.
    """
    creds: Credentials | None = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(filename=TOKEN_FILE, scopes=SCOPES)  # pyright: ignore[reportUnknownMemberType]


    if not creds or not creds.valid:
        if creds is not None and creds.expired and creds.refresh_token is not None:  # pyright: ignore[reportUnknownMemberType]
            try:
                creds.refresh(Request())  # pyright: ignore[reportUnknownMemberType]
            except RefreshError:
                if info: print("[Get Credentials] Token expired, please reconnect")
                logger.warning("[Get Credentials] Token expired, please reconnect")
                TOKEN_FILE.unlink(missing_ok=True)
                flow = InstalledAppFlow.from_client_secrets_file(  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
                    CLIENT_SECRETS_FILE, SCOPES
                )
                creds = flow.run_local_server(port=0)  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
        else:
            flow = InstalledAppFlow.from_client_secrets_file(  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
                CLIENT_SECRETS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]

        if creds is not None:
            with open(TOKEN_FILE, "w", encoding="utf-8") as token:
                token.write(creds.to_json())  # pyright: ignore[reportUnusedCallResult, reportUnknownMemberType, reportUnknownArgumentType]

    logger.info("[Get Credentials] Successfully logged")

    # Explicit cast to satisfy basedpyright typing
    return build(API_SERVICE_NAME, API_VERSION, credentials=creds)
