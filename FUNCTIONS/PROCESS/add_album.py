from pathlib import Path
import time

from FUNCTIONS.helpers import VideoInfo, fprint
from FUNCTIONS.album_system import compute_album, set_album

from logger import setup_logger
logger = setup_logger(__name__)




def process_album_for_video(
    video_info: VideoInfo,
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

    title: str = video_info.get("title", "")
    uploader: str = video_info.get("uploader", "")
    file_order_to_recompute: bool = video_info.get("recompute_album", True)

    if info:
        fprint(prefix=progress_prefix, title=f"Getting album for '{title}'")
    logger.info(f"[Album] Getting album for '{title}'")

    computed_album: str = "Private"

    if file_order_to_recompute and title and uploader and recompute_album:
        computed_album = compute_album(title=title, uploader=uploader)

    success: bool = set_album(
        filepath=filepath,
        album=computed_album,
        test_run=test_run,
    )



    if success:
        if info:
            fprint(progress_prefix, f"Embedded album '{computed_album}' into '{filepath.name}'")
        logger.info(f"[Album] Embedded album '{computed_album}' into '{filepath.name}'")
    else:
        if error:
            print(f"\n[Album] Error embedding album into {filepath.name}")
        logger.error(f"[Album] Error embedding album into {filepath.name}")

    return time.time() - start_processing
