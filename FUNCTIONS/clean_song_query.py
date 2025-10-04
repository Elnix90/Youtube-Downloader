import re
import unicodedata

from CONSTANTS import UNWANTED_PATTERNS_FILE
from FUNCTIONS.HELPERS.logger import setup_logger
from FUNCTIONS.HELPERS.text_helpers import load_patterns

logger = setup_logger(__name__)


def clean_song_query(query: str) -> str:
    old_query = query
    """Normalize and clean a song query string"""
    query = query.lower()

    # Normalize accents: à, é, ê -> a, e, e
    query = unicodedata.normalize('NFKD', query)
    query = query.encode('ASCII', 'ignore').decode('ascii')

    # Remove unwanted patterns first
    patterns_to_remove: set[str] = load_patterns(file=UNWANTED_PATTERNS_FILE)
    for pattern in patterns_to_remove:
        if pattern.startswith("re:"):
            # Handle regex pattern
            regex = pattern[3:].strip()
            query = re.sub(regex, '', query, flags=re.IGNORECASE)
        else:
            # Handle plain word/phrase pattern
            query = re.sub(
                rf"\b{re.escape(pattern)}\b", '', query, flags=re.IGNORECASE
            )

    # Remove "feat ..." or "ft ..." with the artist name
    query = re.sub(r'\b(feat|ft)\.? [\w\s]+', '', query, flags=re.IGNORECASE)

    # Remove anything that's not a-z, A-Z, 0-9, space, apostropthy, or hyphen
    query = re.sub(r"[^a-zA-Z0-9\s'-]", '', query)

    # Remove hyphens surrounded by spaces
    # query = re.sub(r'\s*-\s*', ' ', query)

    # Collapse multiple spaces and strip edges
    query = re.sub(r'\s+', ' ', query).strip()

    # Capitalize words
    query = query.title()

    logger.verbose(f"[Clean Song Query] Cleaned '{old_query}' to '{query}'")
    return query
