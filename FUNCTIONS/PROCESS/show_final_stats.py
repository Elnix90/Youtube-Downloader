from typing import Any


from pathlib import Path
from sqlite3 import Cursor
from FUNCTIONS.extract_and_clean import extract_and_clean_video_ids
from FUNCTIONS.helpers import VideoInfoMap

from logger import setup_logger
logger = setup_logger(__name__)





def show_final_stats(
    download_path: Path,
    entire_duration: str | None,
    calculating_duration: str | None,
    download_duration: str | None,
    cut_duration: str | None,
    lyrics_duration: str | None,
    thumbnail_duration: str | None,
    tag_duration: str | None,
    album_suration: str | None,
    metadata_duration: str | None,
    cur: Cursor,
    test_run: bool,
    remove_malformatted: bool
) -> None:
    """
    Show infos from the process, how much videos are correctly formatted and downloaded, and how much aren't
    """

    ids_present_in_down_dir: VideoInfoMap = extract_and_clean_video_ids(download_path,info=False, test_run=test_run, remove=remove_malformatted)

    list_without_unavailable: VideoInfoMap = {}

    _ = cur.execute("SELECT video_id, status FROM videos")
    infos: set[tuple[Any, Any]]  = {(row["video_id"],row["status"]) for row in cur.fetchall()}  # pyright: ignore[reportAny, reportExplicitAny]

    for video_id, status in infos:  # pyright: ignore[reportAny]
        if status == 0:
            list_without_unavailable[video_id] = {}


    not_in_dir: set[str] = set(list_without_unavailable.keys()) - set(ids_present_in_down_dir.keys())
    not_in_list: set[str] = set(ids_present_in_down_dir.keys()) - set(list_without_unavailable.keys())

    final_stats: list[str] = []


    if not not_in_dir and not not_in_list:
        final_stats.append(" ✅ The database and the download dir have been sucessfully synchronized")
    else:
        if not not_in_dir:
            final_stats.append(f" - {len(list_without_unavailable)} ids are in the database and correctly downloaded")
        else:
            final_stats.append(f" - {len(infos) - len(list_without_unavailable)} ids have not been downloaded, marked as unavailable")

        if not not_in_list:
            final_stats.append(f" - All downloaded files are in the database and corectly formated")
        else:
            final_stats.append(f" - {len(not_in_list)} correctly formatted files are in the download directory but not in the database (pass add_folder_files_not_in_list = True to add them to the database)")


    print(f"\n[TOTAL]:\n - {len(infos)} total videos are in the database {'(contains privates and unavailable)' if len(list_without_unavailable) < len(infos) else ""}\n - {len(ids_present_in_down_dir)} total videos are in download directory")
    print("\n".join(final_stats))


    print(f"[TOTAL TIME] : {entire_duration}")

    if calculating_duration is not None:
        print(f" - Total calculating time: {calculating_duration}")
    if download_duration is not None:
        print(f" - Total download time: {download_duration}")
    if cut_duration is not None:
        print(f" - Total segment cutting time: {cut_duration}")
    if lyrics_duration is not None:
        print(f" - Total lyrics processing time: {lyrics_duration}")
    if thumbnail_duration is not None:
        print(f" - Total thumbnails processing time: {thumbnail_duration}")
    if tag_duration is not None:
        print(f" - Total tags processing time: {tag_duration}")
    if album_suration is not None:
        print(f" - Total album processing time: {album_suration}")
    if metadata_duration is not None:
        print(f" - Total metadata processing time: {metadata_duration}")