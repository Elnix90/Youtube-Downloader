from googleapiclient.errors import HttpError
from CONSTANTS import LIKED_VIDEOS_FILE
from FUNCTIONS.fileops import load,dump
import time
import os

def fetch_liked_videos(youtube):
    print("Fetching liked videos...")
    if not os.path.exists(LIKED_VIDEOS_FILE):
        liked_videos = []
        
        ### Debugging feature ###
        all_request = []
        #########################

        next_page_token = None
        while True:
            try:
                request = youtube.videos().list(
                    part="id",
                    myRating="like",
                    maxResults=50,
                    pageToken=next_page_token
                )
                response = request.execute()
                liked_videos.extend([item['id'] for item in response['items']])

                # Debugging feature ###
                all_request.extend(response)

                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
            except HttpError as e:
                print(f"Error while fetching videos: {e}")
                if "quotaExceeded" in str(e):
                    print("Quota Exceeded, waiting 1 minute before retrying...")
                    time.sleep(60)
                    continue
                else:
                    raise

        dump(liked_videos,LIKED_VIDEOS_FILE)

        # Debugging feature ###
        dump(all_request,"liked_videos_request.json")


    else:
        liked_videos = load(LIKED_VIDEOS_FILE)

    print(f"Found {len(liked_videos)} liked videos")