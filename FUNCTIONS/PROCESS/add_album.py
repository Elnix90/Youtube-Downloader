from pathlib import Path
import time

from FUNCTIONS.helpers import fprint
from FUNCTIONS.album_system import compute_album, set_album

from logger import setup_logger
logger = setup_logger(__name__)




def process_album_for_video(
    uploader: str,
    title: str,
    filepath: Path,
    progress_prefix: str,
    info: bool,
    recompute_album: bool,
    error: bool,
    test_run: bool,
) -> float:
    """
    Process album for a single video: compute, choose, and embed into MP3.
    Uses VideoInfo + update_video_metadata.
    """

    start_processing: float = time.time()

    if info:
        fprint(prefix=progress_prefix, title=f"Getting album for '{title}'")
    logger.info(f"[Album] Getting album for '{title}'")

    computed_album: str = "Private"

    if title and uploader and recompute_album:
        computed_album = compute_album(title=title, uploader=uploader)

    success: bool = set_album(
        filepath=filepath,
        album=computed_album,
        test_run=test_run,
    )



    if success:
        if info: fprint(progress_prefix, f"Embedded album '{computed_album}' into '{title}'")
        logger.info(f"[Album] Embedded album '{computed_album}' into '{title}'")
    else:
        if error: print(f"\n[Album] Error embedding album into '{title}'")
        logger.error(f"[Album] Error embedding album into '{title}'")

    return time.time() - start_processing
