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
    force_recompute_yt_info: bool


    thumbnail_format: Literal['pad', 'crop']

    sponsorblock_categories: list[str]

    tag_separator: str
    tag_start_delimiter: str
    tag_end_delimiter: str
    tag_inner_separator: str

    retry_unavailable: bool
    retry_private: bool

    force_mp3_presence: bool

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

class Config(TypedDict):
    paths: PathsConfig
    patterns: PatternsConfig
    processing: ProcessingConfig
    logging: LoggingConfig




# ---------- Loader functions ----------

def load_config() -> Config:
    """Load configuration from config.toml"""

    config_file = Path("config.toml")
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file '{config_file}' does not exist. Please create it from the provided template.")

    try:
        with open(config_file, "rb") as f:
            _config_cache: Config = tomli.load(f)  # pyright: ignore[reportAssignmentType]
        return _config_cache
    except tomli.TOMLDecodeError as e:
        raise ValueError(f"Syntax error in config.toml: {e}")




def get_config_value(
    section: str,
    key: str,
    default: str | int | bool | list[str] | None = None
) -> str | int | bool | list[str] | None:
    """Get a specific configuration value"""
    config = load_config()
    section_dict = config.get(section)
    if not isinstance(section_dict, dict):
        return default
    return section_dict.get(key, default)  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]





def get_processing_defaults() -> ProcessingConfig:
    """Get all default processing parameters"""
    config = load_config()
    processing = config.get("processing")

    return {
        "max_lyrics_retries": processing.get("max_lyrics_retries"),
        "playlist_id": processing.get("playlist_id"),


        "use_sponsorblock": processing.get("use_sponsorblock"),
        "get_lyrics": processing.get("get_lyrics"),
        "get_thumbnail": processing.get("get_thumbnail"),
        "add_tags": processing.get("add_tags"),
        "add_album": processing.get("add_album"),
        "embed_metadata": processing.get("embed_metadata"),

        "force_recompute_lyrics": processing.get("force_recompute_lyrics"),
        "force_recompute_thumbnails": processing.get("force_recompute_thumbnails"),
        "force_recompute_tags": processing.get("force_recompute_tags"),
        "force_recompute_album": processing.get("force_recompute_album"),
        "force_recompute_yt_info": processing.get("force_recompute_yt_info"),


        "thumbnail_format": processing.get("thumbnail_format"),

        "sponsorblock_categories": processing.get("sponsorblock_categories"),

        "tag_separator": processing.get("tag_separator"),
        "tag_start_delimiter": processing.get("tag_start_delimiter"),
        "tag_end_delimiter": processing.get("tag_end_delimiter"),
        "tag_inner_separator": processing.get("tag_inner_separator"),

        "retry_unavailable": processing.get("retry_unavailable"),
        "retry_private": processing.get("retry_private"),
        "force_mp3_presence": processing.get("force_mp3_presence"),

        "info": processing.get("info"),
        "error": processing.get("error"),
        "test_run": processing.get("test_run"),

        "clean": processing.get("clean"),
        "remove_no_longer_in_playlist": processing.get("remove_no_longer_in_playlist"),
        "remove_malformatted": processing.get("remove_malformatted"),
        "create_db_if_not": processing.get("create_db_if_not"),
        "add_folder_files_not_in_list": processing.get("add_folder_files_not_in_list"),
    }

