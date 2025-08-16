from FUNCTIONS.get_creditentials import get_authenticated_service
from FUNCTIONS.get_playlist_videos import fetch_playlist_videos
from FUNCTIONS.create_videos_to_add_file import create_videos_to_add_files
from FUNCTIONS.add_videos import add_videos
from FUNCTIONS.create_videos_to_download_file import create_videos_to_download
from FUNCTIONS.download import download_playlist
from FUNCTIONS.final_verification import final_verification
from FUNCTIONS.remove_private_videos import remove_private_videos
from CONSTANTS import *
from FUNCTIONS.fileops import *

import shutil

def process_new_liked_videos(playlist_id=None,path=None,format=None,get_lyrics=True,add_album=True):
    """
    Fetches all of you liked videos and the videos in a playlist of your choice and fill the playlist with your liked videos,
    then downloads every liked video with lyrics
    """

    if playlist_id == None : playlist_id = input("Music playlist ID: ")
    if path == None : path = input("Path to download: ")
    if format == None : format = input("Format('mp3' or 'wav'): ")

    JSON_DIR.mkdir(exist_ok=True)
    CRED_DIR.mkdir(exist_ok=True)
    Path(path).mkdir(exist_ok=True)

    youtube = get_authenticated_service()

    fetch_playlist_videos(youtube,playlist_id,PLAYLIST_VIDEOS_FILE)
    fetch_playlist_videos(youtube,"LL",LIKED_VIDEOS_FILE)

    create_videos_to_add_files()
    add_videos(youtube,playlist_id,VIDEOS_TO_ADD_IN_PLAYLIST_FILE)

    create_videos_to_download(path)
    download_playlist(VIDEOS_TO_DOWNLOAD_FILE,path,format,get_lyrics,add_album)

    remove_private_videos(youtube)

    final_verification(path)
    print("\n\n\nDownloading programm ended successfully!!\n\n\n")

    shutil.rmtree(JSON_DIR)


if __name__ == '__main__':
    process_new_liked_videos()