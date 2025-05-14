from FUNCTIONS.get_creditentials import get_authenticated_service
from FUNCTIONS.get_liked_videos import fetch_liked_videos
from FUNCTIONS.get_playlist_videos import fetch_playlist_videos
from FUNCTIONS.create_videos_to_like_and_add_file import create_videos_to_like_and_add_files
from FUNCTIONS.like_videos import like_videos
from FUNCTIONS.add_videos import add_videos
from FUNCTIONS.create_videos_to_download_file import create_videos_to_download
from FUNCTIONS.download import download_playlist
# from FUNCTIONS.intelligent_deleting import inteligent_deleting
from FUNCTIONS.final_verification import final_verification

from CONSTANTS import *

import os


def process_new_liked_videos(clean=True,playlist_id=None,path=None,finalpath=None,format=None):
    if playlist_id == None:playlist_id = input("Music playlist ID: ")
    if path == None:path = input("Path to download: ")
    if finalpath == None:finalpath = input("Final path, where the files will be copied: ")
    if format == None:format = input("Format('mp3' or 'wav'): ")

    # get creditentials
    youtube = get_authenticated_service()

    # Create file of liked videos if not exists
    fetch_liked_videos(youtube)

    # Create file of playlist videos if not exists
    fetch_playlist_videos(youtube,playlist_id)
        
    if not os.path.exists(VIDEOS_TO_ADD_IN_PLAYLIST_FILE):
        # Create files videos to add and like in the playlist (new liked videos)
        create_videos_to_like_and_add_files()
        
        ##### ADD SUBSCRIPTION FUNCTION

        
    # Like videos
    like_videos(youtube)


    # Add videos in playlist
    add_videos(youtube,playlist_id)
    # Update playlist videos if videos have been added
    fetch_playlist_videos(youtube,playlist_id)


    # Deleting videos from playlist and liked list if there was any errors during operations (asking for each to user)
    # if os.path.exists(ERROR_LIKED_FILE):
    #     inteligent_deleting(ERROR_LIKED_FILE,youtube)

    # if os.path.exists(ERROR_ADDED_FILE):
    #     inteligent_deleting(ERROR_ADDED_FILE,youtube)

    # Get id to download
    create_videos_to_download(clean,path)

    
    # Download videos
    download_playlist(path,format)

    final_verification(path)

    print("\n\n\nDownloading programm ended successfully!!\n\n\n")

    


if __name__ == '__main__':
    process_new_liked_videos()