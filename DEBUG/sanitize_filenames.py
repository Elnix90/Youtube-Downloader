"""
sanitize_filenames module: Sanitize all filenemes in the download dir
"""

from pathlib import Path
from sqlite3 import Connection, Cursor

from FUNCTIONS.HELPERS.logger import setup_logger
from FUNCTIONS.HELPERS.text_helpers import sanitize_text
from FUNCTIONS.sql_requests import commit_changes_to_db, get_entry_id

logger = setup_logger(__name__)


def _split_filename_parts(filename: str, separator: str = "---") -> str:
    """
    Split a sanitized filename into to get the filename without the entry_id.
    Returns stem_without_suffix.
    """
    stem = Path(filename).stem
    if separator in stem:
        _, rest = stem.split(separator, 1)
        return rest
    return stem


def sanitize_all_filenames(download_dir: Path, cur: Cursor, conn: Connection, separator: str) -> None:
    """
    Recursively sanitize all filenames in the download directory.
    Keeps file extensions intact while cleaning only the stem.
    """
    if not download_dir.exists() or not download_dir.is_dir():
        logger.warning(f"[Sanitize All] Download directory does not exist: {download_dir}")
        return

    # Iterate recursively through all files
    for file_path in download_dir.rglob("*"):
        if file_path.is_file():

            old_name = file_path.name
            stem_and_entry_id, suffix = file_path.stem, file_path.suffix
            stem = _split_filename_parts(stem_and_entry_id, separator)

            video_row = cur.execute(  # pyright: ignore[reportAny]
                "SELECT video_id FROM Videos WHERE filename = ?", (old_name,)
            ).fetchone()

            if not video_row:
                logger.warning(f"[Sanitize All] No video_id found for {old_name}")
                continue

            video_id = video_row[0]  # pyright: ignore[reportAny]
            entry_id = str(get_entry_id(video_id, cur))  # pyright: ignore[reportAny]

            new_stem = sanitize_text(stem)
            new_name = f"{entry_id}{separator}{new_stem}{suffix}"  # re-attach original extension + entry_id

            if new_name != old_name:
                try:
                    _ = cur.execute(
                        """
                        UPDATE Videos
                        SET filename = ?
                        WHERE filename = ?
                    """,
                        (new_name, old_name),
                    )
                    logger.info(f"[Sanitize All] Updated DB '{old_name}' -> '{new_name}'")
                except Exception as e:  # pylint: disable=broad-exception-caught
                    logger.error(f"[Sanitize All] Failed to update DB '{old_name}' -> '{new_name}': {e}")

                new_path = file_path.with_name(new_name)
                try:
                    _ = file_path.rename(new_path)
                    logger.info(f"[Sanitize All] Renamed file '{old_name}' -> '{new_name}'")
                except Exception as e:  # pylint: disable=broad-exception-caught
                    logger.error(f"[Sanitize All] Failed to rename file '{old_name}' -> '{new_name}': {e}")

    _ = commit_changes_to_db(conn, True)
