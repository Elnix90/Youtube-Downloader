from typing import Literal
import time
from datetime import timedelta


from CONSTANTS import JSON_DIR, CRED_DIR, DOWNLOAD_PATH, PLAYLIST_VIDEOS_FILE
from config_loader import get_processing_defaults
from FUNCTIONS.get_playlist_videos import fetch_playlist_videos
from FUNCTIONS.PROCESS.show_final_stats import show_final_stats
from FUNCTIONS.sql_requests import get_db_connection
from FUNCTIONS.process_all import process_all


from logger import setup_logger
logger = setup_logger(__name__)




def main_list_process(
  
    playlist_id: str = None,
    embed_metadata: bool = None,
    add_album: bool = None,
    recompute_album: bool = None,

    get_lyrics: bool = None,
    recompute_lyrics: bool = None,

    get_thumbnail: bool = None,
    thumbnail_format: Literal["pad", "crop"] = None,
    recompute_thumbnails: bool = None,

    use_sponsorblock: bool = None,
    categories: list[str] = None,

    add_tags: bool = None,
    sep: str = None,
    start_def: str = None,
    end_def: str = None,
    tag_sep: str = None,
    recompute_tags: bool = None,

    retry_unavailable: bool = None,
    retry_private: bool = None,

    info: bool = None,
    error: bool = None,
    test_run: bool = None,

    clean: bool = None,
    remove_no_longer_in_playlist: bool = None,
    remove_malformatted: bool = None,
    create_db_if_not: bool = None,
    add_folder_files_not_in_list: bool = None

) -> None:
    """
    Custom downloading function, that use a main database of videos to know what to do:
    it fetches the playlist videos of the user, then append the infos to a SQL database (the main database) This database contains many infos,
    When the programm is run, all infos present on the list will be verified in the files and added to them if not present of false,
    the database behaves as main source of information, it is very important, more than the metadata info fields themselves.
    
    Les paramètres None utiliseront les valeurs par défaut du fichier config.toml
    """

    # Charger les valeurs par défaut depuis config.toml
    defaults = get_processing_defaults()
    
    # Utiliser les valeurs par défaut si les paramètres sont None
    playlist_id = playlist_id if playlist_id is not None else defaults["playlist_id"]
    embed_metadata = embed_metadata if embed_metadata is not None else defaults["embed_metadata"]
    add_album = add_album if add_album is not None else defaults["add_album"]
    recompute_album = recompute_album if recompute_album is not None else defaults["recompute_album"]
    
    get_lyrics = get_lyrics if get_lyrics is not None else defaults["get_lyrics"]
    recompute_lyrics = recompute_lyrics if recompute_lyrics is not None else defaults["recompute_lyrics"]
    
    get_thumbnail = get_thumbnail if get_thumbnail is not None else defaults["get_thumbnail"]
    thumbnail_format = thumbnail_format if thumbnail_format is not None else defaults["thumbnail_format"]
    recompute_thumbnails = recompute_thumbnails if recompute_thumbnails is not None else defaults["recompute_thumbnails"]
    
    use_sponsorblock = use_sponsorblock if use_sponsorblock is not None else defaults["use_sponsorblock"]
    categories = categories if categories is not None else defaults["categories"]
    
    add_tags = add_tags if add_tags is not None else defaults["add_tags"]
    sep = sep if sep is not None else defaults["sep"]
    start_def = start_def if start_def is not None else defaults["start_def"]
    end_def = end_def if end_def is not None else defaults["end_def"]
    tag_sep = tag_sep if tag_sep is not None else defaults["tag_sep"]
    recompute_tags = recompute_tags if recompute_tags is not None else defaults["recompute_tags"]
    
    retry_unavailable = retry_unavailable if retry_unavailable is not None else defaults["retry_unavailable"]
    retry_private = retry_private if retry_private is not None else defaults["retry_private"]
    
    info = info if info is not None else defaults["info"]
    error = error if error is not None else defaults["error"]
    test_run = test_run if test_run is not None else defaults["test_run"]
    
    clean = clean if clean is not None else defaults["clean"]
    remove_no_longer_in_playlist = remove_no_longer_in_playlist if remove_no_longer_in_playlist is not None else defaults["remove_no_longer_in_playlist"]
    remove_malformatted = remove_malformatted if remove_malformatted is not None else defaults["remove_malformatted"]
    create_db_if_not = create_db_if_not if create_db_if_not is not None else defaults["create_db_if_not"]
    add_folder_files_not_in_list = add_folder_files_not_in_list if add_folder_files_not_in_list is not None else defaults["add_folder_files_not_in_list"]


    All_processing_start: float = time.time()

    # Initialize path and creditentials

    JSON_DIR.mkdir(exist_ok=True)
    CRED_DIR.mkdir(exist_ok=True)

    DOWNLOAD_PATH.mkdir(parents=True, exist_ok=True)





    fetch_playlist_videos(
        playlist_id=playlist_id,
        file=PLAYLIST_VIDEOS_FILE,
        clean=clean,
        info=info,
        errors=error
    )


    with get_db_connection(create_if_not=create_db_if_not) as conn:
        cur = conn.cursor()


        processing_time: dict[str, float | None] = process_all(
            # download_path=DOWNLOAD_PATH,
            # playlist_video_file=PLAYLIST_VIDEOS_FILE,

            # force_recompute_yt_info=force_recompute_yt_info,
            # embed_metadata=embed_metadata,
            # get_lyrics=get_lyrics,
            # force_recompute_lyrics=force_recompute_lyrics,
            # get_thumbnail=get_thumbnail,
            # thumbnail_format=thumbnail_format,
            # force_recompute_thumbnails=force_recompute_thumbnails,
            # use_sponsorblock=use_sponsorblock,
            # sponsorblock_categories=categories,
            # add_tags=add_tags,
            # sep=sep,
            # start_def=start_def,
            # end_def=end_def,
            # tag_sep=tag_sep,
            # force_recompute_tags=force_recompute_tags,
            # add_album=add_album,
            # force_recompute_album=force_recompute_album,
            # retry_unavailable=retry_unavailable,
            # retry_private=retry_private,
            # info=info,
            # error=error,
            # test_run=test_run,
            # remove_malformatted=remove_malformatted,
            # remove_no_longer_in_playlist=remove_no_longer_in_playlist,
            # add_folder_files_not_in_list=add_folder_files_not_in_list,
            # force_mp3_presence=force_mp3_presence,
            # cur=cur,
            # conn=conn
            download_path=DOWNLOAD_PATH,
            playlist_video_file=PLAYLIST_VIDEOS_FILE,

            use_sponsorblock=use_sponsorblock,
            get_lyrics=get_lyrics,
            get_thumbnail=get_thumbnail,
            embed_metadata=embed_metadata,
            add_tags=add_tags,
            add_album=add_album,

            force_recompute_lyrics=force_recompute_lyrics,
            force_recompute_thumbnails=force_recompute_thumbnails,
            force_recompute_tags=force_recompute_tags,
            force_recompute_album=force_recompute_album,
            force_recompute_yt_info=force_recompute_yt_info,

            sponsorblock_categories=sponsorblock_categories,
            thumbnail_format=thumbnail_format,

            sep=sep,
            start_def=start_def,
            end_def=end_def,
            tag_sep=tag_sep,

            retry_unavailable=retry_unavailable,
            retry_private=retry_private,

            info=info,
            error=error,
            test_run=test_run,

            remove_malformatted=remove_malformatted,
            remove_no_longer_in_playlist=remove_no_longer_in_playlist,
            add_folder_files_not_in_list=add_folder_files_not_in_list,
            force_mp3_presence=force_mp3_presence,

            cur=cur,
            conn=conn
        )


        All_processing_end: float = time.time()

        Total_processing_time: float = All_processing_end - All_processing_start
        Total_processing_duration = str(timedelta(milliseconds=int(round(Total_processing_time, 3) * 1000)))

        calculating_duration = str(timedelta(milliseconds=int(round(processing_time["calculating_duration"], 3) * 1000))) if processing_time["calculating_duration"] else None
        download_duration = str(timedelta(milliseconds=int(round(processing_time["download_duration"], 3) * 1000))) if processing_time["download_duration"] else None
        cut_duration = str(timedelta(milliseconds=int(round(processing_time["cut_duration"], 3) * 1000))) if processing_time["cut_duration"] else None
        lyrics_duration = str(timedelta(milliseconds=int(round(processing_time["lyrics_duration"], 3) * 1000))) if processing_time["lyrics_duration"] else None
        thumbnail_duration = str(timedelta(milliseconds=int(round(processing_time["thumbnail_duration"], 3) * 1000))) if processing_time["thumbnail_duration"] else None
        tag_duration = str(timedelta(milliseconds=int(round(processing_time["tag_duration"], 3) * 1000))) if processing_time["tag_duration"] else None
        album_duration = str(timedelta(milliseconds=int(round(processing_time["album_duration"], 3) * 1000))) if processing_time["album_duration"] else None
        metadata_duration = str(timedelta(milliseconds=int(round(processing_time["metadata_duration"], 3) * 1000))) if processing_time["metadata_duration"] else None




        if info:
            show_final_stats(
                download_path=DOWNLOAD_PATH,
                entire_duration=Total_processing_duration,
                calculating_duration=calculating_duration,
                download_duration=download_duration,
                cut_duration=cut_duration,
                lyrics_duration=lyrics_duration,
                thumbnail_duration=thumbnail_duration,
                tag_duration=tag_duration,
                album_suration=album_duration,
                metadata_duration=metadata_duration,
                cur=cur,
                test_run=test_run,
                remove_malformatted=remove_malformatted,
                force_mp3_presence=force_mp3_presence
            )



if __name__ == "__main__":
    main_list_process()
