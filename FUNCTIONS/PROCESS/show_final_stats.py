from typing import Literal, cast

from pathlib import Path
from sqlite3 import Cursor
from CONSTANTS import CORRECT_NOT_IN_DIR_FILE, UNAVAILABLE_VIDEOS_FILE
from FUNCTIONS.extract_and_clean import extract_and_clean_video_ids
from FUNCTIONS.HELPERS.fileops import handler
from FUNCTIONS.HELPERS.helpers import VideoInfoMap

from FUNCTIONS.HELPERS.logger import setup_logger
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
    album_duration: str | None,
    metadata_duration: str | None,
    cur: Cursor,
    test_run: bool,
    remove_malformatted: bool,
    force_mp3_presence: bool
) -> None:
    """
    Show information about the processed videos: correctly formatted, downloaded,
    and discrepancies between database and download directory.
    """

    # Extract video infos from the download directory
    ids_present_in_down_dir: VideoInfoMap = extract_and_clean_video_ids(
        download_directory=download_path,
        info=False,
        test_run=test_run,
        remove=remove_malformatted,
        force_mp3_presence=force_mp3_presence
    )

    # Prepare a mapping of video_id -> empty VideoInfo for all downloaded videos in DB
    list_without_unavailable: VideoInfoMap = {}

    _= cur.execute("SELECT video_id, status FROM videos")
    infos: set[tuple[str, Literal[0, 1, 2, 3]]] = {
        (row["video_id"], cast(Literal[0, 1, 2, 3], row["status"])) for row in cur.fetchall()  # pyright: ignore[reportAny]
    }

    # Keep only videos with status 0 (downloaded)
    for video_id, status in infos:
        if status == 0:
            list_without_unavailable[video_id] = {}  # type: ignore

    # Compute differences
    not_in_dir: set[str] = set(list_without_unavailable.keys()) - set(ids_present_in_down_dir.keys())
    not_in_list: set[str] = set(ids_present_in_down_dir.keys()) - set(list_without_unavailable.keys())

    final_stats: list[str] = []

    if not not_in_dir and not not_in_list:
        final_stats.append(" ✅ The database and the download dir have been successfully synchronized")
    else:
        if not not_in_dir:
            final_stats.append(f" - {len(list_without_unavailable)} ids are in the database and correctly downloaded")
        else:
            final_stats.append(f" - {len(infos) - len(not_in_dir)} ids have not been downloaded, marked as unavailable")
            if len(not_in_dir) < 10:
                for vid in not_in_dir:
                    final_stats.append(f"   • {vid}")
                final_stats.append("")
            else:
                handler.dump(data=list(not_in_dir), file=UNAVAILABLE_VIDEOS_FILE)  # pyright: ignore[reportArgumentType]
                final_stats.append(f"   • List written in {UNAVAILABLE_VIDEOS_FILE}")

        if not not_in_list:
            final_stats.append(f" - All downloaded files are in the database and correctly formatted")
        else:
            final_stats.append(
                f" - {len(not_in_list)} correctly formatted files are in the download directory but not in the database (pass add_folder_files_not_in_list = True to add them to the database)"
            )
            if len(not_in_list) < 10:
                for vid in not_in_list:
                    final_stats.append(f"   • {vid}")
                final_stats.append("\n")
            else:
                handler.dump(data=list(not_in_list), file=CORRECT_NOT_IN_DIR_FILE)  # pyright: ignore[reportArgumentType]
                final_stats.append(f"   • List written in {CORRECT_NOT_IN_DIR_FILE}")

    # Print summary
    print(f"\n[TOTAL]:\n - {len(infos)} total videos in the database "+
        f"{'(contains privates and unavailable)' if len(list_without_unavailable) < len(infos) else ''}\n"+
        f" - {len(ids_present_in_down_dir)} total videos in download directory")
    print("\n".join(final_stats))

    # Print durations
    print(f"[TOTAL TIME] : {entire_duration}")
    if calculating_duration:
        print(f" - Total calculating time: {calculating_duration}")
    if download_duration:
        print(f" - Total download time: {download_duration}")
    if cut_duration:
        print(f" - Total segment cutting time: {cut_duration}")
    if lyrics_duration:
        print(f" - Total lyrics processing time: {lyrics_duration}")
    if thumbnail_duration:
        print(f" - Total thumbnails processing time: {thumbnail_duration}")
    if tag_duration:
        print(f" - Total tags processing time: {tag_duration}")
    if album_duration:
        print(f" - Total album processing time: {album_duration}")
    if metadata_duration:
        print(f" - Total metadata processing time: {metadata_duration}")
