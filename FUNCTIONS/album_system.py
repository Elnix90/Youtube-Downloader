import re
from pathlib import Path
from typing import Literal

from FUNCTIONS.fileops import load_patterns
from FUNCTIONS.helpers import sanitize_text, contains_whole_word
from FUNCTIONS.metadata import write_id3_tag
from logger import setup_logger

logger = setup_logger(__name__)

from CONSTANTS import TRUSTED_ARTISTS_FILE, PRIVATE_PATTERNS_FILE





def compute_album(title: str, uploader: str) -> str:
    """
    Decide album: "Public" or "Private" (default).
    Uses normalized text and regex/keyword patterns from files.
    """

    title_norm = sanitize_text(text=title)
    uploader_norm = sanitize_text(text=uploader)

    # Load patterns
    public_patterns: set[str] = load_patterns(file=TRUSTED_ARTISTS_FILE)
    private_patterns: set[str] = load_patterns(file=PRIVATE_PATTERNS_FILE)

    album: Literal["Private","Public"] = "Private"
    # Public detection
    for pat in public_patterns:
        if pat.startswith("re:"):
            pattern = pat[3:].strip()
            if re.search(pattern, title_norm) or re.search(pattern, uploader_norm):
                logger.verbose(f"[Compute Album] Matched public pattern '{pat}' for '{title} {uploader}'")
                album = "Public"
                break
        else:
            word = sanitize_text(pat)
            if word and (contains_whole_word(text=title_norm, word=word) or contains_whole_word(text=uploader_norm, word=word)):
                logger.verbose(f"[Compute Album] Matched public keyword '{word}' for '{title} {uploader}'")
                album = "Public"
                break

    # Private detection (optional, otherwise default)
    for pat in private_patterns:
        if pat.startswith("re:"):
            pattern = pat[3:].strip()
            if re.search(pattern, title_norm) or re.search(pattern, uploader_norm):
                logger.verbose(f"[Compute Album] Matched private pattern '{pat}' for '{title} {uploader}'")
                return "Private"
        else:
            word = sanitize_text(pat)
            if word and (contains_whole_word(text=title_norm, word=word) or contains_whole_word(text=uploader_norm, word=word)):
                logger.verbose(f"[Compute Album] Matched private keyword '{word}' for '{title} {uploader}'")
                return "Private"

    if album =="Private":
        logger.verbose(f"[Compute Album] No match, defaulted to 'Private' for '{title} {uploader}'")
    return album






def set_album(
    filepath: Path,
    album: str,
    test_run: bool = False
) -> bool:
    """
    Embed album info into MP3 file and update DB flag `update_album`.
    """

    if not filepath.exists():
        logger.error(f"[Set Album] Filepath doesn't exist: '{filepath}'")
        return False

    success = write_id3_tag(filepath=filepath, frame_id="TALB", data=album, test_run=test_run)
    if success:
        logger.verbose(f"[Set Album] Album set to '{album}' for '{filepath}'")
        return True
    else:
        logger.error(f"[Set Album] Failed to set album '{album}' for '{filepath}'")
        return False
