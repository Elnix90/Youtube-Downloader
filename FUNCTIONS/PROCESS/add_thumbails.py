"""
Processes thumbnails for a given video ID.

Provides functionality to check, download, embed, update, or remove
thumbnails from MP3 files. Logs actions and optionally prints
progress messages.

Functions:
    process_thumbnail_for_video: Process thumbnail for a single video.
"""

from __future__ import annotations

import time
from pathlib import Path
from sqlite3 import Connection, Cursor
from typing import Literal

from FUNCTIONS.HELPERS.fprint import fprint
from FUNCTIONS.HELPERS.helpers import thumbnail_png_path_for_mp3
from FUNCTIONS.HELPERS.logger import setup_logger
from FUNCTIONS.sql_requests import update_video_db
from FUNCTIONS.thumbnail import (
    download_and_pad_image,
    embed_image_in_mp3,
    has_embedded_cover,
    remove_image_from_mp3,
)

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
    cur: Cursor,
    conn: Connection,
    test_run: bool,
    force_recompute_thumbnails: bool,
) -> float:
    """
    Process a thumbnail for a single video.

    Steps:
        - Remove thumbnail if requested.
        - Extract embedded cover if missing as file.
        - Download and pad image if no cover exists or force update.
        - Embed local or downloaded thumbnail into MP3.
        - Update database with thumbnail status.

    Args:
        video_id (str): YouTube video identifier.
        title (str): Video title.
        update_thumbnail (bool): Flag to force update of existing thumbnail.
        remove_thumbnail (bool): Flag to remove existing thumbnail.
        thumbnail_url (str): URL of the thumbnail to download.
        filepath (Path): Path to the MP3 file.
        thumbnail_format (Literal['pad', 'crop']): How to format thumbnail.
        progress_prefix (str): Prefix string for progress messages.
        info (bool): Print info messages if True.
        cur (Cursor): Database cursor.
        conn (Connection): Database connection.
        test_run (bool): Skip actual file modifications if True.
        force_recompute_thumbnails (bool): Force re-download/re-embedding.

    Returns:
        float: Time in seconds taken to process the thumbnail.
    """
    start_processing: float = time.time()
    this_thumbnail_path: Path = thumbnail_png_path_for_mp3(mp3_path=filepath)
    embed_from_local_file: bool = False
    download_thumbnail: bool = force_recompute_thumbnails

    # Remove thumbnail if requested
    if remove_thumbnail:
        success_remove = remove_image_from_mp3(
            mp3_path=filepath,
            image_path=this_thumbnail_path,
            test_run=test_run,
        )
        if success_remove:
            update_video_db(
                video_id,
                {"update_thumbnail": False},
                cur,
                conn,
                test_run,
            )
            fprint(
                progress_prefix,
                "[Remove thumbnail] Successfully removed thumbnail and "
                + f"file for '{filepath}'",
            )
            logger.info(
                "[Remove thumbnail] Successfully removed thumbnail and "
                + f"file for '{filepath}'"
            )
        else:
            logger.error(
                "[Remove thumbnail] Error removing thumbnail and file for "
                + f"'{filepath}'"
            )
        return time.time() - start_processing

    # File exists
    elif filepath.exists():
        if info:
            fprint(progress_prefix, f"Checking thumbnail for '{title}'")
        logger.verbose(f"[Thumbnail] Checking thumbnail for '{title}'")

        embedded_bytes = has_embedded_cover(filepath)

        # Save embedded cover to file if missing
        if embedded_bytes is not None and not this_thumbnail_path.exists():
            try:
                if not test_run:
                    with open(this_thumbnail_path, "wb") as f:
                        _ = f.write(embedded_bytes)
                logger.info(
                    "[Thumbnail] Extracted embedded cover to '{title}'"
                )
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.warning(
                    f"[Thumbnail] Failed to extract embedded cover: {e}"
                )

        # Case 1: No cover at all
        if embedded_bytes is None and not this_thumbnail_path.exists():
            logger.debug(
                f"[Thumbnail] No embedded or local cover for '{title}'"
            )

            download_thumbnail = True

        # Case 2: Local file exists and update requested
        elif this_thumbnail_path.exists() and update_thumbnail:
            logger.debug(
                "[Thumbnail] Update requested: embedding thumbnail "
                + f"for '{title}'"
            )
            embed_from_local_file = True

        # Case 3: Embedded image exists and no update needed
        elif embedded_bytes is not None and not update_thumbnail:
            if info:
                fprint(
                    progress_prefix,
                    "Embedded cover already exists - skipping update for "
                    + f"'{title}'",
                )
            logger.debug(
                "[Thumbnail] Embedded cover already exists - skipping "
                + f"update for '{title}'"
            )

        # Case 4: Local file exists but no embedded cover
        elif this_thumbnail_path.exists() and embedded_bytes is None:
            logger.debug(
                "[Thumbnail] Local file exists but no embedded cover - "
                + "embedding now"
            )
            embed_from_local_file = True

    # File missing
    else:
        logger.error(
            "[Thumbnail] Filepath doesn't exist -> cannot embed thumbnail: "
            + f"'{filepath}'"
        )

    # Downloads or embed if requested
    if download_thumbnail or embed_from_local_file:
        if thumbnail_url:
            try:
                success: bool = True
                if download_thumbnail:
                    success = download_and_pad_image(
                        image_url=thumbnail_url,
                        save_path=this_thumbnail_path,
                        thumbnail_format=thumbnail_format,
                    )
                    logger.debug(
                        f"[Thumbnail] Downloaded cover at '{thumbnail_url}'"
                    )
                if success:
                    embed_success: bool = embed_image_in_mp3(
                        mp3_path=filepath,
                        image_path=this_thumbnail_path,
                        test_run=test_run,
                    )
                    if embed_success:
                        update_video_db(
                            video_id,
                            {"update_thumbnail": False},
                            cur,
                            conn,
                            test_run,
                        )
                        if info:
                            fprint(
                                progress_prefix,
                                f"{
                                        'Downloaded & e'
                                        if download_thumbnail
                                        else 'E'
                                    }"
                                + f"mbedded cover for '{title}'",
                            )
                        logger.info(
                            f"[Thumbnail] Embedded cover for '{title}'"
                        )

                else:
                    logger.warning(
                        "[Thumbnail] Failed to download from URL: "
                        + f"'{thumbnail_url}'"
                    )
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error(
                    "[Thumbnail] Exception during thumbnail download/embed: "
                    + f"{e}"
                )
        else:
            logger.warning(
                f"[Thumbnail] No thumbnail URL provided for '{title}'"
            )

    return time.time() - start_processing
