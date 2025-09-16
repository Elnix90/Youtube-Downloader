from __future__ import annotations
from pathlib import Path
from sqlite3 import Connection, Cursor
from typing import Literal
import time


from FUNCTIONS.thumbnail import has_embedded_cover, embed_image_in_mp3, download_and_pad_image, remove_image_from_mp3
from FUNCTIONS.sql_requests import update_video_db
from FUNCTIONS.helpers import VideoInfo, fprint

from logger import setup_logger
logger = setup_logger(__name__)


def process_thumbnail_for_video(
    video_id: str,
    video_info: VideoInfo,
    filepath: Path,
    thumbnail_format: Literal["pad", "crop"],
    progress_prefix: str,
    info: bool,
    error: bool,
    cur: Cursor,
    conn: Connection,
    test_run: bool,
    recompute_thumbnails: bool
) -> float:
    """
    Process thumbnail for a single video: extract, download, embed, or update.
    Uses VideoInfo + update_video_metadata.
    """
    start_processing: float = time.time()



    title: str = video_info.get("title", "")
    update_thumbnail: bool = bool(video_info.get("update_thumbnail", False))
    remove_thumbnail: bool = bool(video_info.get("remove_thumbnail", False))
    thumbnail_url: str = video_info.get("thumbnail_url", "")
    this_thumbnail_path: Path = filepath.with_suffix(".png")


    embed_from_local_file: bool = False
    download_thumbnail: bool = recompute_thumbnails


    # Special calse: asked to emove thumbnail
    if remove_thumbnail:
        success_remove = remove_image_from_mp3(mp3_path=filepath, image_path=this_thumbnail_path, test_run=test_run)
        if success_remove:
            update_video_db(video_id=video_id, update_fields={"update_thumbnail": False},cur=cur, conn=conn)
            fprint(prefix=progress_prefix, title="[Remove thumbnail] Sucessfully removed thumbnail and file for '{filepath}'")
            logger.info(f"[Remove thumbnail] Sucessfully removed thumbnail and file for '{filepath}'")
        else:
            if error: print(f"\n[Remove thumbnail] Error removing thumbnail and file for '{filepath}'")
            logger.error(f"[Remove thumbnail] Error removing thumbnail and file for '{filepath}'")
        download_thumbnail = False

    # --- CASE A: File exists ---
    elif filepath.exists():
        if info: fprint(progress_prefix, f"Checking thumbnail for '{title}'")
        logger.info(f"[Thumbnail] Checking thumbnail for '{title}'")

        embedded_bytes = has_embedded_cover(filepath)

        # Save embedded cover to file if it's missing
        if embedded_bytes is not None and this_thumbnail_path and not this_thumbnail_path.exists():
            try:
                with open(this_thumbnail_path, "wb") as f:
                    _ = f.write(embedded_bytes)
                logger.info(f"[Thumbnail] Extracted embedded cover to '{this_thumbnail_path.name}'")
            except Exception as e:
                logger.warning(f"[Thumbnail] Failed to extract embedded cover: {e}")

        # Case 1: No cover at all (embedded or file)
        if embedded_bytes is None and (not this_thumbnail_path or not this_thumbnail_path.exists()):
            logger.debug(f"[Thumbnail] No embedded or local cover for '{filepath.name}'")
            download_thumbnail = True


        # Case 2: Local file exists and update requested
        elif this_thumbnail_path and this_thumbnail_path.exists() and update_thumbnail:
            logger.debug(f"[Thumbnail] Update requested: embedding thumbnail for '{filepath.name}'")
            embed_from_local_file = True


        # Case 3: Embedded image already exists and no update is needed
        elif embedded_bytes is not None and not update_thumbnail:
            if info: fprint(progress_prefix, f"Embedded cover already exists — skipping update for '{filepath.name}'")
            logger.debug(f"[Thumbnail] Embedded cover already exists — skipping update for '{filepath.name}'")

        # Case 4: Local file exists but no embedded cover, and update not explicitly requested
        elif this_thumbnail_path and this_thumbnail_path.exists() and embedded_bytes is None:
            logger.debug(f"[Thumbnail] Local file exists but no embedded cover — embedding now")
            embed_from_local_file = True


    # --- CASE B: File missing ---
    elif not filepath.exists():
        logger.error(f"[Thumbnail] Filepath doesn't exist -> cannot embed thumbnail: '{filepath}'")
        if error: print(f"\n[Thumbnail] Filepath doesn't exist -> cannot embed thumbnail: '{filepath}'")


    # If code goes here, the world explode
    else:
        logger.error(f"[Thumbnail] WTF error, code shoudln't be reachable :'{filepath}'")
        if error: print(f"\n[Thumbnail] WTF error, code shoudln't be reachable : '{filepath}'")



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
                        if info: fprint(prefix=progress_prefix, title=f"{'Downloaded & e' if download_thumbnail else 'E'}mbedded cover for '{filepath.name}'")
                        logger.info(f"[Thumbnail] Embedded cover for '{filepath.name}'")
                    else:
                        if error: print(f"\nFailed to embed into '{filepath.name}'")
                        logger.warning(f"[Thumbnail] Failed to embed into '{filepath.name}'")
                else:
                    if error: print(f"\nFailed to download from URL: '{thumbnail_url}'")
                    logger.warning(f"[Thumbnail] Failed to download from URL: '{thumbnail_url}'")
            except Exception as e:
                if error: print(f"\nException during thumbnail download/embed: {e}")
                logger.error(f"[Thumbnail] Exception during thumbnail download/embed: {e}")
        else:
            if error: print(f"\nNo thumbnail URL provided for '{filepath.name}'")
            logger.warning(f"[Thumbnail] No thumbnail URL provided for '{filepath.name}'")

    return time.time() - start_processing


