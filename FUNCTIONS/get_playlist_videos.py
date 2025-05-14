from googleapiclient.errors import HttpError
from CONSTANTS import PLAYLIST_VIDEOS_FILE
from FUNCTIONS.fileops import load,dump
import time
import os

def fetch_playlist_videos(youtube,playlist_id):
    print("Fetching playlist videos...")
    if not os.path.exists(PLAYLIST_VIDEOS_FILE):
        playlist_videos = []
        next_page_token = None
        while True:
            try:
                request = youtube.playlistItems().list(
                    part="snippet",
                    playlistId=playlist_id,
                    maxResults=50,
                    pageToken=next_page_token
                )
                response = request.execute()
                playlist_videos.extend([item['snippet']['resourceId']['videoId'] for item in response['items']])
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
            except HttpError as e:
                print(f"Une erreur est survenue lors de la récupération des vidéos de la playlist : {e}")
                if "quotaExceeded" in str(e):
                    print("Quota dépassé. Attente de 1 minute avant de réessayer...")
                    time.sleep(60)
                    continue
                else:
                    raise

        dump(playlist_videos,PLAYLIST_VIDEOS_FILE)
    else:
        playlist_videos = load(PLAYLIST_VIDEOS_FILE)

    print(f"Found {len(playlist_videos)} videos in the playlist")