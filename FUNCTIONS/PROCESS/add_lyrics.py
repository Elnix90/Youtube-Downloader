"""
This module processes lyrics for individual video files.
It can fetch, embed, or remove lyrics from .lrc files,
and update the database accordingly.
"""

from pathlib import Path
from sqlite3 import Connection, Cursor
import time

from FUNCTIONS.HELPERS.fprint import fprint
from FUNCTIONS.HELPERS.helpers import VideoInfo
from FUNCTIONS.sql_requests import update_video_db, get_video_info_from_db
from FUNCTIONS.lyrics import embed_lyrics_into_mp3, remove_lyrics_from_mp3, has_lyrics
from FUNCTIONS.extract_lyrics import get_lyrics_from_syncedlyrics
from FUNCTIONS.HELPERS.logger import setup_logger
from CONSTANTS import MAX_LYRICS_RETRIES

logger = setup_logger(__name__)


def process_lyrics_for_video(
    uploader: str,
    try_lyrics_if_not: bool,
    remove_lyrics: bool,
    lyrics_retries: int,
    title: str,
    subtitles: str | None,
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
    Process lyrics for a video file:
      - Fetch lyrics from YouTube or synced sources
      - Embed lyrics into a .lrc file
      - Remove lyrics if requested
      - Handle remix videos
      - Update database metadata

    Returns:
        Time in seconds spent processing the lyrics
    """
    start_time: float = time.time()
    lyrics_file_path: Path = filepath.with_suffix(".lrc")
    file_lyrics: str | None = has_lyrics(mp3_path=filepath)
    lyrics: str | None = None
    remix_lyrics: str | None = None
    orig_duration: int | None = None
    update_fields: VideoInfo = {}
    reached_max_retries: bool = lyrics_retries > MAX_LYRICS_RETRIES

    if reached_max_retries:
        update_fields["try_lyrics_if_not"] = False

    # --- Handle remixes ---
    if remix_of:
        logger.info(f"[Lyrics] Video '{video_id}' is a remix of '{remix_of}'")
        remix_info: VideoInfo = get_video_info_from_db(video_id=remix_of, cur=cur)
        remix_lyrics = remix_info.get("subtitles") or remix_info.get("syncedlyrics") or remix_info.get("auto_subs")
        orig_duration = remix_info.get("duration")

    # --- CASE A: Fetch or update lyrics ---
    if not remove_lyrics:
        if info:
            fprint(progress_prefix, "Processing lyrics for ?", title)
        logger.info(f"[Lyrics] Processing lyrics for '{title}'")

        embed_lyrics_into_file: bool = recompute_lyrics

        # Handle remix lyrics embedding
        if remix_of and remix_lyrics:
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
                    if info:
                        fprint(
                            progress_prefix,
                            f"Lyrics created from remix '{remix_of}' for ?",
                            title
                        )
                    logger.info(
                        f"[Lyrics] Lyrics created from remix '{remix_of}' for '{title}'"
                        )
                else:
                    if error:
                        print(f"\nFailed to write remix lyrics .lrc for '{title}'")
                    logger.error(f"[Lyrics] Failed to write remix lyrics .lrc for '{title}'")
            except Exception as e:
                if error:
                    print(f"\nError updating remix lyrics for '{title}': {e}")
                logger.error(f"[Lyrics] Error updating remix lyrics for '{title}': {e}")

        # Skip processing if max retries reached
        elif reached_max_retries and not recompute_lyrics:
            pass

        # Use existing file lyrics if available and recompute not forced
        elif file_lyrics and not recompute_lyrics:
            lyrics = file_lyrics
            if info:
                fprint(progress_prefix, "OK, no update needed for ?", title)
            logger.info(f"[Lyrics] OK, no update needed for '{lyrics_file_path.name}'")

        # Attempt to fetch lyrics
        elif try_lyrics_if_not or recompute_lyrics:
            logger.debug(f"[Lyrics] Trying to fetch lyrics for '{filepath}'")
            lyrics = file_lyrics if file_lyrics and not recompute_lyrics else None
            embed_lyrics_into_file = recompute_lyrics or lyrics is not None

            if lyrics is None:
                if subtitles:
                    lyrics = subtitles
                else:
                    if title and uploader:
                        lyrics, query = get_lyrics_from_syncedlyrics(title, uploader)
                        if lyrics is None and auto_subs:
                            lyrics = auto_subs
                        elif lyrics is not None:
                            update_fields["syncedlyrics_query"] = query
                            update_fields["syncedlyrics"] = lyrics

                if lyrics:
                    embed_lyrics_into_file = True
                else:
                    if info:
                        fprint(progress_prefix, "No lyrics found for ? by ?", title, uploader)
                    logger.info(f"[Lyrics] No lyrics found for '{title}' by '{uploader}'")
                    embed_lyrics_into_file = False

                update_fields["lyrics_retries"] = lyrics_retries + 1

        if embed_lyrics_into_file and lyrics:
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
                    if info:
                        fprint(progress_prefix, "Lyrics updated for ?", title)
                    logger.info(f"[Lyrics] Lyrics updated for '{title}'")
                else:
                    if error:
                        print(f"\nFailed to write lyrics .lrc for '{title}'")
                    logger.error(f"[Lyrics] Failed to write lyrics .lrc for '{title}'")
            except Exception as e:
                if error:
                    print(f"\nError updating lyrics for '{title}': {e}")
                logger.error(f"[Lyrics] Error updating lyrics for '{title}'")
        elif embed_lyrics_into_file:
            logger.error("[Lyrics] Lyrics is None, cannot write to file")

    # --- CASE B: Remove lyrics ---
    elif remove_lyrics and filepath.exists():
        try:
            success = remove_lyrics_from_mp3(filepath, error, test_run)
            if success:
                update_fields["remove_lyrics"] = False
                if info:
                    fprint(progress_prefix, "Lyrics removed from ?", title)
                logger.info(f"[Lyrics] Lyrics removed from '{title}'")
            else:
                if error:
                    print(f"\nFailed to remove lyrics for '{title}'")
                logger.error(f"[Lyrics] Failed to remove lyrics for '{title}'")
        except Exception as e:
            if error:
                print(f"\nError removing lyrics from '{video_id}': {e}")
            logger.error(f"[Lyrics] Error removing lyrics from '{video_id}'")

    # --- CASE C: File missing ---
    elif not filepath.exists():
        logger.error(f"[Lyrics] File missing -> cannot do anything: '{filepath}'")

    # --- Update DB ---
    if update_fields:
        update_video_db(video_id, update_fields, cur, conn, test_run)

    return time.time() - start_time
