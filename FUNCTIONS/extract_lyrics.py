import re
import unicodedata
from typing import Set, Optional, Tuple
import logging

import syncedlyrics  # type: ignore

from CONSTANTS import UNWANTED_PATTERNS_FILE, REMIX_PATTERNS_FILE
from FUNCTIONS.fileops import load_patterns

for noisy in ["syncedlyrics", "Musixmatch", "Lrclib", "NetEase", "Megalobiz", "Genius"]:
    logging.getLogger(noisy).disabled = True



def clean_song_query(query: str) -> str:
    """Normalize and clean a song query string."""
    query = query.lower()

    # Normalize accents: à, é, ê -> a, e, e
    query = unicodedata.normalize('NFKD', query)
    query = query.encode('ASCII', 'ignore').decode('utf-8')

    # Remove unwanted patterns first
    patterns_to_remove: Set[str] = load_patterns(UNWANTED_PATTERNS_FILE)
    for pattern in patterns_to_remove:
        query = re.sub(rf"\b{pattern}\b", '', query, flags=re.IGNORECASE)

    # Remove anything that's not a-z, A-Z, 0-9, space, or hyphen
    query = re.sub(r"[^a-zA-Z0-9\s\'\-]", '', query)

    # Remove hyphens surrounded by spaces
    query = re.sub(r'\s*-\s*', ' ', query)

    # Collapse multiple spaces and strip edges
    query = re.sub(r'\s+', ' ', query).strip()

    # Capitalize words
    return query.title()


def get_lyrics_from_syncedlyrics(title: str, artist: str) -> Tuple[Optional[str], str]:
    """
    Try to fetch lyrics from syncedlyrics for the given song.
    Returns (lyrics or None, query used).
    """
    title = title.lower()
    artist = artist.lower()

    song_query: str = f"{title} {artist}"

    plain_only: bool = True


    # If a remix pattern is found, ignore the artist (to improve chances of getting correct lyrics)
    anti_lyrics: Set[str] = load_patterns(REMIX_PATTERNS_FILE)
    if any(anti.lower() in song_query for anti in anti_lyrics):
        song_query = title
        plain_only = False

    # Sometimes the artist is already in the title, so remove it to avoid duplicates
    if artist in title:
        title = title.replace(artist, "")
        song_query = title

    query: str = clean_song_query(song_query)


    lyrics: Optional[str] = syncedlyrics.search(query,plain_only=plain_only)

    if lyrics:
        return lyrics, query
    else: # Try without the artist
        query = clean_song_query(title)
        lyrics = syncedlyrics.search(query)
        return lyrics, query