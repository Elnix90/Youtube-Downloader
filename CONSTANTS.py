from pathlib import Path
from dotenv import load_dotenv
import os


JSON_DIR: Path = Path("JSON")
CRED_DIR: Path = Path("CREDS")
CONFIG_DIR: Path = Path("CONFIG")
TAGS_DIR: Path = Path("TAGS")

CLIENT_SECRETS_FILE: Path = CRED_DIR / "client_secret_cm.json"
TOKEN_FILE: Path = CRED_DIR / "token.json"

LIKED_VIDEOS_FILE: Path = JSON_DIR / "liked_videos.json"
PLAYLIST_VIDEOS_FILE: Path = JSON_DIR / "playlist_videos.json"
PLAYLIST_VIDEOS_INFOS_FILE: Path = JSON_DIR / "playlist_videos_infos.json"
VIDEOS_TO_LIKE_FILE: Path = JSON_DIR / "videos_to_like.json"
VIDEOS_TO_ADD_IN_PLAYLIST_FILE: Path = JSON_DIR / "videos_to_add_in_playlist.json"
VIDEOS_TO_DOWNLOAD_FILE: Path = JSON_DIR / "videos_to_download.json"
VIDEOS_INFOS_FILE: Path = JSON_DIR / "video_infos.json"
ERROR_DOWNLOADED_FILE: Path = JSON_DIR / "error_downloaded.json"
ERROR_LIKED_FILE: Path = JSON_DIR / "error_liked.json"
ERROR_ADDED_FILE: Path = JSON_DIR / "error_added.json"
UNAVAILABLE_VIDEOS_FILE: Path = JSON_DIR / "unavailable_videos.json"

UNWANTED_PATTERNS_FILE: Path = CONFIG_DIR / "unwanted_patterns.txt"
REMIX_PATTERNS_FILE: Path = CONFIG_DIR / "remix_patterns.txt"


load_dotenv()

download_env: str | None = os.getenv("downloadpath")
if download_env is None:
    raise EnvironmentError("Environment variable 'downloadpath' is not set")

DOWNLOAD_PATH: Path = Path(download_env)