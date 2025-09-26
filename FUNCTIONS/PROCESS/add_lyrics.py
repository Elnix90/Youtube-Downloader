from pathlib import Path
from sqlite3 import Connection, Cursor
import time


from FUNCTIONS.HELPERS.fprint import fprint
from FUNCTIONS.HELPERS.helpers import VideoInfo
from FUNCTIONS.sql_requests import update_video_db, get_video_info_from_db
from FUNCTIONS.lyrics import embed_lyrics_into_mp3, remove_lyrics_from_mp3, has_lyrics
from FUNCTIONS.extract_lyrics import get_lyrics_from_syncedlyrics

from CONSTANTS import MAX_LYRICS_RETRIES

from FUNCTIONS.HELPERS.logger import setup_logger
logger = setup_logger(__name__)


def process_lyrics_for_video(
    uploader: str,
    try_lyrics_if_not: bool,
    remove_lyrics: bool,
    lyrics_retries: int,
    title: str,

    subtitles: str | None,
    # syncedlyrics: str | None,
    auto_subs: str | None,

    skips: list[tuple[float, float]] | None,
    duration: int | None,
    remix_of: str | None,

    video_id: str,
    filepath: Path,
    progress_prefix: str,
    info: bool,
    error: bool,
    cur: Cursor,
    conn: Connection,
    test_run: bool,
    recompute_lyrics: bool
) -> float:
    """
    Process lyrics for a given video: create/update/remove .lrc file (no MP3 embedding).
    Works directly with the SQLite database using VideoInfo.
    """ 

    start_processing: float = time.time()

    lyrics_file_path: Path = filepath.with_suffix(".lrc")
    file_lyrics: str | None = has_lyrics(mp3_path=filepath)
    orig_duration: int | None = None
    lyrics: str | None = None
    remix_lyrics: str | None = None

    if remix_of is not None:
        logger.info(f"[Lyrics] video '{video_id}' is a remix of '{remix_of}', processing")
        remix_info: VideoInfo = get_video_info_from_db(video_id=remix_of, cur=cur)

        remix_subtitles: str | None = remix_info.get("subtitles")
        remix_syncedlyrics: str | None = remix_info.get("syncedlyrics")
        remix_auto_subs: str | None = remix_info.get("auto_subs")

        if remix_subtitles:
            remix_lyrics = remix_subtitles
        elif remix_syncedlyrics:
            remix_lyrics = remix_syncedlyrics
        elif remix_auto_subs:
            remix_lyrics = remix_auto_subs
        else:
            remix_lyrics = None

        orig_duration = remix_info.get("duration")
        # print(remix_lyrics,orig_duration)

    # elif subtitles is not None:
    #     lyrics = subtitles
    # elif syncedlyrics:
    #     lyrics = syncedlyrics
    # elif auto_subs:
    #     lyrics = auto_subs
    # else:
    #     lyrics = None

    update_fields: VideoInfo = {}

    reached_max_retries: bool = False
    # Do not compute lyrics, only take those from lyrics music if exists
    if lyrics_retries > MAX_LYRICS_RETRIES:
        update_fields["try_lyrics_if_not"] = False
        reached_max_retries = True


    # --- CASE A: Fetch or update lyrics ---
    if not remove_lyrics:
        if info: fprint(progress_prefix, f"Processing lyrics for ?", title)
        logger.info(f"[Lyrics] Processing lyrics for '{title}'")

        embed_lyrics_into_file: bool = recompute_lyrics


        # If the video is set as a remix
        if remix_of is not None and remix_lyrics is not None:
            embed_lyrics_into_file = False
            try:
                success, lrcs = embed_lyrics_into_mp3(
                    filepath=filepath,
                    lyrics=remix_lyrics,
                    test_run=test_run,
                    file_duration=duration or 0,
                    skips=skips,
                    original_duration=orig_duration
                )
                if success:
                    update_fields["lyrics"] = lrcs
                    if info: fprint(progress_prefix, f"Lyrics created from remix '{remix_of}' for ?", title)
                    logger.info(f"[Lyrics] Lyrics created from remix '{remix_of}' for '{title}'")
                else:
                    if error: print(f"\nFailed to write remix_lyrics .lrc for '{title}'")
                    logger.error(f"[Lyrics] Failed to write remix_lyrics .lrc for '{title}'")
            except Exception as e:
                if error: print(f"\nError updating remix_lyrics for '{title}': {e}")
                logger.error(f"[Lyrics] Error updating remix_lyrics for '{title}': {e}")

        # Condition here to prevent lyrics from computing but allowing embedding if set as a remix
        elif reached_max_retries and not recompute_lyrics:
            pass

        elif file_lyrics is not None and not recompute_lyrics:
            lyrics = file_lyrics

            if info: fprint(progress_prefix, f"OK, no update needed for ?", title)
            logger.info(f"[Lyrics] OK, no update needed for '{lyrics_file_path.name}'")

        
        elif try_lyrics_if_not or recompute_lyrics:
            logger.verbose(f"[Lyrics] Trying to fetch lyrics for '{filepath}'")

            # Prioritize existing file content if present and recompute not forced
            if file_lyrics is not None and not recompute_lyrics:
                logger.debug(f"[Lyrics] Using lyrics from existing .lrc: '{lyrics_file_path}'")
                lyrics = file_lyrics
                embed_lyrics_into_file = True

            else:
                lyrics = None
                # Choose which lyrics to use
                if subtitles is not None:
                    logger.debug(f"[Choosing lyrics] Using manual subtitles from youtube for '{title}'")
                    lyrics = subtitles
                else:
                    if title and uploader:
                        logger.debug(f"[Choosing lyrics] Using lyrics from syncedlyrics for '{title}'")
                        lyrics, query = get_lyrics_from_syncedlyrics(title, uploader)
                        if lyrics is None:
                            if auto_subs is not None:
                                logger.debug(f"[Choosing lyrics] Using auto subtitles from youtube for '{title}'")
                                lyrics = auto_subs
                        else:
                            update_fields["syncedlyrics_query"] = query
                            update_fields["syncedlyrics"] = lyrics

                if lyrics is not None:
                    embed_lyrics_into_file = True
                else:
                    if info: fprint(progress_prefix,f"No lyrics found for ? by ?", title, uploader)
                    logger.info(f"[Lyrics] No lyrics found for '{title}' by '{uploader}'")
                    embed_lyrics_into_file = False
                update_fields["lyrics_retries"] = lyrics_retries + 1

        else:
            logger.debug("[Lyrics] Try lyrics if not is False and not asked to recompute lyrics")


        if embed_lyrics_into_file:
            if lyrics is not None:
                try:
                    success, lrcs = embed_lyrics_into_mp3(
                        filepath=filepath,
                        lyrics=lyrics,
                        test_run=test_run,
                        file_duration=duration or 0,
                        skips=skips,
                        original_duration=orig_duration
                    )
                    if success:
                        update_fields["lyrics"] = lrcs
                        if info: fprint(progress_prefix, f"Lyrics updated for ?", title)
                        logger.info(f"[Lyrics] Lyrics updated for '{title}'")
                    else:
                        if error: print(f"\nFailed to write lyrics .lrc for '{title}'")
                        logger.error(f"[Lyrics] Failed to write lyrics .lrc for '{title}'")

                    # Update anyways, if lo lyrics found, should not overwrite but update the conter (lyrics_retries)

                except Exception as e:
                    if error: print(f"\nError updating lyrics for '{title}': {e}")
                    logger.error(f"[Lyrics] Error updating lyrics for '{title}': {e}")
            else:
                logger.error(f"[Lyrics] Lyrics is None, cannot write to file")


    # --- CASE B: Remove lyrics (.lrc) ---
    elif remove_lyrics and filepath.exists():
        logger.verbose(f"[Lyrics] Removing lyrics (.lrc) for '{title}'")
        try:
            success = remove_lyrics_from_mp3(filepath, error, test_run)
            if success:
                update_fields["remove_lyrics"] = False
                if info: fprint(progress_prefix, f"Lyrics removed from ?", title)
                logger.info(f"[Lyrics] Lyrics removed from '{title}'")
            else:
                if error: print(f"\nFailed to remove lyrics for '{title}'")
                logger.error(f"[Lyrics] Failed to remove lyrics for '{title}'")
        except Exception as e:
            if error: print(f"\nError removing lyrics from '{video_id}': {e}")
            logger.error(f"[Lyrics] Error removing lyrics from '{video_id}': {e}")

    # --- CASE C: File missing ---
    elif not filepath.exists():
        logger.error(f"[Lyrics] File missing -> cannot do anything: '{filepath}'")


    if update_fields:
        update_video_db(
            video_id,
            update_fields,
            cur,
            conn,
            test_run
        )



    return time.time() - start_processing
