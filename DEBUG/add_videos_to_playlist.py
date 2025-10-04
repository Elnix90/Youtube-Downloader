import time
from pathlib import Path

from googleapiclient.errors import HttpError

from CONSTANTS import JSON_DIR
from FUNCTIONS.get_creditentials import get_authenticated_service
from FUNCTIONS.get_playlist_videos import fetch_playlist_videos
from FUNCTIONS.HELPERS.fileops import handler
from FUNCTIONS.HELPERS.fprint import fprint
from FUNCTIONS.HELPERS.logger import setup_logger

logger = setup_logger(__name__)


def add_videos(
    playlist_id: str, clean: bool, test_run: bool, info: bool, error: bool
):

    liked_video_file = Path(
        JSON_DIR / f"liked_videos_{round(time.time(),2)}.json"
    )
    playlist_video_file = Path(JSON_DIR / f"videos_{playlist_id}.json")

    if clean or not (
        playlist_video_file.exists() and liked_video_file.exists()
    ):
        fetch_playlist_videos(
            playlist_id=playlist_id,
            file=playlist_video_file,
            test_run=test_run,
            clean=clean,
            info=info,
            error=error,
        )

        fetch_playlist_videos(
            playlist_id="LL",
            file=liked_video_file,
            test_run=test_run,
            clean=clean,
            info=info,
            error=error,
        )

    playlist_items = handler.load(playlist_video_file)
    playlist_videos = set(
        entry.video_id for entry in playlist_items if entry.video_id
    )

    liked_items = handler.load(liked_video_file)
    liked_videos = set(
        entry.video_id for entry in liked_items if entry.video_id
    )

    videos_to_add = liked_videos - playlist_videos

    n = len(videos_to_add)
    if n == 0:
        logger.info("[Adding videos] No videos to add")
        if info:
            print("[Adding videos] No videos to add")
        return

    youtube = get_authenticated_service(info)

    logger.info("[Adding videos] Adding videos...")
    if info:
        print("[Adding videos] Adding videos...")

    for i, video_id in enumerate(videos_to_add):

        progress_prefix = f"{i+1:{len(str(n))}d}/{n} | "

        try:
            youtube.playlistItems().insert(  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": video_id,
                        },
                    }
                },
            ).execute()

            logger.info(
                "f{progress_prefix} video {video_id} added to {playlist_id}"
            )
            if info:
                fprint(
                    progress_prefix, f"video {video_id} added to {playlist_id}"
                )

        except HttpError as e:
            error_json = (
                e.content.decode() if hasattr(e, 'content') else str(e)
            )  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue, reportUnknownVariableType]
            if 'failedPrecondition' in error_json:
                logger.warning(
                    f"Video {video_id} is likely private or unavailable, skipping..."
                )
                if error:
                    print(
                        f"\nVideo {video_id} is likely private or unavailable, skipping..."
                    )
            else:
                logger.error(f"Error adding {video_id} to playlist: {e}")
                print(f"\nError adding {video_id} to playlist: {e}")
