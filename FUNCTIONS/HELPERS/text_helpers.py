from pathlib import Path

import unicodedata
import re

from FUNCTIONS.HELPERS.logger import setup_logger
logger = setup_logger(__name__)






def sanitize_text(text: str) -> str:
    old_filename = text
    text = text or ""
    text = text.strip()

    # Normalize Unicode (NFKD decomposes accents/emoji)
    text = unicodedata.normalize("NFKD", text)

    # Remove accents/diacritics (keep base ASCII letters)
    text = "".join(
        c for c in text
        if not unicodedata.combining(c)
    )

    # Remove non-ASCII characters
    text = text.encode("ascii", "ignore").decode("ascii")

    # Remove filesystem-forbidden chars
    text = re.sub(r'[\\/:*?"<>|~.\x00-\x1F]', "", text)

    # Collapse spaces
    text = re.sub(r"\s+", " ", text)

    # Only allow safe characters: letters, digits, space, dash, underscore, parentheses, dot
    text = re.sub(r"[^A-Za-z0-9 _\-\(\).]", "", text)

    # Trim trailing dots/spaces again
    text = text.rstrip(". ").strip()

    logger.verbose(f"[Sanitize Filename] Sanitized '{old_filename}' to '{text}'")
    return text.title()





def load_patterns(file: Path) -> set[str]:
    """
    Load non-comment patterns from a file into a set
    """
    if not file.exists():
        return set()
    try:
        lines = file.read_text(encoding="utf-8").splitlines()
        patterns ={sanitize_text(line.strip()) for line in lines if line.strip() and not line.startswith("#") and not line.startswith("re:")}
        logger.verbose(f"[Load patterns] Sucessfully loaded {len(patterns)} patterns from '{file}'")
        return patterns
    except Exception as e:
        logger.error(f"[Compute Tags] Failed to load trusted artists: {e}")
        return set()




def contains_whole_word(text: str, word: str) -> bool:
    """
    Return True if `word` exists as a whole word inside `text`.
    Case-insensitive.
    """
    if not text or not word:
        return False
    pattern = r"\b" + re.escape(word) + r"\b"
    return re.search(pattern, text, flags=re.IGNORECASE) is not None
