from pathlib import Path
from sqlite3 import Connection, Cursor


from FUNCTIONS.HELPERS.fileops import load
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
    test_run: bool
) -> None:
    """
    Remove id from list if not in playlist
    """
    existing_video_ids: set[str] = set[str](get_videos_in_list(include_not_status0=include_not_status0,cur=cur))

    video_ids: set[str] = set[str](load(video_id_file))
    not_in_video_ids: set[str] = existing_video_ids - video_ids

    removed_ids = 0
    removed_files = 0


    for video_id in not_in_video_ids:
        data = get_video_info_from_db(video_id, cur)
        filename = data.get("filename","")
        
        if filename:
            try:
                if not test_run:
                    filepath: Path = (download_path / filename).with_suffix(suffix="mp3")
                    lyrics_path: Path = (download_path / filename).with_suffix(suffix="lrc")
                    thumbnail_path: Path = (download_path / filename).with_suffix(suffix="png")

                    filepath.unlink(missing_ok=True)
                    lyrics_path.unlink(missing_ok=True)
                    thumbnail_path.unlink(missing_ok=True)

                removed_files += 1
            except OSError as e:
                logger.error(f"[Removing Ids] Error while removing {filename}: {e}")
                if error: print(f"[Removing Ids] Error while removing {filename}: {e}")
            except Exception as e:
                logger.error(f"[Removing Ids] Unknown error while deleting {filename}: {e}")
                if error: print(f"[Removing Ids] Unknown error while deleting {filename}: {e}")

        _ = cur.execute("DELETE FROM videos WHERE video_id = ?", (video_id,))
        removed_ids += 1
        if info: fprint("",f"[Removing Ids] Removed {removed_ids} from list")

    if not test_run: conn.commit()
    if info: print()
    if removed_ids == 0:
        logger.info("[Removing Ids] No video to remove from the database")
        if info: print("[Removing Ids] No video to remove from the database")
    else:
        logger.info(f"[Removing Ids] Removed {removed_ids} videos and {removed_files} files")
        if info: print(f"[Removing Ids] Removed {removed_ids} videos and {removed_files} files")