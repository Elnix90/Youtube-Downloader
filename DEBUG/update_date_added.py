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
    video_ids = load(playlist_file)

    updated_ids: int = 0
    errored_ids: int = 0
    total_videos = len(video_ids)

    if total_videos == 0:
        logger.warning(f"No videos found in {playlist_file}")
        return

    start_time = time.time()

    for index, video_id in enumerate(video_ids, start=1):
        try:
            _ = cur.execute(
                """
                UPDATE Videos
                SET date_added = ?
                WHERE video_id = ?
                """,
                (time.time(), video_id.video_id),
            )
            updated_ids += 1
        except sqlite3.OperationalError:
            errored_ids += 1

        # Compute ETA
        elapsed = time.time() - start_time
        avg_time = elapsed / index
        remaining = total_videos - index
        eta_seconds = remaining * avg_time
        eta_formatted = str(timedelta(seconds=int(eta_seconds)))

        # Display progress
        fprint(
            f"{index}/{total_videos} |  ETA: {eta_formatted} | ",
            f"Updated {updated_ids}, failed {errored_ids}",
        )

        time.sleep(0.1)

    conn.commit()

    total_duration = str(timedelta(seconds=int(time.time() - start_time)))
    fprint(
        "[DONE]",
        f"Updated {updated_ids}/{total_videos} videos " + f"(failed: {errored_ids}) in {total_duration}",
    )
    logger.info(
        f"Finished updating {updated_ids}/{total_videos} videos " + f"(failed: {errored_ids}) in {total_duration}"
    )
