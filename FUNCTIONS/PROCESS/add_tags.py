"""
This module processes tags for individual video files.
It computes, merges, and embeds tags into MP3 files, and updates the database.
"""

import time
from pathlib import Path
from sqlite3 import Connection, Cursor

from FUNCTIONS.HELPERS.compute_tags_and_album import compute_tags
from FUNCTIONS.HELPERS.fprint import fprint
from FUNCTIONS.HELPERS.logger import setup_logger
from FUNCTIONS.set_tags_and_album import set_tags
from FUNCTIONS.sql_requests import update_video_db

logger = setup_logger(__name__)


def process_tags_for_video(
    video_id: str,
    title: str,
    uploader: str,
    existing_tags: set[str],
    filepath: Path,
    progress_prefix: str,
    info: bool,
    recompute_tags: bool,
    error: bool,
    cur: Cursor,
    conn: Connection,
    test_run: bool,
    sep: str,
    start_def: str,
    end_def: str,
    tag_sep: str,
) -> float:
    """
    Process tags for a single video:
    - Compute new tags if requested
    - Merge with existing tags
    - Embed tags into the MP3 file
    - Update the database

    Returns:
        float: Time in seconds spent processing tags
    """
    start_time: float = time.time()

    if info:
        fprint(progress_prefix, "Getting tags for ?", title)
    logger.info(f"[Tags] Getting tags for '{title}'")

    # Compute new tags if recompute requested
    computed_tags: set[str] = set()
    if title and uploader and recompute_tags:
        computed_tags = compute_tags(title=title, uploader=uploader)

    # Merge existing + computed tags
    all_tags: set[str] = existing_tags.union(computed_tags)

    # Embed tags into the MP3 file
    success: bool = set_tags(
        filepath=filepath,
        tags=all_tags,
        test_run=test_run,
        sep=sep,
        start_def=start_def,
        end_def=end_def,
        tag_sep=tag_sep,
    )

    # Update database with merged tags
    update_video_db(video_id, {"tags": list(all_tags)}, cur, conn, test_run)

    # Logging results
    if success and all_tags:
        if info:
            fprint(
                progress_prefix, f"Embedded {len(all_tags)} tags into ?", title
            )
        logger.info(
            f"[Tags] Embedded {len(all_tags)} tags into '{filepath.name}'"
        )

    elif not success:
        if error:
            print(f"\n[Tags] Error embedding tags into {filepath.name}")
        logger.error(f"[Tags] Error embedding tags into {filepath.name}")

    return time.time() - start_time
