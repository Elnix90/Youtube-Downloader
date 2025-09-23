
import logging
import syncedlyrics


from CONSTANTS import REMIX_PATTERNS_FILE, TRUSTED_ARTISTS_FILE
from FUNCTIONS.HELPERS.text_helpers import load_patterns, contains_whole_word, sanitize_text
from FUNCTIONS.clean_song_query import clean_song_query


from FUNCTIONS.HELPERS.logger import setup_logger
logger = setup_logger(__name__)


for noisy in ["syncedlyrics", "Musixmatch", "Lrclib", "NetEase", "Megalobiz", "Genius"]:
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
        if contains_whole_word(text=sanitize_text(text=title), word=trusted_artist) and not contains_whole_word(text=sanitize_text(text=title), word=artist):
            song_query = title +trusted_artist
            logger.verbose("[Get Lyrics] Used title + trusted artist as song query")


    query: str = clean_song_query(query=song_query)
    lyrics: str | None = syncedlyrics.search(query)

    logger.info(f"[Get Lyrics] {'Sucessfully got' if lyrics else "Failed to get"} lyrics for '{orig_artist}' by '{orig_title}' with query '{query}'")
    return lyrics, query