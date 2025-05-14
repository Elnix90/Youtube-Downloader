from CONSTANTS import LIKED_VIDEOS_FILE,PLAYLIST_VIDEOS_FILE,VIDEOS_TO_LIKE_FILE,VIDEOS_TO_ADD_IN_PLAYLIST_FILE
from FUNCTIONS.fileops import load,dump

def create_videos_to_like_and_add_files():
    # Load liked videos and playlist videos from file
    liked_videos = load(LIKED_VIDEOS_FILE)
    playlist_videos = load(PLAYLIST_VIDEOS_FILE)

    
    # Initialize lists of videos to like and add in playlist
    videos_to_like =[]
    videos_to_add_in_playist = []

    # If there is need to like or add videos (the work isn't already done)
    if sorted(liked_videos) != sorted(playlist_videos):

        videos_to_add_in_playist = list(set(liked_videos) - set(playlist_videos))
        videos_to_like = list(set(playlist_videos) - set(liked_videos))

        if len(videos_to_like)>0:
            print(f"{len(videos_to_like)} videos have to be liked.")
        else:print("All videos are liked")

        if len(videos_to_add_in_playist)>0:
            print(f"{len(videos_to_add_in_playist)} videos have to be added.")
        else:print("All liked videos are in the playlist")


    else:print("Liked videos and playlist videos are already the same")
    
    dump(videos_to_add_in_playist,VIDEOS_TO_ADD_IN_PLAYLIST_FILE)
    dump(videos_to_like,VIDEOS_TO_LIKE_FILE)