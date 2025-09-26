from typing import Literal


from pathlib import Path
from sqlite3 import Connection, Cursor


from FUNCTIONS.HELPERS.fileops import load
from FUNCTIONS.HELPERS.fprint import fprint
from FUNCTIONS.sql_requests import get_video_info_from_db, get_videos_in_list, insert_video_db, update_video_db
from FUNCTIONS.HELPERS.helpers import VideoInfoMap, VideoInfo, youtube_required_info

from FUNCTIONS.HELPERS.logger import setup_logger
logger = setup_logger(__name__)


def add_new_ids_to_database(
    video_id_file: Path,
    ids_presents_in_down_dir: VideoInfoMap,
    add_folder_files_not_in_list: bool,
    include_not_status0: bool,
    test_run: bool,
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

    existing_video_ids: list[str] = get_videos_in_list(include_not_status0=True,cur=cur)
    video_ids: list[str] = list[str]()

    try:
        video_ids = load(file=video_id_file)
    except Exception as e:
        logger.error(f"[Adding ids] Error loading video ID file '{video_id_file}': {e}")
        if errors: print(f"\n[Adding ids] Error loading video ID file '{video_id_file}': {e}")


    # If asked, insert the videos already presents in the down_dir by date order (should be sorted due to SELECT query who sort by date added)
    if add_folder_files_not_in_list:
        to_add = video_ids
        for video_id in existing_video_ids:
            if video_id not in to_add:
                to_add.insert(0, video_id)

    # Build to_add list just by checking that the video is not aleardy in the datalist
    else:
        to_add: list[str] = [video_id for video_id in video_ids if video_id not in existing_video_ids]

    correct_ids: int = 0
    added_ids: int = 0
    updated_ids: int = 0

    for video_id in to_add:
        # If the video is in the download dir, and coreectly formatted it will get some data, that i'll use later if the list entry is empty or corrupted
        video_data: VideoInfo = ids_presents_in_down_dir.get(video_id, {})
        status: Literal[0, 1, 2, 3] = video_data.get("status", 3)
        try:
            if video_id not in existing_video_ids:
                if (not include_not_status0 and status == 3) or include_not_status0:
                    video_data["video_id"] = video_id 
                    insert_video_db(
                        video_data,
                        cur,
                        conn,
                        test_run
                        )
                    added_ids += 1

            else:
                db_data = get_video_info_from_db(video_id=video_id, cur=cur)
                if not all(key in db_data and db_data[key] is not None for key in youtube_required_info):
                    if all(key in video_data and video_data[key] is not None for key in youtube_required_info):
                        update_video_db(
                            video_id,
                            video_data,
                            cur,
                            conn,
                            test_run
                        )
                        updated_ids += 1
                else:
                    correct_ids += 1

            if info: fprint("",f"[Adding ids] Added {added_ids} ids, Updated {updated_ids} ids, {correct_ids} ids ok")


        except Exception as e:
            logger.error(f"[Adding ids] Failed to insert / update video_id '{video_id}': {e}")
            if errors: 
                print(f"\n[Adding ids] Failed to insert / update video_id '{video_id}': {e}")

    if not test_run: conn.commit()
    logger.info("[Adding ids] " + ("All ids are in the database" if not to_add else f"Added {added_ids}, updated {update_video_db} ids to the database"))
    if info and not to_add: print("[Adding ids] All ids are in the database")
    elif info: print()
