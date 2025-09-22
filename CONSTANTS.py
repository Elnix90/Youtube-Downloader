"""
Constants loader for YouTube Music Downloader
Loads config.toml (validated) and exposes constants.
"""

from pathlib import Path
import tomli
import logging
import sys

from config_loader import Config



# ---------- Load config ----------

CONFIG_FILE = Path("config.toml")

if not CONFIG_FILE.exists():
    print(f"Error: Configuration file '{CONFIG_FILE}' does not exist.")
    print("Please create this file or use config.toml.example as a template.")
    sys.exit(1)

try:
    with open(CONFIG_FILE, "rb") as f:
        config: Config = tomli.load(f)  # pyright: ignore[reportAssignmentType]
except tomli.TOMLDecodeError as e:
    raise ValueError(f"Syntax error in config.toml: {e}")




# ---------- Validation ----------

def validate_config() -> None:
    required_sections = ["paths", "patterns", "processing", "logging"]
    for section in required_sections:
        if section not in config:
            raise ValueError(f"Missing section in config.toml: [{section}]")

    # Check critical paths
    download_path = Path(config["paths"]["download_path"])
    if not download_path.parent.exists():
        print(f"Warning: Parent directory of download_path does not exist: {download_path.parent}")

    db_path = Path(config["paths"]["db_path"])
    if not db_path.exists() and not db_path.parent.exists():
        print(f"Warning: Parent directory of db_path does not exist: {db_path.parent}")

validate_config()




# ---------- Constants ----------

# Base directories
JSON_DIR: Path = Path(config["paths"]["json_dir"])
CRED_DIR: Path = Path(config["paths"]["cred_dir"])
LOGS_DIR: Path = Path(config["paths"]["logs_dir"])

CONFIG_DIR: Path = Path(config["paths"]["config_dir"])
PATTERN_DIR: Path = CONFIG_DIR / "PATTERNS"
TAGS_DIR: Path = CONFIG_DIR / "TAGS"

# Critical paths
DOWNLOAD_PATH: Path = Path(config["paths"]["download_path"]).expanduser().resolve()
DB_PATH: Path = Path(config["paths"]["db_path"])

# Creds files
CLIENT_SECRETS_FILE: Path = CRED_DIR / config["paths"]["client_secrets_file"]
TOKEN_FILE: Path = CRED_DIR / config["paths"]["token_file"]
PLAYLIST_VIDEOS_FILE: Path = JSON_DIR / config["paths"]["playlist_videos_file"]

# Stats files
CORRECT_NOT_IN_DIR_FILE: Path = JSON_DIR / "correct_not_in_db.json"
UNAVAILABLE_VIDEOS_FILE: Path = JSON_DIR / "unavailable_videos.json"

# Pattern files
UNWANTED_PATTERNS_FILE: Path = PATTERN_DIR / config["patterns"]["unwanted_patterns_file"]
REMIX_PATTERNS_FILE: Path = PATTERN_DIR / config["patterns"]["remix_patterns_file"]
PRIVATE_PATTERNS_FILE: Path = PATTERN_DIR / config["patterns"]["private_patterns_file"]
TRUSTED_ARTISTS_FILE: Path = PATTERN_DIR / config["patterns"]["trusted_artists_file"]

# Processing
MAX_LYRICS_RETRIES: int = config["processing"]["max_lyrics_retries"]

# Logging
LOGS_CONSOLE_GLOBALLY: bool = config["logging"]["console_globally"]
OVERLAP_FPRINT: bool = config["logging"]["overlap_fprint"]
OVERWRITE_UNCHANGED: bool = config["logging"]["overwrite_unchanged"]

LOGGING_LEVELS: dict[str, int] = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

LOGGING_LEVEL_CONSOLE: int = LOGGING_LEVELS.get(
    config["logging"]["level_console"].upper(),
    logging.WARNING
)
LOGGING_LEVEL_LOGFILES: int = LOGGING_LEVELS.get(
    config["logging"]["level_logfiles"].upper(),
    logging.DEBUG
)

CONFIG: Config = config