"""
Module to remove videos from the database and filesystem if they are
not present in a given playlist JSON file.
"""

from pathlib import Path
from sqlite3 import Connection, Cursor

from FUNCTIONS.HELPERS.fileops import handler
from FUNCTIONS.sql_requests import get_videos_in_list, get_video_info_from_db
from FUNCTIONS.HELPERS.fprint import fprint
from FUNCTIONS.HELPERS.logger import setup_logger

logger = setup_logger(__name__)


def remove_ids_not_in_list(
    video_id_file: Path,
    download_path: Path,
    include_not_status0: bool,
    cur: Cursor,
    conn: Connection,
    info: bool,
    error: bool,
    test_run: bool,
) -> None:
    """
    Remove videos from the database and filesystem if they are not present
    in the playlist JSON file.

    Args:
        video_id_file: Path to playlist JSON file.
        download_path: Path to download directory.
        include_not_status0: Whether to include videos with non-zero status.
        cur: SQLite cursor.
        conn: SQLite connection.
        info: Whether to print info messages.
        error: Whether to print error messages.
        test_run: If True, do not actually delete files or commit DB.
    """
    # Fetch current video IDs from DB
    existing_video_ids= set(
        get_videos_in_list(include_not_status0=include_not_status0, cur=cur)
    )

    try:
        playlist_entries = handler.load(video_id_file)
        video_ids = set(entry.video_id for entry in playlist_entries if entry.video_id)
    except Exception as e:
        logger.error(f"[Removing Ids] Failed to load '{video_id_file}': {e}")
        if error:
            print(f"[Removing Ids] Failed to load '{video_id_file}': {e}")
        return

    # Determine IDs not in the playlist
    not_in_video_ids = existing_video_ids - video_ids

    removed_ids = 0
    removed_files = 0

    for video_id in not_in_video_ids:
        data = get_video_info_from_db(video_id, cur)
        filename: str = data.get("filename", "")

        if filename:
            try:
                if not test_run:
                    filepath = (download_path / filename).with_suffix(".mp3")
                    lyrics_path = (download_path / filename).with_suffix(".lrc")
                    thumbnail_path = (download_path / filename).with_suffix(".png")

                    filepath.unlink(missing_ok=True)
                    lyrics_path.unlink(missing_ok=True)
                    thumbnail_path.unlink(missing_ok=True)

                removed_files += 1
            except OSError as e:
                logger.error(f"[Removing Ids] Error removing {filename}: {e}")
                if error:
                    print(f"[Removing Ids] Error removing {filename}: {e}")
            except Exception as e:
                logger.error(f"[Removing Ids] Unknown error removing {filename}: {e}")
                if error:
                    print(f"[Removing Ids] Unknown error removing {filename}: {e}")

        _ = cur.execute("DELETE FROM videos WHERE video_id = ?", (video_id,))
        removed_ids += 1

        if info:
            fprint("", f"[Removing Ids] Removed {removed_ids} from list")

    if not test_run:
        conn.commit()

    if removed_ids == 0:
        logger.info("[Removing Ids] No videos to remove from the database")
        if info:
            print("[Removing Ids] No videos to remove from the database")
    else:
        logger.info(
            f"[Removing Ids] Removed {removed_ids} videos and {removed_files} files"
        )
        if info:
            print(f"[Removing Ids] Removed {removed_ids} videos and {removed_files} files")
