"""
Configuration loader for YouTube Music Downloader
Provides functions to access configuration values from config.toml
"""

from pathlib import Path
import tomli
from typing import Dict, Any, Union

_config_cache: Dict[str, Any] = {}

def load_config() -> Dict[str, Any]:
    """Charge la configuration depuis config.toml"""
    global _config_cache
    
    if _config_cache:
        return _config_cache
    
    config_file = Path("config.toml")
    if not config_file.exists():
        raise FileNotFoundError(
            f"Le fichier de configuration '{config_file}' n'existe pas. "
            "Veuillez le créer à partir du modèle fourni."
        )
    
    try:
        with open(config_file, "rb") as f:
            _config_cache = tomli.load(f)
        return _config_cache
    except tomli.TOMLDecodeError as e:
        raise ValueError(f"Erreur de syntaxe dans config.toml: {e}")

def get_config_value(section: str, key: str, default: Any = None) -> Any:
    """Récupère une valeur de configuration"""
    config = load_config()
    return config.get(section, {}).get(key, default)

def get_processing_defaults() -> Dict[str, Any]:
    """Récupère tous les paramètres par défaut pour le traitement"""
    config = load_config()
    processing = config.get("processing", {})
    
    return {
        "playlist_id": processing.get("playlist_id", "LL"),
        "embed_metadata": processing.get("embed_metadata", True),
        "add_album": processing.get("add_album", True),
        "recompute_album": processing.get("recompute_album", True),
        "get_lyrics": processing.get("get_lyrics", True),
        "recompute_lyrics": processing.get("recompute_lyrics", False),
        "get_thumbnail": processing.get("get_thumbnail", True),
        "thumbnail_format": processing.get("thumbnail_format", "pad"),
        "recompute_thumbnails": processing.get("recompute_thumbnails", False),
        "use_sponsorblock": processing.get("use_sponsorblock", True),
        "categories": processing.get("sponsorblock_categories", ["music_offtopic", "sponsor", "intro", "outro"]),
        "add_tags": processing.get("add_tags", True),
        "sep": processing.get("tag_separator", " ~ "),
        "start_def": processing.get("tag_start_delimiter", "["),
        "end_def": processing.get("tag_end_delimiter", "]"),
        "tag_sep": processing.get("tag_inner_separator", ","),
        "recompute_tags": processing.get("recompute_tags", True),
        "retry_unavailable": processing.get("retry_unavailable", False),
        "retry_private": processing.get("retry_private", False),
        "info": processing.get("info", True),
        "error": processing.get("error", True),
        "test_run": processing.get("test_run", False),
        "clean": processing.get("clean", False),
        "remove_no_longer_in_playlist": processing.get("remove_no_longer_in_playlist", False),
        "remove_malformatted": processing.get("remove_malformatted", True),
        "create_db_if_not": processing.get("create_db_if_not", True),
        "add_folder_files_not_in_list": processing.get("add_folder_files_not_in_list", True)
    }