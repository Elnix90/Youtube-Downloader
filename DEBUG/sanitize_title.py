"""
title_sanitizer module:
- set_titles_from_db: restore TIT2 from DB.title
- sanitize_all_titles: add/remove '<entry_id>{SEP}<title>' prefix safely
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


def _has_entry_id_prefix(title: str, entry_id: str) -> bool:
    """Return True if title starts with '<entry_id>{SEP}' or equals entry_id."""
    if not title:
        return False
    return title == entry_id or title.startswith(f"{entry_id}{ENTRY_ID_SEPARATOR}")


def set_titles_from_db(
    download_dir: Path,
    cur: Cursor,
    test_run: bool = False,
) -> None:
    """
    Overwrite TIT2 for each MP3 in download_dir with the title stored in the DB (Videos.title).
    Use test_run=True to only preview changes.
    """

    if not download_dir.exists() or not download_dir.is_dir():
        logger.warning(f"[Set Titles] Download directory does not exist: {download_dir}")
        return

    files = list(download_dir.rglob("*.mp3"))
    total = len(files)
    if total == 0:
        logger.info("[Set Titles] No MP3 files found.")
        return

    start = time.time()
    processed = 0

    for file_path in files:
        if not file_path.is_file():
            continue

        filename = file_path.name
        row = cur.execute(  # pyright: ignore[reportAny]
            "SELECT video_id, title FROM Videos WHERE filename = ?", (filename,)
        ).fetchone()
        if not row:
            logger.warning(f"[Set Titles] No DB entry for file: {filename}")
            continue

        _, db_title = row  # pyright: ignore[reportAny]
        db_title = db_title or ""  # ensure string

        # Read current tag (for logging)
        title_data, status = read_id3_tag(file_path, "TIT2")
        current_title = title_data[0].strip() if (status == 0 and title_data) else ""

        if current_title == db_title:
            logger.debug(f"[Set Titles] Skipping (already matches DB): {filename}")
        else:
            logger.info(f"[Set Titles] Will set '{filename}' title -> '{db_title}' (was: '{current_title}')")
            if not test_run:
                success = write_id3_tag(file_path, "TIT2", db_title, test_run)
                if not success:
                    logger.error(f"[Set Titles] Failed to write title for '{filename}'")

        # Progress & ETA
        processed += 1
        elapsed = time.time() - start
        avg = elapsed / processed if processed else 0
        remaining = total - processed
        eta = str(timedelta(seconds=int(remaining * avg)))

        percent = (processed / total) * 100
        bar_len = 30
        filled = int(bar_len * processed // total)
        progress_bar = "█" * filled + "-" * (bar_len - filled)
        fprint(f"[{progress_bar}] {percent:6.2f}% | {processed}/{total} | ETA: {eta}", "")

    logger.debug(f"[Set Titles] Done in {str(timedelta(seconds=int(time.time() - start)))}")


def sanitize_all_titles(
    download_dir: Path,
    cur: Cursor,
    add: bool = True,
    test_run: bool = False,
) -> None:
    """
    Add or remove the '<entry_id>{SEP}{title}' prefix to the TIT2 frame.

    Behavior:
      - When adding: use the DB.title as the canonical title (fall back to current tag if empty),
        and set TIT2 to "<entry_id>{SEP}{title>" if not already prefixed.
      - When removing: if TIT2 starts with "<entry_id>{SEP}" remove that prefix and set the remainder.
        If remainder is empty, restore DB.title (so we don't leave an empty title).
    """

    if not download_dir.exists() or not download_dir.is_dir():
        logger.warning(f"[Sanitize Titles] Download directory does not exist: {download_dir}")
        return

    files = list(download_dir.rglob("*.mp3"))
    total_files = len(files)
    if total_files == 0:
        logger.info("[Sanitize Titles] No MP3 files found.")
        return

    start_time = time.time()
    processed = 0

    for file_path in files:
        if not file_path.is_file():
            continue

        filename = file_path.name

        # Get db fields: video_id and canonical title
        row = cur.execute(  # pyright: ignore[reportAny]
            "SELECT video_id, title FROM Videos WHERE filename = ?", (filename,)
        ).fetchone()
        if not row:
            logger.warning(f"[Sanitize Titles] No DB entry for file: {filename}")
            continue

        video_id, db_title = row  # pyright: ignore[reportAny]
        db_title = db_title or ""

        entry_id = str(get_entry_id(video_id, cur))  # pyright: ignore[reportAny]

        # Read current TIT2
        title_data, status = read_id3_tag(file_path, "TIT2")
        current_title = title_data[0].strip() if (status == 0 and title_data) else ""

        has_prefix = _has_entry_id_prefix(current_title, entry_id)

        if add:
            # Decide base title: prefer DB.title, fallback to current tag if DB missing
            base_title = db_title if db_title else current_title
            if not base_title:
                logger.warning(f"[Sanitize Titles] No title available to prefix for '{filename}'")
                continue

            if has_prefix:
                logger.debug(f"[Sanitize Titles] Skipping (already prefixed): {current_title} ({filename})")
            else:
                new_title = f"{entry_id}{ENTRY_ID_SEPARATOR}{base_title}"
                logger.info(f"[Sanitize Titles] Will add prefix for '{filename}': '{current_title}' -> '{new_title}'")
                if not test_run:
                    ok = write_id3_tag(file_path, "TIT2", new_title, test_run)
                    if not ok:
                        logger.error(f"[Sanitize Titles] Failed to write title for '{filename}'")
        else:
            # Remove prefix if present
            if not has_prefix:
                logger.debug(f"[Sanitize Titles] Skipping (no prefix): {current_title} ({filename})")
            else:
                # remove only the first occurrence and strip whitespace
                remainder = (
                    current_title.split(ENTRY_ID_SEPARATOR, 1)[1].strip() if ENTRY_ID_SEPARATOR in current_title else ""
                )
                # if remainder is empty, restore DB title (so we don't blank titles)
                new_title = remainder if remainder else db_title
                logger.info(
                    f"[Sanitize Titles] Will remove prefix for '{filename}': '{current_title}' -> '{new_title}'"
                )
                if not test_run:
                    ok = write_id3_tag(file_path, "TIT2", new_title, test_run)
                    if not ok:
                        logger.error(f"[Sanitize Titles] Failed to write title for '{filename}'")

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

        fprint(f"[{progress_bar}] {percent:6.2f}% | {processed}/{total_files} | ETA: {eta_formatted}", "")

    total_time = str(timedelta(seconds=int(time.time() - start_time)))
    logger.debug(f"[Sanitize Titles] Completed in {total_time} ({total_files} files processed).")
