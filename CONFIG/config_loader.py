"""
Configuration loader for YouTube Music Downloader
Provides functions to access configuration values from config.toml
"""

from pathlib import Path
from typing import Literal, TypedDict
import tomli



# ---------- Config schema ----------

class PathsConfig(TypedDict):
    json_dir: str
    cred_dir: str
    logs_dir: str
    config_dir: str
    download_path: str
    db_path: str
    client_secrets_file: str
    token_file: str
    playlist_videos_file: str

class PatternsConfig(TypedDict):
    unwanted_patterns_file: str
    remix_patterns_file: str
    private_patterns_file: str
    trusted_artists_file: str

class ProcessingConfig(TypedDict):
    max_lyrics_retries: int
    playlist_id: str


    use_sponsorblock: bool
    get_lyrics: bool
    get_thumbnail: bool
    add_tags: bool
    add_album: bool
    embed_metadata: bool

    force_recompute_lyrics: bool
    force_recompute_thumbnails: bool
    force_recompute_tags: bool
    force_recompute_album: bool


    thumbnail_format: Literal['pad', 'crop']

    sponsorblock_categories: list[str]

    tag_separator: str
    tag_start_delimiter: str
    tag_end_delimiter: str
    tag_inner_separator: str

    retry_unavailable: bool
    retry_private: bool

    force_recompute_yt_info: bool
    force_mp3_presence: bool

    get_remix_of: bool
    remix_confidence_threshold: float
    force_recompute_remix_of: bool

    info: bool
    error: bool
    test_run: bool

    clean: bool
    remove_no_longer_in_playlist: bool
    remove_malformatted: bool
    create_db_if_not: bool
    add_folder_files_not_in_list: bool

class LoggingConfig(TypedDict):
    console_globally: bool
    level_console: str
    level_logfiles: str
    overlap_fprint: bool
    overwrite_unchanged: bool

class OtherConfig(TypedDict):
    music_playlist_id: str | None
    clean: bool

class Config(TypedDict):
    paths: PathsConfig
    patterns: PatternsConfig
    processing: ProcessingConfig
    logging: LoggingConfig
    other: OtherConfig




# ---------- Loader functions ----------

def load_config(config_file: Path) -> Config:
    """Load configuration from config.toml"""


    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file '{config_file}' does not exist.")
    try:
        with open(config_file, "rb") as f:
            _config_cache: Config = tomli.load(f)  # pyright: ignore[reportAssignmentType]
        return _config_cache
    except tomli.TOMLDecodeError as e:
        raise ValueError(f"Syntax error in config.toml: {e}")


