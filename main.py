from typing import Literal
import time
from datetime import timedelta


from CONSTANTS import JSON_DIR, CRED_DIR, DOWNLOAD_PATH, PLAYLIST_VIDEOS_FILE
from FUNCTIONS.get_playlist_videos import fetch_playlist_videos
from FUNCTIONS.PROCESS.show_final_stats import show_final_stats
from FUNCTIONS.sql_requests import get_db_connection
from FUNCTIONS.process_all import process_all


from logger import setup_logger
logger = setup_logger(__name__)




def main_list_process(

    playlist_id: str = "LL",

    use_sponsorblock: bool = True,
    get_lyrics: bool = True,
    get_thumbnail: bool = True,
    add_tags: bool = True,
    add_album: bool = True,
    embed_metadata: bool = True,

    force_recompute_album: bool = False,
    force_recompute_lyrics: bool = True,
    force_recompute_thumbnails: bool = False,
    force_recompute_tags: bool = False,
    force_recompute_yt_info: bool = False,


    thumbnail_format: Literal["pad", "crop"] = "pad",

    sponsorblock_categories: list[str] = ["music_offtopic", "sponsor", "intro", "outro"],  # pyright: ignore[reportCallInDefaultInitializer]

    sep: str = " ~ ",
    start_def: str = "[",
    end_def: str = "]",
    tag_sep: str = ",",

    retry_unavailable: bool = True,
    retry_private: bool = True,

    info: bool = True,
    error: bool = True,
    test_run: bool = False,

    clean: bool = False,
    remove_no_longer_in_playlist: bool = False,
    remove_malformatted: bool = True,
    create_db_if_not: bool = True,
    add_folder_files_not_in_list: bool = True,
    force_mp3_presence: bool = True
) -> None:
    """
    Custom downloading function, that use a main database of videos to know what to do:
    it fetches the playlist videos of the user, then append the infos to a SQL database (the main database) This database contains many infos,
    When the programm is run, all infos present on the list will be verified in the files and added to them if not present of false,
    the database behaves as main source of information, it is very important, more than the metadata info fields themselves.
    """


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
