from pathlib import Path
import json
from sqlite3 import Cursor
import time


# from DEBUG.compare_dicts import compare_dicts
from FUNCTIONS.HELPERS.fprint import fprint
from FUNCTIONS.HELPERS.helpers import VideoInfo, normalize_skips, remove_data_from_video_info, timestamp_to_id3_unique
from FUNCTIONS.metadata import get_metadata_tag, read_id3_tag, write_id3_tag


from FUNCTIONS.sql_requests import get_video_info_from_db
from FUNCTIONS.HELPERS.logger import setup_logger
logger = setup_logger(__name__)




def embed_metadata_for_video(
    video_id: str,
    filepath: Path,
    progress_prefix: str,
    test_run: bool,
    cur: Cursor,
    info: bool,
    error: bool,
) -> tuple[float, bool]:
    """
    Embed metadata from DB into a single MP3 file using get_video_info.
    Also sets the 'TDRC' (date) frame to the video's date_added.
    """

    start_processing: float = time.time()

    video_info: VideoInfo = get_video_info_from_db(video_id=video_id, cur=cur)
    date: float = video_info.get('date_added',0.0)
    tm: str = timestamp_to_id3_unique(ts=date)
    title: str = video_info.get("title", "")


    if info: fprint(progress_prefix, f"Embedding metadata for ?", title)
    logger.verbose(f"[Metadata] Embedding metadata for '{title}'")


    # Embed the id in the dat field, to sort the video in the player

    file_date, state = read_id3_tag(filepath=filepath, frame_id="TDRC")

    update_date: bool = False
    if state == 0:
        if isinstance(file_date, list):
            file_date = str(file_date[0])
        else: file_date = str(file_date)
        if file_date != tm:
            update_date = True

    else:
        update_date = True


    if update_date:
        success_date: bool = True
        if date:
            success_date = write_id3_tag(
                filepath=filepath,
                frame_id="TDRC",
                data=tm,
                test_run=test_run
            )
            if not success_date:
                if error: print(f"\n[Metadata] Failed to embed date '{tm}' for '{title}'")
                logger.warning(f"[Metadata] Failed to embed date '{tm}' for '{title}'")
            else:
                if info: fprint(progress_prefix, f"Embedded date '{tm}' for ?", title)
                logger.info(f"[Metadata] Embedded date '{tm}' for '{title}'")
    else:
        fprint(progress_prefix, "No need to change date, skipping")




    # Embed full metadata as JSON

    file_video_info, _ = get_metadata_tag(filepath=filepath)
    data: str = json.dumps(video_info,indent=4, ensure_ascii=True)

    update_data: bool = True
    if file_video_info:
        cleaned_file_info: VideoInfo = remove_data_from_video_info(data=file_video_info,to_remove=["date_added", "date_modified"])
        cleaned_data: VideoInfo = remove_data_from_video_info(data=video_info,to_remove=["date_added", "date_modified"])
        if "skips" in cleaned_file_info:
            cleaned_file_info = normalize_skips(cleaned_file_info)
        if (cleaned_file_info == cleaned_data ):
            if cleaned_data:
                update_data = False

        # Debug feature to see why they are updating
        # else:
            # compare_dicts(cleaned_data, cleaned_file_info)

    if update_data:
        success_meta: bool = write_id3_tag(
            filepath=filepath,
            frame_id="TXXX:metadata",
            data=data,
            test_run=test_run
        )

        if not success_meta:
            if error: print(f"\n[Metadata] Failed to embed metadata for '{title}'")
            logger.warning(f"[Metadata] Failed to embed metadata for '{title}'")
        else:
            if info: fprint(progress_prefix, f"Embedded metadata for ?", title)
            logger.info(f"[Metadata] Embedded metadata for '{title}'")
        return time.time() - start_processing, False
    else:

        fprint(progress_prefix, "No need to embed metadata for ?", title)
        logger.info(f"No need to embed metadata for {title}")
        return time.time() - start_processing, True



