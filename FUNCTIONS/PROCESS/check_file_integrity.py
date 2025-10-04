"""
Module to check every file in the download dir and verfy his
health state.
Removes every file that aren't mp3, or lrc or png if
not attached to a mp3 if asked
"""

import time
from pathlib import Path
from sqlite3 import Connection, Cursor
from typing import Literal

from FUNCTIONS.HELPERS.helpers import (
    VideoInfo,
    VideoInfoMap,
    youtube_required_info,
)
from FUNCTIONS.HELPERS.logger import setup_logger
from FUNCTIONS.metadata import repair_mp3_file
from FUNCTIONS.sql_requests import get_video_info_from_db, update_video_db

logger = setup_logger(__name__)


def check_file_integrity_for_video(
    video_id: str,
    download_path: Path,
    ids_present_in_down_dir: VideoInfoMap,
    retry_unavailable: bool,
    retry_private: bool,
    cur: Cursor,
    conn: Connection,
    test_run: bool,
) -> tuple[bool, float]:
    """
    Check integrity for a single video_id.
    Returns True if the video needs to be downloaded, False otherwise.
    """
    start_processing: float = time.time()

    logger.verbose(f"Checking file integrity for {video_id}")

    video_data = get_video_info_from_db(video_id=video_id, cur=cur)

    # --- Case: video exists in download dir ---
    if video_id in ids_present_in_down_dir.keys():
        metadata: VideoInfo = ids_present_in_down_dir.get(video_id, {})
        # print(metadata)
        filename: str = video_data.get(
            "filename", metadata.get("filename", "")
        )
        # print(filename)
        filepath: Path | None = download_path / filename if filename else None
        # print(filepath)

        if not filepath or not filepath.exists():
            # logger.warning(filepath)
            logger.debug(
                "[File Checking] Missing filename or file not found"
                + f"for '{video_id}'"
            )
            return True, time.time() - start_processing

        title: str = metadata.get("title", "")

        # Merge DB data with extracted metadata
        fusion: VideoInfo = metadata | video_data

        if all(
            key in fusion and fusion[key] is not None
            for key in youtube_required_info
        ):
            if repair_mp3_file(filepath, test_run):
                fusion["status"] = 0  # downloaded
                update_video_db(video_id, fusion, cur, conn, test_run)
                logger.debug(
                    f"[File Checking] File valid and repaired: '{title}'"
                )
                return False, time.time() - start_processing
            logger.warning(
                f"[File Checking] Corrupted file, re-downloading: '{title}'"
            )
            return True, time.time() - start_processing
        else:
            missings: set[str] = set(youtube_required_info) - set(
                fusion.keys()
            )

            logger.warning(
                f"[File Checking] Metadata incomplete missing {missings} keys, re-downloading: '{title}'"
            )
            return True, time.time() - start_processing

    # --- Case: video not present in download dir ---
    status: Literal[0, 1, 2, 3] = video_data.get("status", 3)
    if status == 1 and not retry_unavailable:
        logger.info(f"[File Checking] Video {video_id} unavailable, skipping")
        return False, time.time() - start_processing
    elif status == 2 and not retry_private:
        logger.info(f"[File Checking] Video {video_id} private, skipping")
        return False, time.time() - start_processing
    else:
        update_video_db(
            video_id,
            {
                "status": 3,
                "removed_segments_int": 0,
                "removed_segments_duration": 0.0,
            },
            cur,
            conn,
            test_run,
        )
        logger.info(
            f"[File Checking] Missing in download dir, will be downloaded: {video_id}"
        )
        return True, time.time() - start_processing
