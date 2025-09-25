import time
from datetime import timedelta

from CONSTANTS import (
    CONFIG,
    JSON_DIR,
    CRED_DIR,
    DOWNLOAD_PATH,
    PLAYLIST_VIDEOS_FILE,
)
from FUNCTIONS.get_playlist_videos import fetch_playlist_videos
from FUNCTIONS.PROCESS.show_final_stats import show_final_stats
from FUNCTIONS.sql_requests import get_db_connection
from FUNCTIONS.process_all import process_all


from FUNCTIONS.HELPERS.logger import setup_logger
logger = setup_logger(__name__)


def main_list_process() -> None:
    """
    Main processing function.

    Workflow:
    1. Fetch the playlist videos for the user and save them into a JSON file.
    2. Append or update video information into the main SQL database.
    3. Process videos (download, lyrics, thumbnails, metadata, etc.) according to CONFIG.
    4. Show final statistics after processing.

    """

    all_processing_start: float = time.time()


    # Initialize paths and credentials
    JSON_DIR.mkdir(exist_ok=True)
    CRED_DIR.mkdir(exist_ok=True)
    DOWNLOAD_PATH.mkdir(parents=True, exist_ok=True)

    # Step 1: Fetch playlist videos
    fetch_playlist_videos(
        playlist_id=CONFIG["processing"]["playlist_id"],
        file=PLAYLIST_VIDEOS_FILE,
        clean=CONFIG["processing"]["clean"],
        info=CONFIG["processing"]["info"],
        errors=CONFIG["processing"]["error"],
    )

    # Step 2: Process database and files
    with get_db_connection(create_if_not=CONFIG["processing"]["create_db_if_not"]) as conn:
        cur = conn.cursor()

        processing_time: dict[str, float | None] = process_all(
            download_path=DOWNLOAD_PATH,
            playlist_video_file=PLAYLIST_VIDEOS_FILE,

            # SponsorBlock
            use_sponsorblock=CONFIG["processing"]["use_sponsorblock"],
            sponsorblock_categories=CONFIG["processing"]["sponsorblock_categories"],

            # Lyrics
            get_lyrics=CONFIG["processing"]["get_lyrics"],
            force_recompute_lyrics=CONFIG["processing"]["force_recompute_lyrics"],

            # Thumbnails
            get_thumbnail=CONFIG["processing"]["get_thumbnail"],
            thumbnail_format=CONFIG["processing"]["thumbnail_format"],
            force_recompute_thumbnails=CONFIG["processing"]["force_recompute_thumbnails"],

            # Metadata
            embed_metadata=CONFIG["processing"]["embed_metadata"],
            add_tags=CONFIG["processing"]["add_tags"],
            force_recompute_tags=CONFIG["processing"]["force_recompute_tags"],

            # Album
            add_album=CONFIG["processing"]["add_album"],
            force_recompute_album=CONFIG["processing"]["force_recompute_album"],

            # Tags formatting
            sep=CONFIG["processing"]["tag_separator"],
            start_def=CONFIG["processing"]["tag_start_delimiter"],
            end_def=CONFIG["processing"]["tag_end_delimiter"],
            tag_sep=CONFIG["processing"]["tag_inner_separator"],

            # Retry logic
            retry_unavailable=CONFIG["processing"]["retry_unavailable"],
            retry_private=CONFIG["processing"]["retry_private"],

            # Recompute things
            force_mp3_presence=CONFIG["processing"]["force_mp3_presence"],
            force_recompute_yt_info=CONFIG["processing"]["force_recompute_yt_info"],

            # Remix
            get_remix_of=CONFIG["processing"]["get_remix_of"],
            force_recompute_remix_of=CONFIG["processing"]["force_recompute_remix_of"],

            # Behavior
            info=CONFIG["processing"]["info"],
            error=CONFIG["processing"]["error"],
            test_run=CONFIG["processing"]["test_run"],

            # Clean up
            remove_malformatted=CONFIG["processing"]["remove_malformatted"],
            remove_no_longer_in_playlist=CONFIG["processing"]["remove_no_longer_in_playlist"],
            add_folder_files_not_in_list=CONFIG["processing"]["add_folder_files_not_in_list"],

            # DB cursor
            cur=cur,
            conn=conn,
        )

        # Step 3: Calculate durations
        all_processing_end: float = time.time()
        total_processing_time: float = all_processing_end - all_processing_start
        total_processing_duration = str(
            timedelta(milliseconds=int(round(total_processing_time, 3) * 1000))
        )

        def ms_to_str(ms: float | None) -> str | None:
            return (
                str(timedelta(milliseconds=int(round(ms, 3) * 1000)))
                if ms is not None
                else None
            )

        calculating_duration = ms_to_str(processing_time.get("calculating_duration"))
        download_duration = ms_to_str(processing_time.get("download_duration"))
        cut_duration = ms_to_str(processing_time.get("cut_duration"))
        lyrics_duration = ms_to_str(processing_time.get("lyrics_duration"))
        thumbnail_duration = ms_to_str(processing_time.get("thumbnail_duration"))
        tag_duration = ms_to_str(processing_time.get("tag_duration"))
        album_duration = ms_to_str(processing_time.get("album_duration"))
        metadata_duration = ms_to_str(processing_time.get("metadata_duration"))

        # Step 4: Show final stats
        if CONFIG["processing"]["info"]:
            show_final_stats(
                download_path=DOWNLOAD_PATH,
                entire_duration=total_processing_duration,
                calculating_duration=calculating_duration,
                download_duration=download_duration,
                cut_duration=cut_duration,
                lyrics_duration=lyrics_duration,
                thumbnail_duration=thumbnail_duration,
                tag_duration=tag_duration,
                album_duration=album_duration,
                metadata_duration=metadata_duration,
                cur=cur,
                test_run=CONFIG["processing"]["test_run"],
                remove_malformatted=CONFIG["processing"]["remove_malformatted"],
                force_mp3_presence=CONFIG["processing"]["force_mp3_presence"]
            )


if __name__ == "__main__":
    main_list_process()
