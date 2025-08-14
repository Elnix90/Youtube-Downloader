from googleapiclient.errors import HttpError
from pathlib import Path
from FUNCTIONS.fileops import load, dump


def fetch_playlist_videos(youtube, playlist_id,file,clean=False):
    print(f"Fetching videos from playlist {playlist_id}")

    if clean or (not Path(file).exists()):

        all_videos = []
        next_page_token = None

        while True:
            try:
                request = youtube.playlistItems().list(
                    part="contentDetails",
                    playlistId=playlist_id,
                    maxResults=50,
                    pageToken=next_page_token
                )
                response = request.execute()

                for item in response['items']:
                    vid_id = item['contentDetails']['videoId']
                    all_videos.append(vid_id)
                    print(f"\r{len(all_videos)} videos found in playlist : {playlist_id}",end="",flush=True)

                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break

            except HttpError as e:
                print(f"Error while fetching playlist videos: {e}")
                if "quotaExceeded" in str(e):
                    raise Exception("Quota exceeded, please change your token or retry in 24h")
                else:
                    raise

        dump(all_videos, file)
        print()
        return all_videos
    
    else:
        return load(file)
