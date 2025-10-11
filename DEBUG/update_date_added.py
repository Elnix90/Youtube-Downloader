"""
Module to update the date added of the database entries
"""

import sqlite3
import time
from datetime import timedelta
from pathlib import Path

from FUNCTIONS.HELPERS.fileops import load
from FUNCTIONS.HELPERS.fprint import fprint
from FUNCTIONS.HELPERS.logger import setup_logger
from FUNCTIONS.sql_requests import commit_changes_to_db, get_videos_in_db

logger = setup_logger(__name__)


def update_date_added(
    playlist_file: Path,
    cur: sqlite3.Cursor,
    conn: sqlite3.Connection,
) -> None:
    """
    Update the 'date_added' field for all videos listed in a playlist file.

    Displays progress and estimated time remaining (ETA).
    """
    video_ids_map = load(playlist_file)
    video_ids = list(video_ids_map.keys())

    vids_in_db = get_videos_in_db(True, cur)

    for vid in vids_in_db:
        if vid not in video_ids:
            video_ids.append(vid)

    updated_ids: int = 0
    errored_ids: int = 0
    total_videos = len(video_ids)

    if total_videos == 0:
        logger.warning(f"No videos found in {playlist_file}")
        return

    start_time = time.time()

    for index, video_id in enumerate(video_ids):
        try:
            _ = cur.execute(
                """
                UPDATE Videos
                SET date_added = ?
                WHERE video_id = ?
                """,
                (start_time + 5 * index, video_id),
            )
            updated_ids += 1
        except sqlite3.OperationalError:
            errored_ids += 1

        # Compute ETA
        elapsed = time.time() - start_time
        avg_time = elapsed / (index + 1) if not index else index
        remaining = total_videos - index
        eta_seconds = remaining * avg_time
        eta_formatted = str(timedelta(seconds=int(eta_seconds)))

        # Display progress
        fprint(
            f"{index}/{total_videos} |  ETA: {eta_formatted} | ",
            f"Updated {updated_ids}, failed {errored_ids}",
        )

    _ = commit_changes_to_db(conn, True)

    total_duration = str(timedelta(seconds=int(time.time() - start_time)))
    fprint(
        "[DONE] | ",
        f"Updated {updated_ids}/{total_videos} videos " + f"(failed: {errored_ids}) in {total_duration}",
    )
    logger.info(
        f"Finished updating {updated_ids}/{total_videos} videos " + f"(failed: {errored_ids}) in {total_duration}"
    )
