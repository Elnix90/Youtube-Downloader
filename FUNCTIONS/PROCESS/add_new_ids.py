"""
Module to load new video IDs from a JSON file and add or update entries in
the SQLite database. Handles merging playlist info with existing database
entries, optionally adding files not in the playlist, and updating incomplete
database records.
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from sqlite3 import Connection, Cursor

from FUNCTIONS.HELPERS.fileops import handler
from FUNCTIONS.HELPERS.types_playlist import PlaylistVideoEntry
from FUNCTIONS.HELPERS.fprint import fprint
from FUNCTIONS.sql_requests import (
    get_video_info_from_db,
    get_videos_in_list,
    insert_video_db,
    update_video_db,
)
from FUNCTIONS.HELPERS.helpers import (
    VideoInfo,
    VideoInfoMap,
    youtube_required_info
)
from FUNCTIONS.HELPERS.logger import setup_logger

logger = setup_logger(__name__)


def add_new_ids_to_database(
    video_id_file: Path,
    ids_present_in_down_dir: VideoInfoMap,
    add_folder_files_not_in_list: bool,
    include_not_status0: bool,
    test_run: bool,
    info: bool,
    errors: bool,
    cur: Cursor,
    conn: Connection,
) -> None:
    """
    Load video data from a JSON file and add or update entries in the database.

    Args:
        video_id_file: Path to JSON file containing video IDs.
        ids_present_in_down_dir: videoInfoMap already present in download dir.
        add_folder_files_not_in_list: Include files not in playlist when True.
        include_not_status0: Include videos not having status=0 when True.
        test_run: If True, do not commit DB changes.
        info: Print info messages if True.
        errors: Print error messages if True.
        cur: SQLite cursor object.
        conn: SQLite connection object.
    """
    # Fetch current video IDs from DB
    existing_video_ids: list[str] = get_videos_in_list(
        include_not_status0=True, cur=cur
    )

    try:
        playlist_entries: list[PlaylistVideoEntry] = handler.load(
            video_id_file
        )

    except Exception as e:
        logger.error(f"[Adding IDs] Error loading '{video_id_file}': {e}")
        if errors:
            print(f"[Adding IDs] Error loading '{video_id_file}': {e}")
        return

    # Extract video IDs from the playlist
    file_video_ids: list[str] = [entry.video_id for entry in playlist_entries]

    # Determine which videos to add/update
    if add_folder_files_not_in_list:
        to_add = file_video_ids.copy()
        for video_id in existing_video_ids:
            if video_id not in to_add:
                to_add.insert(0, video_id)
    else:
        to_add = [
            vid for vid in file_video_ids if vid not in existing_video_ids
        ]

    correct_ids = added_ids = updated_ids = 0

    for video_id in to_add:
        try:
            # Fetch info from download directory
            video_data = ids_present_in_down_dir.get(video_id, {})
            status: int = video_data.get("status", 3)

            # Find matching playlist entry
            entry = next(
                (e for e in playlist_entries if e.video_id == video_id), None
            )

            if entry:
                # Merge JSON dataclass info
                entry_dict = asdict(entry)
                for key in entry_dict:
                    if key in VideoInfo.__annotations__:
                        video_data[key] = entry_dict[key]

                logger.debug(
                    f"[Merge] Updated video_data for {video_id} from playlist"
                )

            # Insert new video
            if video_id not in existing_video_ids:
                if include_not_status0 or status != 3:
                    video_data["video_id"] = video_id
                    insert_video_db(video_data, cur, conn, test_run)
                    added_ids += 1
            else:
                # Update incomplete DB info
                db_data = get_video_info_from_db(video_id=video_id, cur=cur)
                if not all(
                    key in db_data and db_data[key] is not None
                    for key in youtube_required_info
                ):
                    if all(
                        key in video_data and video_data[key] is not None
                        for key in youtube_required_info
                    ):
                        update_video_db(
                            video_id,
                            video_data,
                            cur,
                            conn,
                            test_run
                        )
                        updated_ids += 1
                else:
                    correct_ids += 1

            # Print progress
            if info:
                fprint(
                    "",
                    f"[Adding IDs] Added {added_ids} | " +
                    f"Updated {updated_ids} | {correct_ids} OK",
                )

        except Exception as e:
            logger.error(f"[Adding IDs] Failed for '{video_id}': {e}")
            if errors:
                print(f"[Adding IDs] Failed for '{video_id}': {e}")

    if not test_run:
        conn.commit()

    summary = (
        f"[Adding IDs] Added {added_ids}," +
        "Updated {updated_ids}, {correct_ids} already OK"
    )
    logger.info(summary)
    if info:
        print(summary)
