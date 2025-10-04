"""
Lyrics processing module for individual videos.

This module fetches, embeds, or removes lyrics (.lrc) files for MP3s.
It also updates the database with lyrics status and metadata.
"""

from __future__ import annotations

import time
from pathlib import Path
from sqlite3 import Connection, Cursor

from CONSTANTS import MAX_LYRICS_RETRIES
from FUNCTIONS.extract_lyrics import get_lyrics_from_syncedlyrics
from FUNCTIONS.HELPERS.fprint import fprint
from FUNCTIONS.HELPERS.helpers import VideoInfo
from FUNCTIONS.HELPERS.logger import setup_logger
from FUNCTIONS.lyrics import (
    embed_lyrics_into_mp3,
    has_lyrics,
    remove_lyrics_from_mp3,
)
from FUNCTIONS.sql_requests import (
    get_video_info_from_db,
    update_video_db,
)

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
    recompute_lyrics: bool,
) -> float:
    """
    Process lyrics for a video file.

    Handles:
      - fetching or embedding lyrics into MP3
      - reusing remix lyrics
      - removing lyrics if requested
      - updating the SQL database

    Returns:
        float: seconds spent processing this file
    """
    start_time: float = time.time()

    lyrics_path = filepath.with_suffix(".lrc")
    file_lyrics: str | None = has_lyrics(mp3_path=filepath)
    lyrics: str | None = None
    remix_lyrics: str | None = None
    orig_duration: int | None = None
    update_fields: VideoInfo = {}

    reached_max_retries = lyrics_retries > MAX_LYRICS_RETRIES
    if reached_max_retries:
        update_fields["try_lyrics_if_not"] = False

    # ---------------------------------------------------------------
    # Handle remixes: reuse lyrics from the original video
    # ---------------------------------------------------------------
    if remix_of:
        logger.info(f"[Lyrics] '{video_id}' is a remix of '{remix_of}'")
        remix_info = get_video_info_from_db(video_id=remix_of, cur=cur)
        remix_lyrics = (
            remix_info.get("subtitles")
            or remix_info.get("syncedlyrics")
            or remix_info.get("auto_subs")
        )
        orig_duration = remix_info.get("duration")

    # ---------------------------------------------------------------
    # Case A: Fetch or update lyrics
    # ---------------------------------------------------------------
    if not remove_lyrics:
        if info:
            fprint(progress_prefix, "Processing lyrics for ?", title)
        logger.info(f"[Lyrics] Processing lyrics for '{title}'")

        embed_lyrics: bool = recompute_lyrics

        # --- Handle remix lyrics embedding ---
        if remix_of and remix_lyrics:
            _embed_remix_lyrics(
                filepath=filepath,
                remix_of=remix_of,
                remix_lyrics=remix_lyrics,
                duration=duration,
                skips=skips,
                orig_duration=orig_duration,
                info=info,
                error=error,
                test_run=test_run,
                progress_prefix=progress_prefix,
                title=title,
                update_fields=update_fields,
            )

        # --- Skip processing if max retries reached ---
        elif reached_max_retries and not recompute_lyrics:
            logger.debug("[Lyrics] Max retries reached, skipping fetch")

        # --- Use existing file lyrics ---
        elif file_lyrics and not recompute_lyrics:
            lyrics = file_lyrics
            if info:
                fprint(progress_prefix, "OK, no update needed for ?", title)
            logger.info(
                f"[Lyrics] OK, no update needed for '{lyrics_path.name}'"
            )

        # --- Attempt to fetch lyrics ---
        elif try_lyrics_if_not or recompute_lyrics:
            lyrics = _try_fetch_lyrics(
                title=title,
                uploader=uploader,
                subtitles=subtitles,
                auto_subs=auto_subs,
                recompute=recompute_lyrics,
                file_lyrics=file_lyrics,
                info=info,
                progress_prefix=progress_prefix,
                update_fields=update_fields,
            )

            if lyrics:
                embed_lyrics = True
            update_fields["lyrics_retries"] = lyrics_retries + 1

        # --- Embed lyrics into MP3 if available ---
        if embed_lyrics and lyrics:
            _embed_lyrics_to_mp3(
                filepath=filepath,
                lyrics=lyrics,
                duration=duration,
                skips=skips,
                orig_duration=orig_duration,
                info=info,
                error=error,
                title=title,
                test_run=test_run,
                progress_prefix=progress_prefix,
                update_fields=update_fields,
            )
        elif embed_lyrics and not lyrics:
            logger.error("[Lyrics] No lyrics to embed")

    # ---------------------------------------------------------------
    # Case B: Remove lyrics
    # ---------------------------------------------------------------
    elif remove_lyrics and filepath.exists():
        _remove_lyrics_from_file(
            filepath=filepath,
            video_id=video_id,
            title=title,
            info=info,
            error=error,
            test_run=test_run,
            progress_prefix=progress_prefix,
            update_fields=update_fields,
        )

    # ---------------------------------------------------------------
    # Case C: Missing file
    # ---------------------------------------------------------------
    elif not filepath.exists():
        logger.error(f"[Lyrics] Missing file: '{filepath}'")

    # ---------------------------------------------------------------
    # Update DB if necessary
    # ---------------------------------------------------------------
    if update_fields:
        update_video_db(video_id, update_fields, cur, conn, test_run)

    return time.time() - start_time


# -------------------------------------------------------------------
# Helper subroutines
# -------------------------------------------------------------------


def _embed_remix_lyrics(
    *,
    filepath: Path,
    remix_of: str,
    remix_lyrics: str,
    duration: int | None,
    skips: list[tuple[float, float]] | None,
    orig_duration: int | None,
    info: bool,
    error: bool,
    test_run: bool,
    progress_prefix: str,
    title: str,
    update_fields: VideoInfo,
) -> None:
    """Embed remix lyrics into a file."""
    try:
        success, lrcs = embed_lyrics_into_mp3(
            filepath=filepath,
            lyrics=remix_lyrics,
            test_run=test_run,
            file_duration=duration or 0,
            skips=skips,
            original_duration=orig_duration,
        )
        if success:
            update_fields["lyrics"] = lrcs
            if info:
                fprint(
                    progress_prefix,
                    f"Lyrics from remix '{remix_of}' for ?",
                    title,
                )
            logger.info(
                f"[Lyrics] Embedded remix lyrics from '{remix_of}' "
                + f"into '{title}'"
            )
        else:
            _log_error(
                f"Failed to write remix lyrics for '{title}'", error=error
            )
    except OSError as exc:
        _log_error(f"OS error embedding remix lyrics: {exc}", error=error)


def _try_fetch_lyrics(
    *,
    title: str,
    uploader: str,
    subtitles: str | None,
    auto_subs: str | None,
    recompute: bool,
    file_lyrics: str | None,
    info: bool,
    progress_prefix: str,
    update_fields: VideoInfo,
) -> str | None:
    """Fetch lyrics from available sources."""
    lyrics = file_lyrics if file_lyrics and not recompute else None
    if lyrics:
        return lyrics

    if subtitles:
        return subtitles

    lyrics, query = get_lyrics_from_syncedlyrics(title, uploader)
    if lyrics:
        update_fields["syncedlyrics_query"] = query
        update_fields["syncedlyrics"] = lyrics
        return lyrics

    if auto_subs:
        return auto_subs

    if info:
        fprint(progress_prefix, "No lyrics found for ? by ?", title, uploader)
    logger.info(f"[Lyrics] No lyrics found for '{title}' by '{uploader}'")
    return None


def _embed_lyrics_to_mp3(
    *,
    filepath: Path,
    lyrics: str,
    duration: int | None,
    skips: list[tuple[float, float]] | None,
    orig_duration: int | None,
    info: bool,
    error: bool,
    title: str,
    test_run: bool,
    progress_prefix: str,
    update_fields: VideoInfo,
) -> None:
    """Embed provided lyrics into an MP3 file."""
    try:
        success, lrcs = embed_lyrics_into_mp3(
            filepath=filepath,
            lyrics=lyrics,
            test_run=test_run,
            file_duration=duration or 0,
            skips=skips,
            original_duration=orig_duration,
        )
        if success:
            update_fields["lyrics"] = lrcs
            if info:
                fprint(progress_prefix, "Lyrics updated for ?", title)
            logger.info(f"[Lyrics] Lyrics updated for '{title}'")
        else:
            _log_error(
                f"Failed to write lyrics .lrc for '{title}'",
                error=error,
            )
    except OSError as exc:
        _log_error(
            f"OS error embedding lyrics: {exc}",
            error=error,
        )


def _remove_lyrics_from_file(
    *,
    filepath: Path,
    video_id: str,
    title: str,
    info: bool,
    error: bool,
    test_run: bool,
    progress_prefix: str,
    update_fields: VideoInfo,
) -> None:
    """Remove lyrics from a file and update DB fields."""
    try:
        success = remove_lyrics_from_mp3(filepath, error, test_run)
        if success:
            update_fields["remove_lyrics"] = False
            if info:
                fprint(progress_prefix, "Lyrics removed from ?", title)
            logger.info(f"[Lyrics] Lyrics removed from '{title}'")
        else:
            _log_error(f"Failed to remove lyrics for '{title}'", error=error)
    except OSError as exc:
        _log_error(
            f"OS error removing lyrics from '{video_id}': {exc}", error=error
        )


def _log_error(msg: str, *, error: bool) -> None:
    """Print and log an error message."""
    if error:
        print(f"\n{msg}")
    logger.error(msg)
