"""
Text helper utilities.

Provides functions for sanitizing text (e.g., filenames),
loading word or regex patterns from files, and detecting
whole-word matches within text.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from FUNCTIONS.HELPERS.logger import setup_logger

logger = setup_logger(__name__)


def sanitize_text(text: str) -> str:
    """
    Sanitize a text string by removing unsafe characters and accents.

    Args:
        text: The raw text to sanitize.

    Returns:
        A cleaned and title-cased string safe for use in filenames
        or text comparison.
    """
    original: str = text
    text = (text or "").strip()

    # Normalize Unicode (NFKD decomposes accents and emoji)
    text = unicodedata.normalize("NFKD", text)

    # Remove accents/diacritics (keep ASCII base letters)
    text = "".join(c for c in text if not unicodedata.combining(c))

    # Remove non-ASCII characters
    text = text.encode("ascii", "ignore").decode("ascii")

    # Remove forbidden filesystem characters
    text = re.sub(r'[\\/:*?"<>|~.\x00-\x1F]', "", text)

    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text)

    # Allow only safe characters
    text = re.sub(r"[^A-Za-z0-9 _\-\(\).]", "", text)

    # Trim trailing dots/spaces again
    text = text.rstrip(". ").strip()

    logger.verbose(f"[Sanitize] '{original}' → '{text}'")
    return text.title()


def load_patterns(file: Path) -> set[str]:
    """
    Load non-comment patterns from a file into a set.

    Each non-empty line that is not a comment ('#') or regex
    directive ('re:') is cleaned with `sanitize_text` and added.

    Args:
        file: Path to the file containing patterns.

    Returns:
        A set of sanitized string patterns.
    """
    if not file.exists():
        return set()

    try:
        lines: list[str] = file.read_text(encoding="utf-8").splitlines()

        patterns: set[str] = {
            sanitize_text(line.strip())
            for line in lines
            if (
                line.strip()
                and not line.startswith("#")
                and not line.startswith("re:")
            )
        }

        logger.verbose(
            f"[Load Patterns] Loaded {len(patterns)} "
            + f"patterns from '{file}'"
        )
        return patterns

    except (OSError, UnicodeDecodeError, ValueError) as exc:
        logger.error(f"[Load Patterns] Failed to load '{file}': {exc}")
        return set()


def contains_whole_word(text: str, word: str) -> bool:
    """
    Determine if a whole word appears in the provided text.

    Args:
        text: The text to search within.
        word: The target word to look for.

    Returns:
        True if `word` exists as a whole word inside `text`
        (case-insensitive), otherwise False.
    """
    if not text or not word:
        return False

    pattern: str = rf"\b{re.escape(word)}\b"
    return bool(re.search(pattern, text, flags=re.IGNORECASE))
