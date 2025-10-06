"""
Extracts lyrics either using ytmusicapi or syncedlyrics if no
manual subtitles provided
"""

import logging
import syncedlyrics
from ytmusicapi import YTMusic

from CONSTANTS import REMIX_PATTERNS_FILE, TRUSTED_ARTISTS_FILE
from FUNCTIONS.clean_song_query import clean_song_query
from FUNCTIONS.HELPERS.logger import setup_logger
from FUNCTIONS.HELPERS.text_helpers import (
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


def get_lyrics_from_syncedlyrics(
    orig_title: str, orig_artist: str
) -> tuple[str | None, str]:
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
        logger.verbose(
            "[Get Lyrics] Removed artist from query due to unwanted pattern found"
        )

    # Sometimes the artist is already in the title, so ignore it to avoid duplicates
    if artist in title:
        song_query = title
        logger.verbose(
            "[Get Lyrics] Removed artist from query cause it is in the title (using only title)"
        )

    # Add the trusted artist to the query if found in the title
    trusted_artists: set[str] = load_patterns(file=TRUSTED_ARTISTS_FILE)
    for trusted_artist in trusted_artists:
        if contains_whole_word(
            text=sanitize_text(text=title), word=trusted_artist
        ) and not contains_whole_word(
            text=sanitize_text(text=title), word=artist
        ):
            song_query = title + trusted_artist
            logger.verbose(
                "[Get Lyrics] Used title + trusted artist as song query"
            )

    query: str = clean_song_query(query=song_query)
    lyrics: str | None = syncedlyrics.search(query)

    logger.info(
        "[Get Lyrics] "
        + f"{'Sucessfully got' if lyrics else "Failed to get"} "
        + f"lyrics for '{orig_artist}' by '{orig_title}' with query '{query}'"
    )
    return lyrics, query







from typing import Optional
from ytmusicapi import YTMusic
from FUNCTIONS.HELPERS.logger import setup_logger

logger = setup_logger(__name__)


def extract_lyrics_from_ytmusicapi(video_id: str) -> Optional[str]:
    """
    Fetch and return the lyrics for a YouTube Music video if available.

    Args:
        video_id: The YouTube video ID.

    Returns:
        The lyrics text if found, otherwise None.
    """
    try:
        # Initialize the YTMusic client (unauthenticated for public songs)
        ytmusic = YTMusic()

        # Step 1: Get song metadata (contains menuItems with lyrics endpoint)
        song_data: dict[str, object] = ytmusic.get_song(video_id)

        # Step 2: Extract the "browseId" for lyrics if it exists
        lyrics_browse_id = (
            song_data.get("microformat", {})
            .get("microformatDataRenderer", {})
            .get("urlCanonical")
        )

        # In reality, ytmusicapi provides a cleaner helper:
        lyrics_data = ytmusic.get_lyrics(song_data.get("videoId", video_id))
        if not lyrics_data:
            return None

        # Step 3: Extract text safely
        lyrics_field = lyrics_data.get("lyrics") if isinstance(lyrics_data, dict) else None

        if isinstance(lyrics_field, str):
            return lyrics_field

        # Sometimes it's a list of lyric lines → join them
        if isinstance(lyrics_field, list):
            return "\n".join(
                line.get("text", "") for line in lyrics_field if isinstance(line, dict)
            )

        return None

    except Exception as exc:
        logger.warning(f"Failed to extract lyrics for {video_id}: {exc}")
        return None
