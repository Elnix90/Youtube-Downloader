from pathlib import Path
from sqlite3 import Connection, Cursor


from FUNCTIONS.fileops import load
from FUNCTIONS.sql_requests import get_videos_in_list, insert_video_db
from FUNCTIONS.helpers import VideoInfoMap, VideoInfo, fprint

from logger import setup_logger
logger = setup_logger(__name__)


def add_new_ids_to_database(
    video_id_file: Path,
    ids_presents_in_down_dir: VideoInfoMap,
    add_folder_files_not_in_list: bool,
    info: bool,
    errors: bool,
    cur: Cursor,
    conn: Connection,
) -> None:
    """
    Fetches the ids from a given file and adds them to the database if not already present.
    Uses metadata from ids_presents_in_down_dir when available, otherwise inserts defaults.
    Ensures all VideoInfo fields are present.
    """

    # Fetch existing video_ids from database
    existing_video_ids: set[str] = set[str](get_videos_in_list(cur))
    video_ids: set[str] = set()

    try:
        video_ids = set(load(file=video_id_file))
    except Exception as e:
        logger.error(f"[Adding ids] Error loading video ID file ({video_id_file}): {e}")
        if errors:
            print(f"[Adding ids] Error loading video ID file ({video_id_file}): {e}")


    if add_folder_files_not_in_list:
        video_ids.update(set[str](ids_presents_in_down_dir.keys()))

    to_add: set[str] = video_ids - existing_video_ids


    added_ids: int = 0


    # Default fields for a new video
    default_fields: VideoInfo = {
        "status": 3,
        "recompute_tags": True,
        "recompute_album": True,
        "try_lyrics_if_not": True,
        "remove_lyrics": False,
        "remove_thumbnail": False,
        "update_thumbnail": False,
    }

    for video_id in to_add:
        vi: VideoInfo = ids_presents_in_down_dir.get(video_id, {})
        video_data: VideoInfo = {**default_fields, **vi, "video_id": video_id}

        try:
            insert_video_db(video_data=video_data, cur=cur, conn=conn)
            added_ids += 1
            if info:
                fprint("",f"[Adding ids] Added {added_ids} ids in the database")

        except Exception as e:
            logger.error(f"[Adding ids] Failed to insert/update video_id '{video_id}': {e}")
            if errors: 
                print(f"\n[Adding ids] Failed to insert/update video_id '{video_id}': {e}")

    conn.commit()
    logger.info(
        "[Adding ids] "
        + ("All ids are in the database" if not to_add else f"Added/Updated {added_ids} ids to the database")
    )
    if info and not to_add:
        print("[Adding ids] All ids are in the database")
    elif info:
        print()
