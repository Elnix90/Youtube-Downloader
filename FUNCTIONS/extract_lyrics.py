"""
Extracts lyrics either using ytmusicapi or syncedlyrics if no
manual subtitles provided
"""

from __future__ import annotations

import logging
from typing import TypedDict, cast

import syncedlyrics
from ytmusicapi import YTMusic

from CONSTANTS import REMIX_PATTERNS_FILE, TRUSTED_ARTISTS_FILE
from FUNCTIONS.HELPERS.logger import setup_logger
from FUNCTIONS.HELPERS.text_helpers import (
    clean_song_query,
    contains_whole_word,
    load_patterns,
    sanitize_text,
)

logger = setup_logger(__name__)


for noisy in [
    "syncedlyrics",
    "Musixmatch",
    "Lrclib",
    "NetEase",
    "Megalobiz",
    "Genius",
]:
    logging.getLogger(noisy).disabled = True


def get_lyrics_from_syncedlyrics(orig_title: str, orig_artist: str) -> tuple[str | None, str]:
    """
    Try to fetch lyrics from syncedlyrics for the given song.
    Returns (lyrics or None, query used).
    """
    title = orig_title.lower()
    artist = orig_artist.lower()

    song_query: str = f"{title} {artist}"

    # If a remix pattern is found, ignore the artist (to improve chances of getting correct lyrics)
    anti_lyrics: set[str] = load_patterns(REMIX_PATTERNS_FILE)
    if any(anti.lower() in song_query for anti in anti_lyrics):
        song_query = title
        logger.verbose("[Get Lyrics] Removed artist from query due to unwanted pattern found")

    # Sometimes the artist is already in the title, so ignore it to avoid duplicates
    if artist in title:
        song_query = title
        logger.verbose("[Get Lyrics] Removed artist from query cause it is in the title (using only title)")

    # Add the trusted artist to the query if found in the title
    trusted_artists: set[str] = load_patterns(file=TRUSTED_ARTISTS_FILE)
    for trusted_artist in trusted_artists:
        if contains_whole_word(text=sanitize_text(text=title), word=trusted_artist) and not contains_whole_word(
            text=sanitize_text(text=title), word=artist
        ):
            song_query = title + trusted_artist
            logger.verbose("[Get Lyrics] Used title + trusted artist as song query")

    query: str = clean_song_query(query=song_query)
    lyrics: str | None = syncedlyrics.search(query)

    logger.info(
        "[Get Lyrics] "
        + f"{'Sucessfully got' if lyrics else "Failed to get"} "
        + f"lyrics for '{orig_artist}' by '{orig_title}' with query '{query}'"
    )
    return lyrics, query


class LyricLine(TypedDict, total=False):
    """Type safe definition of a single synchronised lyric line."""
    text: str


class LyricsResponse(TypedDict, total=False):
    """Type safe definition of the lyrics returned by ytmusicapi."""
    lyrics: str | list[LyricLine]


def extract_lyrics_from_ytmusicapi(video_id: str) -> str | None:
    """
    Fetch and return the lyrics for a YouTube Music video if available.

    Args:
        video_id: The YouTube video ID.

    Returns:
        The lyrics text if found, otherwise None.
    """
    ytmusic = YTMusic()  # unauthenticated for public access

    try:
        # Step 1: get watch playlist metadata
        watch_data = ytmusic.get_watch_playlist(video_id)

        # Step 2: extract lyrics browseId (ensure it's a string)
        raw_browse = watch_data.get("lyrics") or watch_data.get("lyricsBrowseId")
        lyrics_browse_id = raw_browse if isinstance(raw_browse, str) else None

        if not lyrics_browse_id:
            logger.info(f"[Lyrics] No lyrics browseId found for {video_id}")
            return None

        # Step 3: fetch lyrics via browseId
        lyrics_raw = ytmusic.get_lyrics(lyrics_browse_id)

        # Safely cast
        lyrics_data = cast(LyricsResponse, cast(object, lyrics_raw))
        lyrics_field = lyrics_data.get("lyrics")

        # Handle both string and list forms
        if isinstance(lyrics_field, str):
            return lyrics_field.strip() or None

        if isinstance(lyrics_field, list):
            text = "\n".join(
                line.get("text", "")
                for line in lyrics_field
                if isinstance(line, dict)  # pyright: ignore[reportUnnecessaryIsInstance]
            ).strip()
            return text or None

        return None

    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.warning(f"[Lyrics] Failed to extract lyrics for {video_id}: {exc}")
        return None
