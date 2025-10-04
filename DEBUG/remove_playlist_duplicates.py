from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from CONSTANTS import PLAYLIST_VIDEOS_FILE
from FUNCTIONS.get_creditentials import get_authenticated_service
from FUNCTIONS.get_playlist_videos import fetch_playlist_videos
from FUNCTIONS.HELPERS.fileops import handler
from FUNCTIONS.HELPERS.fprint import fprint
from FUNCTIONS.HELPERS.logger import setup_logger
from FUNCTIONS.HELPERS.types_playlist import PlaylistVideoEntry

logger = setup_logger(__name__)


def remove_duplicate_videos_from_playlist(
    playlist_id: str,
    test_run: bool = False,
    clean: bool = False,
    info: bool = True,
    error: bool = True,
) -> None:
    """Remove duplicate videos from a YouTube playlist."""

    playlist_video_file = PLAYLIST_VIDEOS_FILE

    # 1. Ensure we have up-to-date playlist data
    fetch_playlist_videos(
        playlist_id=playlist_id,
        file=playlist_video_file,
        test_run=test_run,
        clean=clean,
        info=info,
        error=error,
    )

    # 2. Load playlist entries with the typed JSONFileHandler
    playlist_entries: list[PlaylistVideoEntry] = handler.load(
        playlist_video_file
    )

    # 3. Build mapping video_id -> list[item_id]
    video_id_to_items: dict[str, list[str]] = {}
    for entry in playlist_entries:
        video_id = entry.video_id
        item_id = entry.playlist_item_id
        if video_id and item_id:  # skip entries missing essential data
            video_id_to_items.setdefault(video_id, []).append(item_id)

    # 4. Detect duplicates (more than one item_id per video_id)
    duplicates: dict[str, list[str]] = {
        vid: ids for vid, ids in video_id_to_items.items() if len(ids) > 1
    }

    if not duplicates:
        msg = "[Remove Duplicates] No duplicate videos found in playlist"
        logger.info(msg)
        if info:
            print(msg)
        return

    # 5. Authenticate and prepare deletion
    youtube: Resource = get_authenticated_service(info)
    logger.info(
        "[Remove Duplicates] Removing duplicate videos from playlist..."
    )
    if info:
        print("[Remove Duplicates] Removing duplicate videos from playlist...")

    removed_count = 0
    total_duplicates = sum(len(ids) - 1 for ids in duplicates.values())
    progress_counter = 1

    for video_id, item_ids in duplicates.items():
        # Skip the first item, keep it in the playlist
        for idx, item_id in enumerate(item_ids[1:], start=2):
            if not item_id:
                logger.warning(
                    f"Cannot remove duplicate: missing item_id for video {video_id}"
                )
                continue

            progress_prefix = f"{progress_counter}/{total_duplicates} | "
            try:
                if test_run:
                    msg = f"[Test Run] Would remove duplicate {idx} of video {video_id} (item_id={item_id})"
                    logger.info(msg)
                    if info:
                        print(progress_prefix + msg)
                    progress_counter += 1
                    continue

                # Perform actual deletion
                youtube.playlistItems().delete(
                    id=item_id
                ).execute()  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
                removed_count += 1
                msg = f"Removed duplicate {idx} of video {video_id}: item_id={item_id}"
                logger.info(msg)
                if info:
                    fprint(progress_prefix, msg)
                progress_counter += 1

            except HttpError as e:
                msg = f"Error removing duplicate {idx} of {video_id}: {e}"
                logger.error(msg)
                if error:
                    print(msg)

    logger.info(
        f"[Remove Duplicates] Removed {removed_count} duplicate videos from playlist"
    )
    if info:
        print(
            f"[Remove Duplicates] Removed {removed_count} duplicate videos from playlist"
        )
