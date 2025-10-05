"""
Module to load and dump playlist video info JSON files.
"""

import json
from pathlib import Path
from typing import TypeVar, cast

from FUNCTIONS.HELPERS.logger import setup_logger
from FUNCTIONS.HELPERS.types_playlist import PlaylistItem, PlaylistVideoEntry

logger = setup_logger(__name__)

T = TypeVar("T")  # Generic type for entries


def load(file_path: Path) -> list[PlaylistVideoEntry]:
    """
    Load a JSON file containing playlist video entries and
    return a list of PlaylistVideoEntry instances.
    """
    if not file_path.exists():
        msg = f"Error: '{file_path}' does not exist"
        logger.error(msg)
        raise FileNotFoundError(msg)

    try:
        with file_path.open("r", encoding="utf-8") as f:
            raw_data = cast(list[PlaylistItem], json.load(f))
    except json.JSONDecodeError as exc:
        msg = f"Error decoding JSON in '{file_path}': {exc}"
        logger.error(msg)
        raise ValueError(msg) from exc

    entries: list[PlaylistVideoEntry] = []
    for item in raw_data:
        try:
            entry = PlaylistVideoEntry.from_api_response(item)
            entries.append(entry)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.exception(f"Error parsing item from '{file_path}': {exc}")

    logger.debug(f"[Load] Loaded {len(entries)} entries from '{file_path}'")
    return entries


def dump(entries: list[T], file_path: Path) -> None:
    """
    Dump a list of JSON-serializable objects into a JSON file.
    Automatically creates a backup before overwriting.

    This function is generic and works for:
      - list[PlaylistVideoEntry]
      - list[str]
      - list[dict]
    """
    backup_path = file_path.with_suffix(file_path.suffix + ".bak")

    if file_path.exists():
        _ = backup_path.write_bytes(file_path.read_bytes())

    try:
        # Handle PlaylistVideoEntry objects
        json_ready = [  # pyright: ignore[reportUnknownVariableType]
            entry.to_json() if hasattr(entry, "to_json") else entry  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
            for entry in entries
        ]

        with file_path.open("w", encoding="utf-8") as f:
            json.dump(json_ready, f, indent=2, ensure_ascii=False)

        if backup_path.exists():
            backup_path.unlink()

        logger.debug(
            f"[Dump] Successfully dumped {len(entries)} entries to '{file_path}'"
        )

    except OSError as exc:
        if backup_path.exists():
            _ = file_path.write_bytes(backup_path.read_bytes())
            backup_path.unlink()
        logger.exception(f"[Dump] Failed to write to '{file_path}': {exc}")
        raise
