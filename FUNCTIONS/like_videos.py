from googleapiclient.errors import HttpError
from CONSTANTS import VIDEOS_TO_LIKE_FILE,ERROR_LIKED_FILE
from FUNCTIONS.fileops import load,dump

def like_videos(youtube,):
    videos_to_like = load(VIDEOS_TO_LIKE_FILE)

    error_liked = []
    
    n = len(videos_to_like)
    if n==0:
        print("No videos to like")
        return

    print("Liking videos...")

    for i,video_id in enumerate(videos_to_like):
        try:
            youtube.videos().rate(id=video_id, rating="like").execute()
            print(f"\r{i+1} / {n} liked videos",end="")
 
            # Remove ID from file
            remaining_videos = load(VIDEOS_TO_LIKE_FILE)
            remaining_videos.remove(video_id)
            dump(remaining_videos,VIDEOS_TO_LIKE_FILE)
        
        except HttpError as e:
            print(f"\nError during like: {video_id}: {e}\n")
            error_liked.append(video_id)

    nerrs = len(error_liked)

    if nerrs > 0:
        print(f"{nerrs} videos failed to like -> added to error_liked file")
        dump(error_liked,ERROR_LIKED_FILE)

    print("\n")

