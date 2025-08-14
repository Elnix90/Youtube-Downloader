from googleapiclient.errors import HttpError
from CONSTANTS import PRIVATE_VIDEOS_FILE
from FUNCTIONS.fileops import load, dump
import os
from pathlib import Path
def remove_private_videos(youtube, playlist_id="LL"):

    if Path(PRIVATE_VIDEOS_FILE).exists():
        private_videos = load(PRIVATE_VIDEOS_FILE) or []
    else: return

    removed_count = 0
    next_page_token = None

    if len(private_videos) > 0:
        while True:
            request = youtube.playlistItems().list(
                part="id,snippet",
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()
            items = response.get("items", [])

            for item in items:
                video_id = item["snippet"]["resourceId"]["videoId"]
                if video_id in private_videos:
                    try:
                        youtube.playlistItems().delete(id=item["id"]).execute()
                        removed_count += 1
                        print(f"\r{removed_count} videos removed", end="", flush=True)

                        # Update local private_videos list
                        private_videos.remove(video_id)
                        dump(private_videos, PRIVATE_VIDEOS_FILE)

                    except HttpError as e:
                        print(f"\nError removing video {video_id}: {e}")

            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break

        print(f"\rFinished removing videos. {removed_count} removed.")

    if len(private_videos) == 0:
        os.remove(PRIVATE_VIDEOS_FILE)
