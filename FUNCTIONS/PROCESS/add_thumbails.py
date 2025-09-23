from __future__ import annotations
from pathlib import Path
from sqlite3 import Connection, Cursor
from typing import Literal
import time


from FUNCTIONS.HELPERS.fprint import fprint
from FUNCTIONS.thumbnail import has_embedded_cover, embed_image_in_mp3, download_and_pad_image, remove_image_from_mp3
from FUNCTIONS.sql_requests import update_video_db
from FUNCTIONS.HELPERS.helpers import thumbnail_png_path_for_mp3

from FUNCTIONS.HELPERS.logger import setup_logger
logger = setup_logger(__name__)


def process_thumbnail_for_video(
    video_id: str,

    title: str,
    update_thumbnail: bool,
    remove_thumbnail: bool,
    thumbnail_url: str,

    filepath: Path,
    thumbnail_format: Literal["pad", "crop"],
    progress_prefix: str,
    info: bool,
    error: bool,
    cur: Cursor,
    conn: Connection,
    test_run: bool,
    force_recompute_thumbnails: bool
) -> float:
    """
    Process thumbnail for a single video: extract, download, embed, or update.
    """
    start_processing: float = time.time()

    this_thumbnail_path: Path = thumbnail_png_path_for_mp3(mp3_path=filepath)
    embed_from_local_file: bool = False
    download_thumbnail: bool = force_recompute_thumbnails

    # Asked to remove thumbnail
    if remove_thumbnail:
        success_remove = remove_image_from_mp3(mp3_path=filepath, image_path=this_thumbnail_path, test_run=test_run)
        if success_remove:
            update_video_db(video_id=video_id, update_fields={"update_thumbnail": False},cur=cur, conn=conn)
            fprint(progress_prefix, f"[Remove thumbnail] Sucessfully removed thumbnail and file for '{filepath}'")
            logger.info(f"[Remove thumbnail] Sucessfully removed thumbnail and file for '{filepath}'")
        else:
            if error: print(f"\n[Remove thumbnail] Error removing thumbnail and file for '{filepath}'")
            logger.error(f"[Remove thumbnail] Error removing thumbnail and file for '{filepath}'")
        return time.time() - start_processing

    # File exists
    elif filepath.exists():
        if info: fprint(progress_prefix, f"Checking thumbnail for ?", title)
        logger.verbose(f"[Thumbnail] Checking thumbnail for '{title}'")

        embedded_bytes = has_embedded_cover(filepath)

        # Save embedded cover to file if it's missing
        if embedded_bytes is not None and this_thumbnail_path and not this_thumbnail_path.exists():
            try:
                with open(this_thumbnail_path, "wb") as f:
                    _ = f.write(embedded_bytes)
                logger.info(f"[Thumbnail] Extracted embedded cover to '{title}'")
            except Exception as e:
                logger.warning(f"[Thumbnail] Failed to extract embedded cover: {e}")

        # Case 1: No cover at all (embedded or file)
        if embedded_bytes is None and (not this_thumbnail_path or not this_thumbnail_path.exists()):
            logger.debug(f"[Thumbnail] No embedded or local cover for '{title}'")
            download_thumbnail = True


        # Case 2: Local file exists and update requested
        elif this_thumbnail_path and this_thumbnail_path.exists() and update_thumbnail:
            logger.debug(f"[Thumbnail] Update requested: embedding thumbnail for '{title}'")
            embed_from_local_file = True


        # Case 3: Embedded image already exists and no update is needed
        elif embedded_bytes is not None and not update_thumbnail:
            if info: fprint(progress_prefix, f"Embedded cover already exists — skipping update for ?", title)
            logger.debug(f"[Thumbnail] Embedded cover already exists — skipping update for '{title}'")

        # Case 4: Local file exists but no embedded cover, and update not explicitly requested
        elif this_thumbnail_path and this_thumbnail_path.exists() and embedded_bytes is None:
            logger.debug(f"[Thumbnail] Local file exists but no embedded cover — embedding now")
            embed_from_local_file = True


    # File missing
    else:
        logger.error(f"[Thumbnail] Filepath doesn't exist -> cannot embed thumbnail: '{filepath}'")
        if error: print(f"\n[Thumbnail] Filepath doesn't exist -> cannot embed thumbnail: '{filepath}'")


    # Downloads or embed if asked
    if download_thumbnail or embed_from_local_file:
        if thumbnail_url:
            try:
                success: bool = True
                if download_thumbnail :
                    success = download_and_pad_image(image_url=thumbnail_url, save_path=this_thumbnail_path, thumbnail_format=thumbnail_format)
                    logger.debug(f"[Thumbnail] Downloaded cover at '{thumbnail_url}'")
                if success is True:
                    embed_success: bool = embed_image_in_mp3(mp3_path=filepath, image_path=this_thumbnail_path,test_run=test_run)
                    if embed_success is True:
                        update_video_db(video_id=video_id, update_fields={"update_thumbnail": False}, cur=cur, conn=conn)
                        if info: fprint(progress_prefix, f"{'Downloaded & e' if download_thumbnail else 'E'}mbedded cover for ?", title)
                        logger.info(f"[Thumbnail] Embedded cover for '{title}'")
                    else:
                        if error: print(f"\nFailed to embed into '{title}'")
                        logger.warning(f"[Thumbnail] Failed to embed into '{title}'")
                else:
                    if error: print(f"\nFailed to download from URL: '{thumbnail_url}'")
                    logger.warning(f"[Thumbnail] Failed to download from URL: '{thumbnail_url}'")
            except Exception as e:
                if error: print(f"\nException during thumbnail download/embed: {e}")
                logger.error(f"[Thumbnail] Exception during thumbnail download/embed: {e}")
        else:
            if error: print(f"\nNo thumbnail URL provided for '{title}'")
            logger.warning(f"[Thumbnail] No thumbnail URL provided for '{title}'")

    return time.time() - start_processing


