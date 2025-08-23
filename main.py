from __future__ import annotations
from pathlib import Path
import shutil
from dotenv import load_dotenv
import os
from typing import Optional


from FUNCTIONS.add_videos import add_videos
from FUNCTIONS.create_videos_to_add_file import create_videos_to_add_files
from FUNCTIONS.create_videos_to_download_file import create_videos_to_download
from FUNCTIONS.download import download_playlist
from FUNCTIONS.final_verification import final_verification
from FUNCTIONS.get_creditentials import get_authenticated_service
from FUNCTIONS.get_playlist_videos import fetch_playlist_videos
from FUNCTIONS.remove_private_videos import remove_private_videos
from CONSTANTS import *

def process_new_liked_videos(
    embed_metadata: bool = True,
    get_lyrics: bool = True,
    show_ETA: bool = True,
    use_sponsorblock: bool = True,
    add_tags: bool = True,
    verbose: bool = True,
    errors: bool = True
) -> None:
    """
    Fetch all liked videos and a playlist, add them to the playlist, and download them with optional lyrics.
    """

    load_dotenv()
    playlist_id_env: str | None = os.getenv("playlistid")
    if playlist_id_env is None:
        raise EnvironmentError("Environment variable 'playlistid' is not set")
    playlist_id: str = playlist_id_env


    JSON_DIR.mkdir(exist_ok=True)
    CRED_DIR.mkdir(exist_ok=True)
    DOWNLOAD_PATH.mkdir(parents=True, exist_ok=True)

    youtube = get_authenticated_service()

    fetch_playlist_videos(
        youtube,
        playlist_id,
        PLAYLIST_VIDEOS_FILE,
        verbose=verbose,
        errors=errors
    )

    fetch_playlist_videos(
        youtube,
        "LL",
        LIKED_VIDEOS_FILE,
        verbose=verbose,
        errors=errors
    )

    create_videos_to_add_files()
    add_videos(youtube, playlist_id, Path(VIDEOS_TO_ADD_IN_PLAYLIST_FILE))

    create_videos_to_download(DOWNLOAD_PATH)
    download_playlist(
        VIDEOS_TO_DOWNLOAD_FILE,
        DOWNLOAD_PATH,
        embed_metadata=embed_metadata,
        get_lyrics=get_lyrics,
        use_list=False,
        show_ETA=show_ETA,
        use_sponsorblock=use_sponsorblock,
        add_tags=add_tags
        )
    

    remove_private_videos(youtube)
    final_verification(DOWNLOAD_PATH)

    print("\n\n\nDownloading program ended successfully!!\n\n\n")
    shutil.rmtree(JSON_DIR)


def download_videos_from_playlist(
    embed_metadata: bool = True,
    get_lyrics: bool = True,
    show_ETA: bool = True,
    use_sponsorblock: bool = True,
    add_tags: bool = True,
    clean: bool = True,
    verbose: bool = True,
    errors: bool = True
) -> None:
    """
    Download all videos in a given playlist to a folder.
    """

    load_dotenv()
    playlist_id_env: str | None = os.getenv("playlistid")
    if playlist_id_env is None:
        raise EnvironmentError("Environment variable 'playlistid' is not set")
    playlist_id: str = playlist_id_env


    DOWNLOAD_PATH.mkdir(parents=True, exist_ok=True)

    youtube = get_authenticated_service()
    playlist_videos_file = JSON_DIR / f"{playlist_id}.json"
    fetch_playlist_videos(
        youtube,
        playlist_id,
        playlist_videos_file,
        clean=clean,
        verbose=verbose,
        errors=errors
    )

    download_playlist(
        playlist_videos_file,
        DOWNLOAD_PATH,
        embed_metadata=embed_metadata,
        get_lyrics=get_lyrics,
        show_ETA=show_ETA,
        use_sponsorblock=use_sponsorblock,
        add_tags=add_tags
        )


def main_list_process(
    embed_metadata: bool = True,
    get_lyrics: bool = True,
    show_ETA: bool = True,
    use_sponsorblock: bool = True,
    add_tags: bool = True,
    remove_no_longer_in_like: bool = False,
    recompute_tags: bool = True,
    retry_unavailable: bool = False,
    clean: bool = False,
    info: bool = True,
    verbose: bool = True,
    errors: bool = True
) -> None:
    """
    Custom downloading function, that use a main list of videos to know what to do:
    it fetches the liked videos of the user, then append the infos to a json (the main list) This list contains many infos,
    it is formatted like this: (all keys may not be present for every video) 
    {
        video_id : {
            "id" : id,
            "title" : title,
            "thumbnail" : thumbnail,
            "description" : description,
            "channel_id" : channel_id,
            "channel_url" : channel_url,
            "duration" : duration,
            "view_count" : view_count,
            "comment_count" : comment_count,
            "like_count" : like_count,
            "uploader" : uploader,
            "channel_follower_count" : channel_follower_count,
            "uploader_id" : uploader_id,
            "uploader_url" : uploader_url,
            "upload_date" : upload_date,
            "timestamp" : timestamp,
            "duration_string" : duration_string,

            "filename" : filename_for_this_music,
            "status" : "available" or "unavailable",               # If the status is not "available" the programm will just skip the video

            "date_added" : date_where_it_is added_to_this_list,    # to be able to sort the finals videos by date to have the more recent first (more likely prone to be liked)
            "lyrics" : DOWNLOAD_PATH,
            "try_lyrics_if_not" : bool,
            "lyrics_found" : bool,                                 # if the lyrics were found or not, to be able to retry later
            "query_used" : str,                                    # the query used to find the lyrics, to be able to retry later
            "tags" : list,                                         # a list of tage the user can update, and the next time the programm is used with this list, it will be added to the files (to sort, more efficient than a playlist who can change between apps)
            "remix_of" : video_id                                  # If the video is a remix of an other, useful to pick the right artist -> may be implemented later
        }
    }
    
    When the programm is run, all infos present on the list will be verified in the files and added to them if not present of false,
    the list behaves as main source of information, it is very important, more than the fiels itselves.
    """
    from FUNCTIONS.list import Process_list

    pl = Process_list()


    JSON_DIR.mkdir(exist_ok=True)
    CRED_DIR.mkdir(exist_ok=True)
    DOWNLOAD_PATH.mkdir(parents=True, exist_ok=True)



    youtube = get_authenticated_service()
    fetch_playlist_videos(
        youtube,
        "LL",
        LIKED_VIDEOS_FILE,
        clean=clean,
        verbose=verbose,
        errors=errors
    )


    pl.add_new_ids_to_list(
        LIKED_VIDEOS_FILE,
        verbose=verbose,
        errors=errors
    )

    if remove_no_longer_in_like:
        pl.remove_video_not_in_liked(
            LIKED_VIDEOS_FILE,
            info=info,
            verbose=verbose,
            errors=errors
            )


    pl.get_videos_to_download(
        Path(VIDEOS_TO_DOWNLOAD_FILE),
        retry_unavailable=retry_unavailable,
        info=info,
        verbose=verbose,
        errors=errors
    )

    duration: Optional[str] = None
    if Path(VIDEOS_TO_DOWNLOAD_FILE).exists():
        duration = download_playlist(
            VIDEOS_TO_DOWNLOAD_FILE,
            DOWNLOAD_PATH,
            embed_metadata=embed_metadata,
            get_lyrics=get_lyrics,
            use_list=True,
            show_ETA=show_ETA,
            use_sponsorblock=use_sponsorblock,
            add_tags=add_tags
        )

    pl.add_tags(
        recompute_tags=recompute_tags,
        info=info,
        verbose=verbose,
        errors=errors
    )

    pl.update_metadata(info=info,verbose=verbose,errors=errors)

    pl.show_final_stats(duration=duration)




if __name__ == "__main__":
    # process_new_liked_videos()
    # download_videos_from_playlist()
    main_list_process()
