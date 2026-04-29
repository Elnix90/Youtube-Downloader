"""
Constants loader for YouTube Music Downloader
Loads config.toml (validated) and exposes constants.
"""

import logging
from pathlib import Path

from CONFIG.config_loader import load_config

# ---------- Load config ----------

CONFIG_FILE = Path("CONFIG/config.toml")


CONFIG = load_config(CONFIG_FILE)


# ---------- Validation ----------


def validate_config() -> None:
    """
    Loads the config file and checks for any errros to avoid later exceptions
    """
    required_sections = ["paths", "patterns", "processing", "logging"]
    for section in required_sections:
        if section not in CONFIG:
            raise ValueError(f"Missing section in config.toml: [{section}]")

    # Check critical paths
    download_path = Path(CONFIG["paths"]["download_path"]).expanduser().resolve()
    if not download_path.parent.exists():
        print(f"Warning: Parent directory of download_path does not exist: {download_path.parent}; will be created")

    db_path = Path(CONFIG["paths"]["db_path"])
    if not db_path.exists() and not db_path.parent.exists():
        print(f"Warning: Parent directory of db_path does not exist: {db_path.parent}")


validate_config()


# ---------- Constants ----------

# Base directories
JSON_DIR: Path = Path(CONFIG["paths"]["json_dir"])
CRED_DIR: Path = Path(CONFIG["paths"]["cred_dir"])
LOGS_DIR: Path = Path(CONFIG["paths"]["logs_dir"])

CONFIG_DIR: Path = Path(CONFIG["paths"]["config_dir"])
PATTERN_DIR: Path = CONFIG_DIR / "PATTERNS"
TAGS_DIR: Path = CONFIG_DIR / "TAGS"

# Critical paths
DOWNLOAD_PATH: Path = Path(CONFIG["paths"]["download_path"]).expanduser().resolve()
DB_PATH: Path = Path(CONFIG["paths"]["db_path"])
PLAYLIST_VIDEOS_FILE: Path = JSON_DIR / CONFIG["paths"]["playlist_videos_file"]

# Creds files
CLIENT_SECRETS_FILE: Path = CRED_DIR / CONFIG["paths"]["client_secrets_file"]
TOKEN_FILE: Path = CRED_DIR / CONFIG["paths"]["token_file"]
COOKIE_FILE: Path = CRED_DIR / CONFIG["paths"]["cookies_file"]
PROXIES_FILE: Path = CRED_DIR / CONFIG["paths"]["proxies_file"]
LAST_PROXY_FILE: Path = CRED_DIR / CONFIG["paths"]["last_proxy_file"]

# Stats files
CORRECT_NOT_IN_DIR_FILE: Path = JSON_DIR / "correct_not_in_db.json"
UNAVAILABLE_VIDEOS_FILE: Path = JSON_DIR / "unavailable_videos.json"

# Pattern files
UNWANTED_PATTERNS_FILE: Path = PATTERN_DIR / CONFIG["patterns"]["unwanted_patterns_file"]
REMIX_PATTERNS_FILE: Path = PATTERN_DIR / CONFIG["patterns"]["remix_patterns_file"]
PRIVATE_PATTERNS_FILE: Path = PATTERN_DIR / CONFIG["patterns"]["private_patterns_file"]
TRUSTED_ARTISTS_FILE: Path = PATTERN_DIR / CONFIG["patterns"]["trusted_artists_file"]

# Processing
MAX_LYRICS_RETRIES: int = CONFIG["processing"]["max_lyrics_retries"]
REMIX_CONFIDENCE_THRESHOLD: float = CONFIG["processing"]["remix_confidence_threshold"]

ADD_ENTRY_ID_TO_TITLE = CONFIG["processing"]["add_entry_id_to_title"]
ENTRY_ID_SEPARATOR = CONFIG["processing"]["entry_id_separator"]
ENTRY_ID_SIZE = CONFIG["processing"]["entry_id_size"]

# Logging
LOGS_CONSOLE_GLOBALLY: bool = CONFIG["logging"]["console_globally"]
OVERLAP_FPRINT: bool = CONFIG["logging"]["overlap_fprint"]
OVERWRITE_UNCHANGED: bool = CONFIG["logging"]["overwrite_unchanged"]

INCLUDE_TIME_IN_EMBEDDED_TIME = CONFIG["processing"]["include_time_in_embedded_date"]

LOGGING_LEVELS: dict[str, int] = {
    "VERBOSE": 5,
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

LOGGING_LEVEL_CONSOLE: int = LOGGING_LEVELS[CONFIG["logging"]["level_console"].upper()]
LOGGING_LEVEL_LOGFILES: int = LOGGING_LEVELS[CONFIG["logging"]["level_logfiles"].upper()]

LOG_YT_DLP_INFO: bool = CONFIG["logging"]["log_yt_dlp_info"]
LOG_YT_DLP_VERBOSE: bool = CONFIG["logging"]["log_yt_dlp_verbose"]

EXCLUDE_FROM_MAIN = {"skips", "tags", "playlist_id", "playlist_item_id", "position", "date_added"}
