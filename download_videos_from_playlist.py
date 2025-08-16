from main import *

def download_videos_from_playlist(playlist_id = None,loc = None):
    """
    Download all videos in a given playlist to a folder
    """
    if playlist_id == None : playlist_id = input("Music playlist ID: ")
    if loc == None : loc = input("Download location: ")

    youtube = get_authenticated_service()


    playlist_videos_file = JSON_DIR + playlist_id + ".json"
    fetch_playlist_videos(youtube,playlist_id,playlist_videos_file)

    download_playlist(playlist_videos_file,loc,'mp3')


if __name__ == "__main__":
    download_playlist()