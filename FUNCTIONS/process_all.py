from pathlib import Path
from sqlite3 import Connection, Cursor
from typing import Literal
import time
from datetime import timedelta




from FUNCTIONS.PROCESS.add_new_ids import add_new_ids_to_database
from FUNCTIONS.PROCESS.remove_ids_not_in_list import remove_ids_not_in_list
from FUNCTIONS.extract_and_clean import extract_and_clean_video_ids
from FUNCTIONS.PROCESS.add_lyrics import process_lyrics_for_video
from FUNCTIONS.PROCESS.add_tags import process_tags_for_video
from FUNCTIONS.PROCESS.add_thumbails import process_thumbnail_for_video
from FUNCTIONS.PROCESS.check_file_integrity import check_file_integrity_for_video
from FUNCTIONS.PROCESS.remove_sponsorblock_segments import remove_sponsorblock_segments_for_video
from FUNCTIONS.PROCESS.embed_metadata import embed_metadata_for_video
from FUNCTIONS.PROCESS.add_album import process_album_for_video
from FUNCTIONS.download import download_video
from FUNCTIONS.sql_requests import get_videos_in_list, get_video_info_from_db, init_db
from FUNCTIONS.helpers import fprint, VideoInfo, VideoInfoMap


from logger import setup_logger
logger = setup_logger(__name__)




def process_all(
    download_path: Path,
    playlist_video_file: Path,
    embed_metadata: bool,
    get_lyrics: bool,
    recompute_lyrics: bool,

    get_thumbnail: bool,
    thumbnail_format: Literal["pad", "crop"],
    recompute_thumbnails: bool,

    use_sponsorblock: bool,
    categories: list[str],

    add_tags: bool,
    sep: str,
    start_def: str,
    end_def: str,
    tag_sep: str,
    recompute_tags: bool,

    add_album: bool,
    recompute_album: bool,

    retry_unavailable: bool,
    retry_private: bool,

    info: bool,
    error: bool,
    test_run: bool,

    remove_malformatted: bool,
    remove_no_longer_in_playlist: bool,
    add_folder_files_not_in_list: bool,

    cur: Cursor,
    conn: Connection
) -> dict[str,float | None]:




    # --- Process all videos ---

    Processing_start_time: float = time.time()

    # Initialise the database if not (create it)
    init_db(cur=cur, conn=conn)

    ids_present_in_down_dir: VideoInfoMap = extract_and_clean_video_ids(download_path, info=info,test_run=test_run, remove=remove_malformatted)



    add_new_ids_to_database(
        video_id_file=playlist_video_file,
        ids_presents_in_down_dir=ids_present_in_down_dir,
        add_folder_files_not_in_list=add_folder_files_not_in_list,
        info=info,
        errors=error,
        cur=cur,
        conn=conn
    )


    if remove_no_longer_in_playlist:
        remove_ids_not_in_list(
            video_id_file=playlist_video_file,
            download_path=download_path,
            info=info,
            error=error,
            cur=cur,
            test_run=test_run
        )


    video_ids = get_videos_in_list(cur)

    avg_times: list[float] = []
    eta_str: str = 'N/A'
    total_videos: int = len(video_ids)
    progress_count: int = 1


    calculating_duration: float = 0.0
    download_duration: float = 0.0
    cut_duration:  float = 0.0
    lyrics_duration: float = 0.0
    thumbnail_duration: float = 0.0
    tag_duration: float = 0.0
    album_duration: float = 0.0
    metadata_duration: float = 0.0




    if info: print(f"[PROCESSING] Processing {total_videos} videos...")
    logger.info(f"[PROCESSING] Processing {total_videos} videos...")

    # raise

    for video_id in video_ids:

        start_processing: float = time.time()

        progress_prefix = f"{progress_count:{len(str(total_videos))}d}/{total_videos} | {eta_str} | "


        need_download, checking_duration = check_file_integrity_for_video(
            video_id=video_id,
            download_path=download_path,
            ids_present_in_down_dir=ids_present_in_down_dir,
            retry_unavailable=retry_unavailable,
            retry_private=retry_private,
            cur=cur,
            conn=conn,
            test_run=test_run
        )
        calculating_duration += checking_duration


        if need_download:
            download_duration += download_video(
                download_path=download_path,
                video_id=video_id,
                progress_prefix=progress_prefix,
                info=info,
                cur=cur,
                conn=conn,
                test_run=test_run
            )

        data: VideoInfo = get_video_info_from_db(video_id=video_id, cur=cur)
        
        filename: str | None = data.get("filename")
        filepath: Path | None = download_path / filename if filename else None
        removed_segments_int: int = data.get("removed_segments_int",0)
        removed_segments_duration: float = data.get("removed_segments_duration",0.0)



        if filepath is None or not filepath.exists():
            if info: fprint(progress_prefix, f"Missing filename, title or file not found for '{video_id}', skipping rest of processing")
            logger.debug(f"[Sponsorblock] Missing filename, title or file not found for '{video_id}', skipping rest of processing")
            progress_count += 1
            continue





        if use_sponsorblock:
            cut_duration += remove_sponsorblock_segments_for_video(
                video_id=video_id,
                filepath=filepath,
                removed_segments_int=removed_segments_int,
                removed_segments_duration=removed_segments_duration,
                cur=cur,
                conn=conn,
                progress_prefix=progress_prefix,
                categories=categories,
                info=info,
                test_run=test_run
            )


        if get_lyrics:
            lyrics_duration += process_lyrics_for_video(
                video_id=video_id,
                filepath=filepath,
                video_info=data,
                progress_prefix=progress_prefix,
                info=info,
                error=error,
                cur=cur,
                conn=conn,
                test_run=test_run,
                recompute_lyrics=recompute_lyrics
            )


        if get_thumbnail:
            thumbnail_duration += process_thumbnail_for_video(
                video_id=video_id,
                video_info=data,
                filepath=filepath,
                thumbnail_format=thumbnail_format,
                progress_prefix=progress_prefix,
                info=info,
                error=error,
                cur=cur,
                conn=conn,
                test_run=test_run,
                recompute_thumbnails=recompute_thumbnails
            )


        if add_tags:
            calculating_duration += process_tags_for_video(
                video_id=video_id,
                video_info=data,
                filepath=filepath,
                progress_prefix=progress_prefix,
                info=info,
                error=error,
                cur=cur,
                conn=conn,
                test_run=test_run,
                recompute_tags=recompute_tags,
                sep=sep,
                start_def=start_def,
                end_def=end_def,
                tag_sep=tag_sep
            )


        if add_album:
            calculating_duration += process_album_for_video(
                video_info=data,
                filepath=filepath,
                progress_prefix=progress_prefix,
                recompute_album=recompute_album,
                info=info,
                error=error,
                test_run=test_run,
            )


        if embed_metadata:
            metadata_duration += embed_metadata_for_video(
                video_id=video_id,
                filepath=filepath,
                progress_prefix=progress_prefix,
                cur=cur,
                info=info,
                error=error,
                test_run=test_run
            )




        progress_count += 1
        if info: print()

        avg_times.append(time.time() - start_processing)
        if len(avg_times) > 5:
            _ = avg_times.pop(0)

        eta_seconds: float =(sum(avg_times) / len(avg_times)) * (total_videos - progress_count + 1)
        if eta_seconds > 5: eta_seconds = round(eta_seconds)
        eta_str = str(timedelta(seconds=eta_seconds))

    if info: print()

    Processing_end_time: float = time.time()
    Processing_total_time: float = Processing_end_time - Processing_start_time

    return {
        "total": Processing_total_time,
        "calculating_duration": calculating_duration,
        "download_duration": download_duration if download_duration else None,
        "cut_duration":  cut_duration,
        "lyrics_duration": lyrics_duration,
        "thumbnail_duration": thumbnail_duration,
        "tag_duration": tag_duration,
        "album_duration": album_duration,
        "metadata_duration": metadata_duration
    }