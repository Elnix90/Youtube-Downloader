from pathlib import Path
from sqlite3 import Connection, Cursor
import time

from FUNCTIONS.metadata import repair_mp3_file
from FUNCTIONS.sql_requests import update_video_db, get_video_info_from_db
from FUNCTIONS.helpers import VideoInfo, VideoInfoMap, youtube_required_info



from logger import setup_logger
logger = setup_logger(__name__)


def check_file_integrity_for_video(
    video_id: str,
    download_path: Path,
    ids_present_in_down_dir: VideoInfoMap,
    retry_unavailable: bool,
    retry_private: bool,
    cur: Cursor,
    conn: Connection,
    test_run: bool
) -> tuple[bool,float]:
    """
    Check integrity for a single video_id.
    Returns True if the video needs to be downloaded, False otherwise.
    """
    start_processing: float = time.time()


    
    # --- Fetch all existing DB data ---
    video_data = get_video_info_from_db(video_id, cur)

    logger.info(f"Checking file integrity for {video_id}")


    # --- Case: video exists in download dir ---
    if video_id in ids_present_in_down_dir:
        metadata: VideoInfo = ids_present_in_down_dir.get(video_id, {})
        filename: str = metadata.get("filename", video_data.get("filename", ""))
        filepath = download_path / filename if filename else None
        if not filepath or not filepath.exists():
            logger.debug(f"[File Checking] Missing filename or file not found for '{video_id}'")
            return True ,time.time() - start_processing

 
        # Merge DB data with extracted metadata
        fusion: VideoInfo = metadata | video_data

        if all(key in fusion and fusion[key] is not None for key in youtube_required_info):
            if repair_mp3_file(filepath,test_run):
                fusion["status"] = 0  # downloaded
                update_video_db(video_id, fusion, cur, conn)
                logger.info(f"[File Checking] File valid and repaired: '{filepath.name}'")
                return False ,time.time() - start_processing
            else:
                logger.warning(f"[File Checking] Corrupted file, re-downloading: '{filepath.name}'")
                return True ,time.time() - start_processing
        else:
            missings: set[str] = set(youtube_required_info) - set(fusion.keys())
            n_missings = len(missings)
            print(missings)

            logger.warning(f"[File Checking] Metadata incomplete missing {n_missings} keys, re-downloading: '{filepath.name}'")
            return True ,time.time() - start_processing


    # --- Case: video not present in download dir ---
    status: int = video_data.get("status", 0)
    if status == 1 and not retry_unavailable:
        logger.info(f"[File Checking] Video {video_id} unavailable, skipping")
        return False ,time.time() - start_processing
    elif status == 2 and not retry_private:
        logger.info(f"[File Checking] Video {video_id} private, skipping")
        return False ,time.time() - start_processing
    else:
        update_video_db(video_id=video_id, update_fields={"removed_segments_int":0, "removed_segments_duration": 0.0},cur=cur, conn=conn)
        logger.info(f"[File Checking] Missing in download dir, will be downloaded: {video_id}")
        return True ,time.time() - start_processing




# def check_file_integrity(
#     music_path: Path,
#     videos_file: Path,
#     cur: Cursor,
#     conn: Connection,
#     retry_unavailable: bool,
#     retry_private: bool,
#     info: bool,
#     test_run: bool,
#     remove_malformatted: bool
# ) -> list[str]:
#     """
#     Iterate over all videos and check integrity.
#     Returns the list of video_ids that need to be downloaded.
#     """
#     ids_present_in_down_dir: VideoInfoMap = clean_and_extract_video_ids(music_path, info=info,test_run=test_run, remove=remove_malformatted)

    

#     videos_to_download: list[str] = []
#     video_to_check: list[str] = load(file=videos_file)


#     for video_id in video_to_check:
#         try:
#             needs_download = check_file_integrity_for_video(
#                 video_id=video_id,
#                 music_path=music_path,
#                 youtube_required_info=youtube_required_info,
#                 ids_present_in_down_dir=ids_present_in_down_dir,
#                 retry_unavailable=retry_unavailable,
#                 retry_private=retry_private,
#                 cur=cur,
#                 conn=conn,
#                 test_run=test_run

#             )
#             if needs_download:
#                 videos_to_download.append(video_id)
#         except Exception as e:
#             logger.error(f"[File Checking] Unexpected error while checking '{video_id}': {e}")

#     return videos_to_download
