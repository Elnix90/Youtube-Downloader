"""
Computes every ids in the playliost fetch and add  the new ones into the DB
"""

from __future__ import annotations

from pathlib import Path
from sqlite3 import Connection, Cursor

from FUNCTIONS.HELPERS.fileops import load
from FUNCTIONS.HELPERS.fprint import fprint
from FUNCTIONS.HELPERS.helpers import VideoInfo, VideoInfoMap
from FUNCTIONS.HELPERS.logger import setup_logger
from FUNCTIONS.sql_requests import commit_changes_to_db, get_videos_in_db, insert_video_db

logger = setup_logger(__name__)


def add_new_ids_to_database(
    video_id_file: Path,
    ids_present_in_down_dir: VideoInfoMap,
    add_folder_files_not_in_list: bool,
    include_not_status0: bool,
    test_run: bool,
    info: bool,
    errors: bool,
    cur: Cursor,
    conn: Connection,
) -> None:
    """
    Load video data from a JSON file and add or update entries in the database.
    """

    try:
        playlist_entries = load(video_id_file)
    except Exception as e:  # pylint: disable=broad-exception-caught
        msg = f"[Adding IDs] Error loading '{video_id_file}': {e}"
        logger.error(msg)
        if errors:
            print(msg)
        return

    existing_video_ids = get_videos_in_db(True, cur)
    file_video_ids = list(playlist_entries.keys())

    # First; determine which video IDs to process

    # 1. Only add the videos that are in the file got by the fetch
    to_add = [vid for vid in file_video_ids if vid not in existing_video_ids]

    # 2. If asked to use also the videos that are in the download dir but not in the list fetched
    if add_folder_files_not_in_list:
        for vid in ids_present_in_down_dir.keys():
            if vid not in to_add and vid not in existing_video_ids:
                to_add.insert(0, vid)

    added_ids = 0

    for video_id in to_add:
        try:
            # Video data from local directory (downloaded files)
            video_data = ids_present_in_down_dir.get(video_id, {})
            status = video_data.get("status", 3)

            # Playlist info from the JSON file (fresh metadata)
            playlist_info: VideoInfo | None = playlist_entries.get(video_id)

            # Merge if both exist
            if playlist_info:
                for key, value in playlist_info.items():
                    if key in VideoInfo.__annotations__ and value is not None:
                        video_data[key] = value
                logger.debug(f"[Merge] Merged playlist info into {video_id}")

            if include_not_status0 or status == 3:
                video_data["video_id"] = video_id
                insert_video_db(video_data, cur, conn, test_run)
                added_ids += 1

                # Progress display
                if info:
                    fprint("", f"[Adding IDs] Added {added_ids}")
            else:
                logger.info(
                    "[Adding ids] Did not add either cause status is private or unavailable or already downloaded or not asked to include them"
                )

        except Exception as e:  # pylint: disable=broad-exception-caught
            msg = f"[Adding IDs] Failed for '{video_id}': {e}"
            logger.error(msg)
            if errors:
                print(msg)

    _ = commit_changes_to_db(conn, True, test_run)

    summary = f"[Adding IDs] Added {added_ids}"
    # summary = f"[Adding IDs] Added {added_ids} | " + f"Updated {updated_ids} | " + f"{correct_ids} already OK"
    logger.info(summary)
