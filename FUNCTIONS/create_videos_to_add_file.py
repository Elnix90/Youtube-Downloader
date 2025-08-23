from CONSTANTS import LIKED_VIDEOS_FILE,PLAYLIST_VIDEOS_FILE,VIDEOS_TO_ADD_IN_PLAYLIST_FILE,UNAVAILABLE_VIDEOS_FILE
from FUNCTIONS.fileops import load,dump
from pathlib import Path

def create_videos_to_add_files():

    if not Path(VIDEOS_TO_ADD_IN_PLAYLIST_FILE).exists():
        liked_videos = load(LIKED_VIDEOS_FILE)
        playlist_videos = load(PLAYLIST_VIDEOS_FILE)

        videos_to_add_in_playist = list(set(liked_videos) - set(playlist_videos))
        if Path(UNAVAILABLE_VIDEOS_FILE).exists():
            private_videos = load(UNAVAILABLE_VIDEOS_FILE)
            for video in private_videos:
                if video in videos_to_add_in_playist:
                    videos_to_add_in_playist.remove(video)

        if len(videos_to_add_in_playist) > 0:
            print(f"{len(videos_to_add_in_playist)} videos have to be added.")
        else:print("All liked videos are in the playlist")

        dump(videos_to_add_in_playist,VIDEOS_TO_ADD_IN_PLAYLIST_FILE)
