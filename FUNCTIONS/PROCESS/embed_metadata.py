from pathlib import Path
import json
from sqlite3 import Cursor
import time

from FUNCTIONS.helpers import fprint
from FUNCTIONS.metadata import write_id3_tag
from FUNCTIONS.sql_requests import get_video_info_from_db
from logger import setup_logger

logger = setup_logger(__name__)


def embed_metadata_for_video(
    video_id: str,
    filepath: Path,
    progress_prefix: str,
    cur: Cursor,
    test_run: bool,
    info: bool,
    error: bool,
) -> float:
    """
    Embed metadata from DB into a single MP3 file using get_video_info.
    Also sets the 'TDRC' (date) frame to the video's date_added.
    """

    start_processing: float = time.time()

    video_info = get_video_info_from_db(video_id=video_id, cur=cur)
    date = str(video_info.get('date_added',))

    title: str = filepath.name

    if info: fprint(prefix=progress_prefix, title=f"Embedding metadata for '{title}'")
    logger.debug(f"[Metadata] Embedding metadata for '{title}'")


    # Embed the id in the dat field, to sort the video in the player
    success_date: bool = True
    if date:
        success_date = write_id3_tag(
            filepath=filepath,
            frame_id="TDRC",
            data=date,
            test_run=test_run
        )
        if not success_date:
            if error: print(f"\n[Metadata] Failed to embed date for '{title}'")
            logger.warning(f"[Metadata] Failed to embed date for '{title}'")
        else:
            if info: fprint(prefix=progress_prefix, title=f"Embedded date for '{title}'")
            logger.debug(f"[Metadata] Embedded date for '{title}'")


    # Embed full metadata as JSON
    success_meta: bool = write_id3_tag(
        filepath=filepath,
        frame_id="TXXX:metadata",
        data=json.dumps(video_info, ensure_ascii=True),
        test_run=test_run
    )

    if not success_meta:
        if error: print(f"\n[Metadata] Failed to embed metadata for '{title}'")
        logger.warning(f"[Metadata] Failed to embed metadata for '{title}'")
    else:
        if info: fprint(prefix=progress_prefix, title=f"Embedded metadata for '{title}'")
        logger.debug(f"[Metadata] Embedded metadata for '{title}'")


    return time.time() - start_processing
