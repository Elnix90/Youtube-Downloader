"""
This module processes the album metadata for individual video files.
It can compute the album from the uploader/title, read existing ID3 tags,
and embed the album into an MP3 file.
"""

from pathlib import Path
import time


from FUNCTIONS.HELPERS.compute_tags_and_album import compute_album
from FUNCTIONS.HELPERS.fprint import fprint
from FUNCTIONS.set_tags_and_album import set_album
from FUNCTIONS.metadata import read_id3_tag


from FUNCTIONS.HELPERS.logger import setup_logger
logger = setup_logger(__name__)


def process_album_for_video(
    uploader: str,
    title: str,
    filepath: Path,
    progress_prefix: str,
    info: bool,
    recompute_album: bool,
    test_run: bool,
) -> float:
    """
    Process album for a single video: compute, choose, and embed into MP3.
    Uses VideoInfo + update_video_metadata.
    """

    start_processing: float = time.time()

    if info:
        fprint(progress_prefix, "Getting album for ?", title)

    logger.debug(f"[Album] Getting album for '{title}'")
    actual_album, state = read_id3_tag(filepath=filepath, frame_id="TALB")
    computed_album: str = "Private"

    if title and uploader and recompute_album:
        computed_album = compute_album(title=title, uploader=uploader)

    update_album: bool = False
    if state == 0:
        if isinstance(actual_album, list):
            actual_album = str(actual_album[0])
        else:
            actual_album = str(actual_album)
        if computed_album != actual_album:
            update_album = True
    else:
        update_album = True

    if update_album:
        success: bool = set_album(
            filepath=filepath,
            album=computed_album,
            test_run=test_run,
        )

        if success:
            if info:
                fprint(
                    progress_prefix,
                    f"Embedded album '{computed_album}' into ?",
                    title
                )
            logger.info(
                f"[Album] Embedded album '{computed_album}' into '{title}'"
            )

        else:
            logger.error(f"[Album] Error embedding album into '{title}'")

    return time.time() - start_processing
