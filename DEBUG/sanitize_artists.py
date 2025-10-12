"""
sanitize_artists module:
Add or remove entry_id prefix in MP3 artist tags (TPE1 frame)
"""

import time
from datetime import timedelta
from pathlib import Path
from sqlite3 import Cursor

from constants import ENTRY_ID_SEPARATOR
from FUNCTIONS.HELPERS.fprint import fprint
from FUNCTIONS.HELPERS.logger import setup_logger
from FUNCTIONS.metadata import read_id3_tag, write_id3_tag
from FUNCTIONS.sql_requests import get_entry_id

logger = setup_logger(__name__)


def _has_entry_id_prefix(artist: str, entry_id: str) -> bool:
    """Check if artist name starts with '<entry_id>---'."""
    return artist.startswith(f"{entry_id}{ENTRY_ID_SEPARATOR}")


def sanitize_all_artists(
    download_dir: Path,
    cur: Cursor,
    add: bool = True,
    test_run: bool = False,
) -> None:
    """
    Recursively add or remove entry_id prefixes from MP3 artist tags.

    Args:
        download_dir (Path): Root download directory.
        cur (Cursor): SQLite cursor to read data.
        add (bool): If True, add entry_id prefix. If False, remove it.
        test_run (bool): If True, simulate changes without writing tags.
    """
    if not download_dir.exists() or not download_dir.is_dir():
        logger.warning(f"[Sanitize Artists] Download directory does not exist: {download_dir}")
        return

    # Collect all MP3 files once so we can count them
    files = list(download_dir.rglob("*.mp3"))
    total_files = len(files)
    if total_files == 0:
        logger.info("[Sanitize Artists] No MP3 files found.")
        return

    start_time = time.time()
    processed = 0

    for file_path in files:
        if not file_path.is_file():
            continue

        filename = file_path.name

        video_row = cur.execute(  # pyright: ignore[reportAny]
            "SELECT video_id FROM Videos WHERE filename = ?", (filename,)
        ).fetchone()

        if not video_row:
            logger.warning(f"[Sanitize Artists] No DB entry for file: {filename}")
            continue

        video_id = video_row[0]  # pyright: ignore[reportAny]
        entry_id = str(get_entry_id(video_id, cur))  # pyright: ignore[reportAny]

        # Read artist tag
        artist_data, status = read_id3_tag(file_path, "TPE1")

        if status != 0 or not artist_data:
            logger.warning(f"[Sanitize Artists] No artist tag found in '{filename}'")
            continue

        artist = artist_data[0].strip()
        has_prefix = _has_entry_id_prefix(artist, entry_id)

        if add:
            if has_prefix:
                logger.debug(f"[Sanitize Artists] Skipping (already prefixed): {artist}")
                continue
            new_artist = f"{entry_id}{ENTRY_ID_SEPARATOR}{artist}"
        else:
            if not has_prefix:
                logger.debug(f"[Sanitize Artists] Skipping (no prefix): {artist}")
                continue
            new_artist = artist.split(ENTRY_ID_SEPARATOR, 1)[1]

        # Write tag
        success = write_id3_tag(file_path, "TPE1", new_artist, test_run)
        if success:
            logger.info(f"[Sanitize Artists] '{artist}' → '{new_artist}' ({filename})")
        else:
            logger.error(f"[Sanitize Artists] Failed to update artist in '{filename}'")

        # Progress + ETA
        processed += 1
        elapsed = time.time() - start_time
        avg_time = elapsed / processed if processed > 0 else 0
        remaining = total_files - processed
        eta_seconds = remaining * avg_time
        eta_formatted = str(timedelta(seconds=int(eta_seconds)))

        percent = (processed / total_files) * 100
        bar_len = 30
        filled_len = int(bar_len * processed // total_files)
        progress_bar = "█" * filled_len + "-" * (bar_len - filled_len)

        fprint(
            f"[{progress_bar}] {percent:6.2f}% | {processed}/{total_files} | ETA: {eta_formatted}",
            ""
        )

    total_time = str(timedelta(seconds=int(time.time() - start_time)))
    logger.debug(f"[Sanitize Artists] Completed in {total_time} ({total_files} files processed).")
