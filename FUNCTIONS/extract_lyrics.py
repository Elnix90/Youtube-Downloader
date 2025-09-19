import re
import unicodedata
import logging
import syncedlyrics

from CONSTANTS import UNWANTED_PATTERNS_FILE, REMIX_PATTERNS_FILE, TRUSTED_ARTISTS
from FUNCTIONS.fileops import load_patterns


from FUNCTIONS.helpers import contains_whole_word, sanitize_text
from logger import setup_logger
logger = setup_logger(__name__)

for noisy in ["syncedlyrics", "Musixmatch", "Lrclib", "NetEase", "Megalobiz", "Genius"]:
    logging.getLogger(noisy).disabled = True






def _clean_song_query(query: str) -> str:
    old_query = query
    """Normalize and clean a song query string"""
    query = query.lower()

    # Normalize accents: à, é, ê -> a, e, e
    query = unicodedata.normalize('NFKD', query)
    query = query.encode(encoding='ASCII', errors='ignore').decode(encoding='utf-8')

    # Remove unwanted patterns first
    patterns_to_remove: set[str] = load_patterns(file=UNWANTED_PATTERNS_FILE)
    for pattern in patterns_to_remove:
        query = re.sub(rf"\b{pattern}\b", '', query, flags=re.IGNORECASE)

    # Remove anything that's not a-z, A-Z, 0-9, space, or hyphen
    query = re.sub(r"[^a-zA-Z0-9\s\'\-]", '', query)

    # Remove hyphens surrounded by spaces
    query = re.sub(r'\s*-\s*', ' ', query)

    # Collapse multiple spaces and strip edges
    query = re.sub(r'\s+', ' ', query).strip()

    # Capitalize words
    logger.info(f"[Clean Song Query] Cleaned '{old_query}' to '{query}'")
    return query.title()







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
        logger.debug("[Get Lyrics] Removed artist from query due to unwanted pattern found")


    # Sometimes the artist is already in the title, so ignore it to avoid duplicates
    if artist in title:
        song_query = title
        logger.debug("[Get Lyrics] Removed artist from query cause it is in the title (using only title)")


    # Add the trusted artist to the query if found in the title
    trusted_artists: set[str] = load_patterns(file=TRUSTED_ARTISTS)
    for trusted_artist in trusted_artists:
        if contains_whole_word(text=sanitize_text(text=title), word=trusted_artist) and not contains_whole_word(text=sanitize_text(text=title), word=artist):
            song_query = title +trusted_artist
            logger.debug("[Get Lyrics] Used title + trusted artist as song query")


    query: str = _clean_song_query(query=song_query)
    lyrics: str | None = syncedlyrics.search(query)

    logger.info(f"[Get Lyrics] {'Sucessfully got' if lyrics else "Failed to get"} lyrics for '{orig_artist}' by '{orig_title}' with query '{query}'")
    return lyrics, query