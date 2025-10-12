"""
Module to manually add entry_id to every video entry in the DB if they not have some yet,
"""

import sqlite3
import time
from datetime import timedelta
from pathlib import Path

from FUNCTIONS.HELPERS.fileops import load
from FUNCTIONS.HELPERS.logger import setup_logger
from FUNCTIONS.sql_requests import commit_changes_to_db, get_videos_in_db

logger = setup_logger(__name__)


def add_entries_to_db(
    playlist_file: Path,
    cur: sqlite3.Cursor,
    conn: sqlite3.Connection,
) -> None:
    """
    Manually add entry_id for all entries into the DB,  normally it's automated but since i implementedthat yet,
    no video have a playlist entry
    """

    # Here it should be sorted in the order we want (old before)
    video_ids_map = load(playlist_file)
    video_ids = list(video_ids_map.keys())

    # If Youtube's API returns the playlist video in the newest first, reverse the list to have older first
    video_ids.reverse()

    vids_in_db = get_videos_in_db(True, cur)

    # Add the entries that aren't in the PLaylist list first, (usually the removed ones)
    for vid in vids_in_db:
        if vid not in video_ids:
            video_ids.insert(0, vid)

    updated_ids: int = 0
    failed_ids: int = 0
    total_videos = len(video_ids)

    if total_videos == 0:
        logger.warning(f"No videos found in {playlist_file}")
        return

    start_time = time.time()

    for video_id in video_ids:
        try:
            _ = cur.execute(
                "INSERT INTO ids (video_id) VALUES (?)",
                (video_id,),
            )
            updated_ids += 1
        except sqlite3.IntegrityError:
            # likely already exists (because video_id is UNIQUE)
            failed_ids += 1
        except sqlite3.OperationalError as e:
            logger.error(e)
            failed_ids += 1

    _ = commit_changes_to_db(conn, True)

    total_duration = str(timedelta(seconds=int(time.time() - start_time)))
    print(
        f"[DONE] | Processed {total_videos} videos " + f"(failed: {failed_ids}) in {total_duration}",
    )
    logger.info(
        f"Finished processing {total_videos} videos " + f"(failed: {failed_ids}) in {total_duration}"
    )
