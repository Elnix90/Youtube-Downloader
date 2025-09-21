from pathlib import Path
from sqlite3 import Cursor

from FUNCTIONS.helpers import sanitize_text
from logger import setup_logger
logger = setup_logger(__name__)

def sanitize_all_filenames(download_dir: Path, cur: Cursor) -> None:
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
            stem, suffix = file_path.stem, file_path.suffix

            new_stem = sanitize_text(stem)
            new_name = new_stem + suffix  # re-attach original extension

            if new_name != old_name:
                try:
                    _ = cur.execute("""
                        UPDATE Videos
                        SET filename = ?
                        WHERE filename = ?
                    """, (new_name, old_name))
                    logger.info(f"[Sanitize All] Updated DB '{old_name}' -> '{new_name}'")
                except Exception as e:
                    logger.error(f"[Sanitize All] Failed to update DB '{old_name}' -> '{new_name}': {e}")

                new_path = file_path.with_name(new_name)
                try:
                    _ = file_path.rename(new_path)
                    logger.info(f"[Sanitize All] Renamed file '{old_name}' -> '{new_name}'")
                except Exception as e:
                    logger.error(f"[Sanitize All] Failed to rename file '{old_name}' -> '{new_name}': {e}")

