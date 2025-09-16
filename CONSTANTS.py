from pathlib import Path
from dotenv import load_dotenv
import os
import logging


JSON_DIR: Path = Path("JSON")
CRED_DIR: Path = Path("CREDS")
LOGS_DIR: Path = Path("LOGS")


CONFIG_DIR: Path = Path("CONFIG")
PATTERN_DIR: Path = CONFIG_DIR / "PATTERNS"
TAGS_DIR: Path = CONFIG_DIR / "TAGS"
ALBUM_DIR: Path = Path("ALBUMS")


CLIENT_SECRETS_FILE: Path = CRED_DIR / "client_secret_cm.json"
TOKEN_FILE: Path = CRED_DIR / "token.json"

PLAYLIST_VIDEOS_FILE: Path = JSON_DIR / "playlist_videos.json"
UNWANTED_PATTERNS_FILE: Path = PATTERN_DIR / "unwanted_patterns.txt"
REMIX_PATTERNS_FILE: Path = PATTERN_DIR / "remix_patterns.txt"
PUBLIC_PATTERNS_FILE: Path = ALBUM_DIR / "public_patterns.txt"
PRIVATE_PATTERNS_FILE: Path = ALBUM_DIR / "private_patterns.txt"


_ = load_dotenv()

download_env: str | None = os.getenv("downloadpath")
if download_env is None:
    raise EnvironmentError("Environment variable 'downloadpath' is not set")
DOWNLOAD_PATH: Path = Path(download_env)

db_file = Path(os.getenv("dbpath", ""))
if not (db_file.exists() and db_file.is_file()):
    print("Warning: Database does not exists")



LOGS_CONSOLE_GLOBALLY: bool = True
LOGGING_LEVEL: int = logging.DEBUG
NOT_OVERLAP_FPRINT: bool = False


# STATUS_MAP = {
#     0: "downloaded",
#     1: "unavailable",
#     2: "private",
#     3: "unknown"
# }