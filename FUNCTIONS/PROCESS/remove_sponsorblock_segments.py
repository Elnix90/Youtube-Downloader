from pathlib import Path
import subprocess
import time
from sqlite3 import Connection, Cursor


from FUNCTIONS.helpers import fprint
from FUNCTIONS.sponsorblock import get_skip_segments, cut_segments_ffmpeg
from FUNCTIONS.sql_requests import update_video_db

from logger import setup_logger
logger = setup_logger(__name__)


def remove_sponsorblock_segments_for_video(
    video_id: str,
    title: str,
    filepath: Path,
    removed_segments_int: int,
    removed_segments_duration: float,
    cur: Cursor,
    conn: Connection,
    progress_prefix: str,
    categories: list[str],
    info: bool,
    test_run: bool
) -> float:
    """
    Process SponsorBlock removal for a single video_id.
    """
    start_cut: float = time.time()

    # --- Fetch existing skips from DB ---
    _ = cur.execute("""
        SELECT segment_start, segment_end
        FROM removed_segments
        WHERE video_id = ?
    """, (video_id,))

    skips = [(row["segment_start"], row["segment_end"]) for row in cur.fetchall()]  # pyright: ignore[reportAny]


    # --- If values are defined (not None) ---

    if (removed_segments_int == -1 and removed_segments_duration == -1.0) or (removed_segments_int > 0 and removed_segments_duration > 0.0):
        if info: fprint(progress_prefix, f"Skipping -> already processed", stitle=title)
        logger.debug(f"[Sponsorblock] Skipping -> already processed '{title}'")
        return time.time() - start_cut


    # --- If no skips in DB and the values of segments skipped are None, query SponsorBlock ---
    elif not skips:
        logger.debug(f"[Sponsorblock] No skips in DB, querying API for '{title}'")
        skips = get_skip_segments(video_id, categories=categories)

    # --- If no skips even after SponsorBlock query, means that the video has not, so update the fields to not retry later---
    if not skips:
        if info: fprint(progress_prefix, f"No segments to cut for", stitle=title)
        logger.debug(f"[Sponsorblock] No segments to cut for '{title}'")
        update_video_db(
            video_id,
            {
                "removed_segments_int": -1,
                "removed_segments_duration": -1.0,
            },
            cur,
            conn
        )
        return time.time() - start_cut


    # --- Perform cutting ---
    if info:
        fprint(progress_prefix, f"Cutting {len(skips)} segments from", stitle=title)
    logger.info(f"[Sponsorblock] Cutting {len(skips)} segments from '{title}'")

    temp_output = filepath.with_suffix(".tmp.mp3")
    try:
        total_removed = cut_segments_ffmpeg(filepath, temp_output, skips,test_run)
        successful_segments = len(skips)
        update_video_db(
            video_id,
            {
                "removed_segments_int": successful_segments,
                "removed_segments_duration": total_removed,
                "skips": skips,
            },
            cur,
            conn
        )

        logger.info(f"[Sponsorblock] Removed {successful_segments} segments ({round(total_removed, 1)}s) from '{title}'")

        _ = temp_output.replace(filepath)

        if info:
            fprint(progress_prefix, f"Sucessfully cutted {len(skips)} segments from", stitle=title)
        logger.info(f"[Sponsorblock] Sucessfully cutted {len(skips)} segments from '{title}'")

    except subprocess.CalledProcessError:
        logger.error(f"[Sponsorblock] Error cutting segments for '{title}'")
        if temp_output.exists():
            temp_output.unlink()

    return time.time() - start_cut



