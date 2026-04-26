"""
Embed DB metadata into the video itself to ensure security in case of loosing the DB,
and also the data edded to sort it in the music player
"""
import json
import time
from pathlib import Path
from sqlite3 import Cursor

from constants import ADD_ENTRY_ID_TO_TITLE, ENTRY_ID_SEPARATOR, INCLUDE_TIME_IN_EMBEDDED_TIME

# from DEBUG.compare_dicts import compare_dicts
from FUNCTIONS.HELPERS.fprint import fprint
from FUNCTIONS.HELPERS.helpers import (
    VideoInfo,
    has_entry_id_prefix,
    normalize_skips,
    remove_data_from_video_info,
    timestamp_to_id3_unique,
)
from FUNCTIONS.HELPERS.logger import setup_logger
from FUNCTIONS.metadata import get_metadata_tag, read_id3_tag, write_id3_tag
from FUNCTIONS.sql_requests import get_entry_id, get_video_info_from_db

logger = setup_logger(__name__)


def embed_metadata_for_video(
    video_id: str,
    filepath: Path,
    progress_prefix: str,
    test_run: bool,
    cur: Cursor,
    info: bool,
    force_update_date: bool,
    force_update_metadata: bool
) -> tuple[float, bool]:
    """
    Embed metadata from DB into a single MP3 file using get_video_info.
    Also sets the 'TDRC' (date) frame to the video's date_added.
    """

    start_processing: float = time.time()

    video_info: VideoInfo = get_video_info_from_db(video_id=video_id, cur=cur)
    date: float = video_info.get('date_added', 0.0)
    tm: str = timestamp_to_id3_unique(date, INCLUDE_TIME_IN_EMBEDDED_TIME)
    title: str = video_info.get("title", "")

    if info:
        fprint(progress_prefix, "Embedding metadata for ?", title)
    logger.verbose(f"[Metadata] Embedding metadata for '{title}'")

    # -----------------------------
    # Embed the date field
    # -----------------------------

    file_date, state = read_id3_tag(filepath, "TDRC")

    update_date: bool = force_update_date
    if state == 0:
        if isinstance(file_date, list):
            file_date = str(file_date[0])
        else:
            file_date = str(file_date)
        if file_date != tm:
            update_date = True

    else:
        update_date = True

    if update_date:
        if date:
            success_date = write_id3_tag(filepath, "TDRC", tm, test_run)
            if not success_date:
                logger.warning(f"[Metadata] Failed to embed date '{tm}' for '{title}'")
            else:
                if info:
                    fprint(progress_prefix, f"Embedded date '{tm}' for ?", title)
                logger.info(f"[Metadata] Embedded date '{tm}' for '{title}'")
    else:
        fprint(progress_prefix, "No need to change date, skipping")

    # -----------------------------
    # Embed entry_id into the title
    # -----------------------------

    filename = filepath.name

    # Get db fields: video_id and canonical title
    row = cur.execute(  # pyright: ignore[reportAny]
        "SELECT title FROM Videos WHERE filename = ?", (filename,)
    ).fetchone()
    if not row:
        logger.warning(f"[Sanitize Titles] No DB entry for file: {filename}")

    else:
        db_title = row[0]  # pyright: ignore[reportAny]
        db_title = db_title or ""

        entry_id = str(get_entry_id(video_id, cur))

        # Read current TIT2
        title_data, status = read_id3_tag(filepath, "TIT2")
        current_title = title_data[0].strip() if (status == 0 and title_data) else ""

        has_prefix = has_entry_id_prefix(current_title, entry_id)

        if ADD_ENTRY_ID_TO_TITLE:
            # Decide base title: prefer DB.title, fallback to current tag if DB missing
            base_title = db_title if db_title else current_title
            if not base_title:
                logger.warning(f"[Sanitize Titles] No title available to prefix for '{filename}'")

            else:
                if has_prefix:
                    logger.debug(f"[Sanitize Titles] Skipping (already prefixed): {current_title} ({filename})")
                else:
                    new_title = f"{entry_id}{ENTRY_ID_SEPARATOR}{base_title}"
                    logger.info(f"[Sanitize Titles] Will add prefix for '{filename}': '{current_title}' -> '{new_title}'")
                    if not test_run:
                        ok = write_id3_tag(filepath, "TIT2", new_title, test_run)
                        if not ok:
                            logger.error(f"[Sanitize Titles] Failed to write title for '{filename}'")
        else:
            # Remove prefix if present
            if not has_prefix:
                logger.debug(f"[Sanitize Titles] Skipping (no prefix): {current_title} ({filename})")
            else:
                # remove only the first occurrence and strip whitespace
                remainder = (
                    current_title.split(ENTRY_ID_SEPARATOR, 1)[1].strip() if ENTRY_ID_SEPARATOR in current_title else ""
                )
                # if remainder is empty, restore DB title (so we don't blank titles)
                new_title = remainder if remainder else db_title
                logger.info(
                    f"[Sanitize Titles] Will remove prefix for '{filename}': '{current_title}' -> '{new_title}'"
                )
                if not test_run:
                    ok = write_id3_tag(filepath, "TIT2", new_title, test_run)
                    if not ok:
                        logger.error(f"[Sanitize Titles] Failed to write title for '{filename}'")

    # -----------------------------
    # Embed full metadata as JSON
    # -----------------------------

    file_video_info, _ = get_metadata_tag(filepath=filepath)
    data: str = json.dumps(video_info, indent=4, ensure_ascii=True)

    update_data: bool = True
    if file_video_info and not force_update_metadata:
        cleaned_file_info: VideoInfo = remove_data_from_video_info(
            data=file_video_info, to_remove=["date_added", "date_modified"]
        )
        cleaned_data: VideoInfo = remove_data_from_video_info(
            data=video_info, to_remove=["date_added", "date_modified"]
        )
        if "skips" in cleaned_file_info:
            cleaned_file_info = normalize_skips(cleaned_file_info)
        if cleaned_file_info == cleaned_data:
            if cleaned_data:
                update_data = False

        # Debug feature to see what's the difference, and why the code updates the tags
        # else:
        #     print(compare_dicts(cleaned_file_info, cleaned_data))

    if update_data:
        success_meta: bool = write_id3_tag(
            filepath=filepath,
            frame_id="TXXX:metadata",
            data=data,
            test_run=test_run,
        )

        if not success_meta:
            logger.warning(f"[Metadata] Failed to embed metadata for '{title}'")
        else:
            if info:
                fprint(progress_prefix, "Embedded metadata for ?", title)
            logger.info(f"[Metadata] Embedded metadata for '{title}'")
        return time.time() - start_processing, False

    fprint(progress_prefix, "No need to embed metadata for ?", title)
    logger.info(f"No need to embed metadata for {title}")
    return time.time() - start_processing, True
