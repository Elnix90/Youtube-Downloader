"""
Modules that contains compute_tags and compute_albums functions
"""

from typing import Literal

from CONSTANTS import PRIVATE_PATTERNS_FILE, TAGS_DIR, TRUSTED_ARTISTS_FILE
from FUNCTIONS.HELPERS.logger import setup_logger
from FUNCTIONS.HELPERS.tag_helpers import (
    compute_tag_set_from_file,
    matches_patterns,
)
from FUNCTIONS.HELPERS.text_helpers import load_patterns, sanitize_text

logger = setup_logger(__name__)


def compute_tags(title: str, uploader: str) -> set[str]:
    """
    Computes tags from a title and a uploadern,
    Iterates through all files in TAGS_DIR and read their content
    if a matching tag is found in the title or uploader name, the tag
    is added to the set that is retured
    """
    tags: set[str] = set()

    if not TAGS_DIR.exists() or not TAGS_DIR.is_dir():
        logger.warning(
            f"[Compute Tags] Tags directory '{TAGS_DIR}'"
            + "doesn't exist or is a file"
        )
        return tags

    # Normalize inputs
    title_norm = sanitize_text(title).lower()
    uploader_norm = sanitize_text(uploader).lower()

    for tag_file in TAGS_DIR.glob("*.txt"):
        tag_name, should_add = compute_tag_set_from_file(
            (title_norm, uploader_norm), tag_file
        )

        if tag_name and should_add:
            tags.add(tag_name)
            logger.debug(f"[Compute Tags] Added '{tag_name}'")

    logger.info(
        "[Compute Tags] Computed "
        + f"{len(tags)} tag{'s' if len(tags) != 1 else ''}"
        + f"from '{title} {uploader}' : {tags}"
    )
    return tags


def compute_album(title: str, uploader: str) -> str:
    """Decide album: Public or Private"""
    title_norm = sanitize_text(title)
    uploader_norm = sanitize_text(uploader)

    public_patterns = load_patterns(file=TRUSTED_ARTISTS_FILE)
    private_patterns = load_patterns(file=PRIVATE_PATTERNS_FILE)

    album: Literal["Private", "Public"] = "Private"

    if matches_patterns(title_norm, public_patterns) or matches_patterns(
        uploader_norm, public_patterns
    ):
        album = "Public"
        logger.verbose(
            f"[Compute Album] Matched public pattern for '{title} {uploader}'"
        )

    if matches_patterns(title_norm, private_patterns) or matches_patterns(
        uploader_norm, private_patterns
    ):
        logger.verbose(
            f"[Compute Album] Matched private pattern for '{title} {uploader}'"
        )
        return "Private"

    if album == "Private":
        logger.verbose(
            "[Compute Album] No public match, defaulted to 'Private' for"
            + f"'{title} {uploader}'"
        )

    return album
