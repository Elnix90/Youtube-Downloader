from pathlib import Path
from sqlite3 import Connection, Cursor
import time


from FUNCTIONS.sql_requests import update_video_db
from FUNCTIONS.helpers import VideoInfo, fprint
from FUNCTIONS.tags_system import compute_tags, set_tags

from logger import setup_logger
logger = setup_logger(__name__)


def process_tags_for_video(
    video_id: str,
    video_info: VideoInfo,
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
    tag_sep: str
) -> float:
    """
    Process tags for a single video: compute, merge, and embed into MP3.
    Uses VideoInfo + update_video_metadata.
    """

    start_processing: float = time.time()


    title: str = filepath.name
    uploader: str = video_info.get("uploader", "")
    existing_tags: set[str] = set(video_info.get("tags", []))
    file_order_to_recompute: bool = video_info.get("recompute_tags", True)

    if info: fprint(prefix=progress_prefix, title=f"Getting tags for '{title}'")
    logger.info(f"[Tags] Getting tags for '{title}'")

    computed_tags: set[str] = set()

    if file_order_to_recompute and title and uploader and recompute_tags:
        computed_tags = compute_tags(title, uploader, error=error)


    # Merge existing + computed
    all_tags: set[str] = existing_tags.union(computed_tags)

    success: bool = set_tags(
        filepath=filepath,
        tags=all_tags,
        error=error,
        test_run=test_run,
        sep=sep,
        start_def=start_def,
        end_def=end_def,
        tag_sep=tag_sep
    )

    # Update DB with merged tags
    update_video_db(video_id, {"tags": list(all_tags)}, cur, conn)

    if success and all_tags:
        if info: fprint(progress_prefix, f"Embedded {len(all_tags)} tags into '{filepath.name}'")
        logger.info(f"[Tags] Embedded {len(all_tags)} tags into '{filepath.name}'")
    if not success:
        if error: print(f"\n[Tags] Error embedding tags into {filepath.name}")
        logger.error(f"[Tags] Error embedding tags into {filepath.name}")

    return time.time() - start_processing


