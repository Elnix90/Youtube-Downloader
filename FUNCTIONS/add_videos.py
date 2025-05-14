from googleapiclient.errors import HttpError
from CONSTANTS import VIDEOS_TO_ADD_IN_PLAYLIST_FILE,ERROR_ADDED_FILE,PLAYLIST_VIDEOS_FILE
from FUNCTIONS.fileops import load,dump
import os

def add_videos(youtube,playlist_id):

    videos_to_add = load(VIDEOS_TO_ADD_IN_PLAYLIST_FILE)
    error_added = []
    
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

            videos_added = load(VIDEOS_TO_ADD_IN_PLAYLIST_FILE)
            videos_added.remove(video_id)
            dump(videos_added,VIDEOS_TO_ADD_IN_PLAYLIST_FILE)

        except HttpError as e:
            print(f"\nError adding {video_id} to playlist : {e}")
            error_added.append(video_id)

    nerrs = len(error_added)
    if nerrs > 0:
        print(f"{nerrs} videos failed to add -> added to error_added file")
        dump(error_added,ERROR_ADDED_FILE)

    print("\n")

    os.remove(PLAYLIST_VIDEOS_FILE)