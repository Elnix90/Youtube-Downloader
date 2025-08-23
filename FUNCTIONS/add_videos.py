from typing import Any, List
from googleapiclient.errors import HttpError  # type: ignore
from CONSTANTS import ERROR_ADDED_FILE, UNAVAILABLE_VIDEOS_FILE
from FUNCTIONS.fileops import load, dump
from pathlib import Path

def add_videos(
    youtube: Any,
    playlist_id: str,
    file: Path
) -> None:
    if not file.exists():
        print(f"File: {file} doesn't exist")
        return

    videos_to_add: List[str] = load(file)
    error_added: List[str] = []

    if Path(UNAVAILABLE_VIDEOS_FILE).exists():
        unavailable_videos: List[str] = load(UNAVAILABLE_VIDEOS_FILE)
    else:
        unavailable_videos: List[str] = []

    n: int = len(videos_to_add)
    if n == 0:
        print("No videos to add")
        return

    print("Adding videos...")

    for i, video_id in enumerate(videos_to_add):
        try:
            youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": video_id
                        }
                    }
                }
            ).execute()

            print(f"\r{i+1} / {n} videos added", end="")

        except HttpError as e:
            error_json: str = e.content.decode() if hasattr(e, 'content') else str(e)
            if 'failedPrecondition' in error_json:
                print(f"\nVideo {video_id} is likely private or unavailable, skipping...")
                unavailable_videos.append(video_id)
                dump(unavailable_videos, UNAVAILABLE_VIDEOS_FILE)
            else:
                print(f"\nError adding {video_id} to playlist: {e}")
                error_added.append(video_id)
                dump(error_added, Path(ERROR_ADDED_FILE))

        videos_added: List[str] = load(file)
        if video_id in videos_added:
            videos_added.remove(video_id)
        dump(videos_added, file)

    nerrs: int = len(error_added)
    if nerrs > 0:
        print(f"\n{nerrs} videos failed to add -> added to error_added file")
    else:
        print()
