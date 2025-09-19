from pathlib import Path
import sqlite3
import time

from FUNCTIONS.fileops import load
from FUNCTIONS.helpers import fprint
from logger import setup_logger
logger = setup_logger(__name__)



def update_date_added(playlist_file: Path, cur: sqlite3.Cursor) -> None:
    video_ids = load(playlist_file)

    updated_ids: int = 0
    errored_ids: int = 0
    total_videos= len(video_ids)

    for video_id in video_ids:
        try:
            _ = cur.execute("""
                UPDATE Videos
                SET date_added = ?
                WHERE video_id = ?
            """,
            (time.time(),video_id)
            )
            updated_ids += 1
        except sqlite3.OperationalError:
            errored_ids += 1
        fprint(prefix=f"{updated_ids + errored_ids}/{total_videos} | ",title=f"Updated {updated_ids}, failed to update {errored_ids} (likely not present db)")