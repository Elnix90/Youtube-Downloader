from googleapiclient.errors import HttpError
from CONSTANTS import ERROR_ADDED_FILE,UNAVAILABLE_VIDEOS_FILE
from FUNCTIONS.fileops import load,dump
import os
from pathlib import Path

def add_videos(youtube,playlist_id,file):

    if Path(file).exists():
        videos_to_add = load(file)
    else:
        print(f"File: {file} doesen't exists")
        return
    
    error_added = []

    if Path(UNAVAILABLE_VIDEOS_FILE).exists():
        private_videos = load(UNAVAILABLE_VIDEOS_FILE)
    else: private_videos = []
    
    n = len(videos_to_add)
    if n==0:
        print("No videos to add")
        return

    print("Adding videos...")

    for i,video_id in enumerate(videos_to_add):
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

            print(f"\r{i+1} / {n} videos added",end="")

        except HttpError as e:
            error_json = e.content.decode() if hasattr(e, 'content') else str(e)
            if 'failedPrecondition' in error_json:
                print(f"\nVideo {video_id} is likely private or unavailable, skipping...")
                private_videos.append(video_id)
                dump(private_videos, UNAVAILABLE_VIDEOS_FILE)
            else:
                print(f"\nError adding {video_id} to playlist: {e}")
                error_added.append(video_id)
                dump(error_added, ERROR_ADDED_FILE)

        videos_added = load(file)
        videos_added.remove(video_id)
        dump(videos_added,file)

    nerrs = len(error_added)
    if nerrs > 0:
        print(f"\n{nerrs} videos failed to add -> added to error_added file")
    else:
        print()
