from typing import Any, List, Optional
from googleapiclient.errors import HttpError  # type: ignore
from CONSTANTS import UNAVAILABLE_VIDEOS_FILE
from FUNCTIONS.fileops import load, dump
import os
from pathlib import Path

def remove_private_videos(youtube: Any, playlist_id: str = "LL") -> None:
    unavailable_path = Path(UNAVAILABLE_VIDEOS_FILE)
    if not unavailable_path.exists():
        return

    private_videos: List[str] = load(unavailable_path)
    if not private_videos:
        return

    removed_count: int = 0
    next_page_token: Optional[str] = None

    while True:
        try:
            request = youtube.playlistItems().list(
                part="id,snippet",
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )
            response: dict[str, Any] = request.execute()
        except HttpError as e:
            print(f"\nError fetching playlist items: {e}")
            break

        items: List[Any] = response.get("items", [])
        for item in items:
            video_id: str = item.get("snippet", {}).get("resourceId", {}).get("videoId", "")
            if video_id and video_id in private_videos:
                try:
                    youtube.playlistItems().delete(id=item.get("id")).execute()
                    removed_count += 1
                    print(f"\r{removed_count} videos removed", end="", flush=True)
                    private_videos.remove(video_id)
                    dump(private_videos, unavailable_path)
                except HttpError as e:
                    print(f"\nError removing video {video_id}: {e}")

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    print(f"\rFinished removing videos. {removed_count} removed.")

    if not private_videos and unavailable_path.exists():
        os.remove(unavailable_path)
