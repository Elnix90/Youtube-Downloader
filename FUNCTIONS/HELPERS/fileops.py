"""
Module to load and dump playlist video info JSON files.
"""

import json
from pathlib import Path
from typing import TypeVar, cast

from FUNCTIONS.HELPERS.helpers import VideoInfoMap
from FUNCTIONS.HELPERS.logger import setup_logger

logger = setup_logger(__name__)

T = TypeVar("T")


def load(file_path: Path) -> VideoInfoMap:
    """
    Load a JSON file containing playlist video entries and
    return a list of VideoInfo instances.
    """
    if not file_path.exists():
        msg = f"Error: '{file_path}' does not exist"
        logger.error(msg)
        raise FileNotFoundError(msg)

    try:
        with file_path.open("r", encoding="utf-8") as f:
            raw_data = cast(VideoInfoMap, json.load(f))
    except json.JSONDecodeError as exc:
        msg = f"Error decoding JSON in '{file_path}': {exc}"
        logger.error(msg)
        raise ValueError(msg) from exc

    logger.debug(f"[Load] Loaded {len(raw_data)} entries from '{file_path}'")
    return raw_data


def loadlist(file_path: Path) -> list[str]:
    """
    Load a JSON file containing playlist video entries and
    return a list of VideoInfo instances.
    """
    if not file_path.exists():
        msg = f"Error: '{file_path}' does not exist"
        logger.error(msg)
        raise FileNotFoundError(msg)

    try:
        with file_path.open("r", encoding="utf-8") as f:
            raw_data = cast(list[str], json.load(f))
    except json.JSONDecodeError as exc:
        msg = f"Error decoding JSON in '{file_path}': {exc}"
        logger.error(msg)
        raise ValueError(msg) from exc

    logger.debug(f"[Load] Loaded {len(raw_data)} entries from '{file_path}'")
    return raw_data


def dump(entries: VideoInfoMap | list[str], file_path: Path) -> None:
    """
    Dump a list of JSON-serializable objects into a JSON file.
    Automatically creates a backup before overwriting.

    This function is generic and works for:
      - list[VideoInfo]
      - list[str]
    """
    backup_path = file_path.with_suffix(file_path.suffix + ".bak")

    if file_path.exists():
        _ = backup_path.write_bytes(file_path.read_bytes())

    try:

        with file_path.open("w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2, ensure_ascii=False)

        if backup_path.exists():
            backup_path.unlink()

        logger.debug(f"[Dump] Successfully dumped {len(entries)}" + f"entries to '{file_path}'")

    except OSError as exc:
        if backup_path.exists():
            _ = file_path.write_bytes(backup_path.read_bytes())
            backup_path.unlink()
        logger.exception(f"[Dump] Failed to write to '{file_path}': {exc}")
        raise
