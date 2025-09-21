from pathlib import Path
from dotenv import load_dotenv
import os



JSON_DIR: Path = Path("JSON")
CRED_DIR: Path = Path("CREDS")
LOGS_DIR: Path = Path("LOGS")


CONFIG_DIR: Path = Path("CONFIG")
PATTERN_DIR: Path = CONFIG_DIR / "PATTERNS"
TAGS_DIR: Path = CONFIG_DIR / "TAGS"


CLIENT_SECRETS_FILE: Path = CRED_DIR / "client_secret_cm.json"
TOKEN_FILE: Path = CRED_DIR / "token.json"

PLAYLIST_VIDEOS_FILE: Path = JSON_DIR / "playlist_videos.json"
CORRECT_NOT_IN_DIR_FILE: Path = JSON_DIR / "correct_not_in_db.json"
UNAVAILABLE_VIDEOS_FILE: Path = JSON_DIR / "unavailable_videos.json"

UNWANTED_PATTERNS_FILE: Path = PATTERN_DIR / "unwanted_patterns.txt"
REMIX_PATTERNS_FILE: Path = PATTERN_DIR / "remix_patterns.txt"
PRIVATE_PATTERNS_FILE: Path = PATTERN_DIR / "private_patterns.txt"
TRUSTED_ARTISTS_FILE: Path = PATTERN_DIR / "trusted_artists.txt"

MAX_LYRICS_RETRIES: int = 1



_ = load_dotenv()

download_env: str | None = os.getenv("downloadpath")
if download_env is None:
    raise EnvironmentError("Environment variable 'downloadpath' is not set")
DOWNLOAD_PATH: Path = Path(download_env)

db_file = Path(os.getenv("dbpath", ""))
if not (db_file.exists() and db_file.is_file()):
    print("Warning: Database does not exists")



LOGS_CONSOLE_GLOBALLY: bool = True
LOGGING_LEVEL_CONSOLE: int = 30
LOGGING_LEVEL_LOGFILES: int = LOGGING_LEVEL_CONSOLE
OVERLAP_FPRINT: bool = True
OVERWRITE_UNCHANGED: bool = True

# STATUS_MAP = {
#     0: "downloaded",
#     1: "unavailable",
#     2: "private",
#     3: "unknown"
# }