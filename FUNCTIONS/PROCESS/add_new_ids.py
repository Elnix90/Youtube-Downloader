from __future__ import annotations

from pathlib import Path
from sqlite3 import Connection, Cursor

from FUNCTIONS.HELPERS.fileops import load
from FUNCTIONS.HELPERS.fprint import fprint
from FUNCTIONS.HELPERS.helpers import VideoInfo, VideoInfoMap, youtube_required_info
from FUNCTIONS.HELPERS.logger import setup_logger
from FUNCTIONS.sql_requests import (
    get_video_info_from_db,
    get_videos_in_db,
    insert_video_db,
    update_video_db,
)

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
    """

    try:
        playlist_entries = load(video_id_file)
    except Exception as e:  # pylint: disable=broad-exception-caught
        msg = f"[Adding IDs] Error loading '{video_id_file}': {e}"
        logger.error(msg)
        if errors:
            print(msg)
        return

    existing_video_ids = get_videos_in_db(include_not_status0=True, cur=cur)
    file_video_ids = list(playlist_entries.keys())

    # Determine which video IDs to process
    if add_folder_files_not_in_list:
        print("adding files")
        to_add = file_video_ids.copy()
        for vid in existing_video_ids:
            if vid not in to_add:
                to_add.insert(0, vid)
    else:
        to_add = [vid for vid in file_video_ids if vid not in existing_video_ids]

    print(
        "ids_presents size:", len(ids_present_in_down_dir),
        "\nplaylist_entries size:", len(playlist_entries),
        "\nexisting size:", len(existing_video_ids),
        "\nto_add size:", len(to_add)
    )

    added_ids = updated_ids = correct_ids = 0

    for video_id in to_add:
        try:
            # Video data from local directory (downloaded files)
            video_data = ids_present_in_down_dir.get(video_id, {})
            status = video_data.get("status", 3)

            # Playlist info from the JSON file (fresh metadata)
            playlist_info: VideoInfo | None = playlist_entries.get(video_id)

            # Merge if both exist
            if playlist_info:
                for key, value in playlist_info.items():
                    if key in VideoInfo.__annotations__ and value is not None:
                        video_data[key] = value
                logger.debug(f"[Merge] Merged playlist info into {video_id}")

            # Insert new entry if not already in DB
            if video_id not in existing_video_ids:
                if include_not_status0 or status != 3:
                    video_data["video_id"] = video_id
                    insert_video_db(video_data, cur, conn, test_run)
                    added_ids += 1
            else:
                # Possibly update existing DB entry if missing info
                db_data = get_video_info_from_db(video_id=video_id, cur=cur)
                db_missing_fields = [k for k in youtube_required_info if not db_data.get(k)]

                if db_missing_fields:
                    has_enough_data = all(
                        key in video_data and video_data[key] is not None for key in youtube_required_info
                    )
                    if has_enough_data:
                        update_video_db(video_id, video_data, cur, conn, test_run)
                        updated_ids += 1
                else:
                    correct_ids += 1

            # Progress display
            if info:
                fprint(
                    "",
                    f"[Adding IDs] Added {added_ids} | Updated {updated_ids} | {correct_ids} already OK",
                )

        except Exception as e:  # pylint: disable=broad-exception-caught
            msg = f"[Adding IDs] Failed for '{video_id}': {e}"
            logger.error(msg)
            if errors:
                print(msg)

    if not test_run:
        conn.commit()

    summary = f"[Adding IDs] Added {added_ids} | " + f"Updated {updated_ids} | " + f"{correct_ids} already OK"
    logger.info(summary)
    if info:
        print(summary)
