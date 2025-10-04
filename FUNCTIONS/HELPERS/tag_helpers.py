"""
Tag computation utilities.

This module provides functions to determine whether a given title or
uploader name matches specific tag patterns, as defined in pattern files.
Patterns may be literal words or regular expressions.
"""

from __future__ import annotations

import re
from pathlib import Path

from FUNCTIONS.HELPERS.text_helpers import (
    contains_whole_word,
    load_patterns,
    sanitize_text,
)


def matches_patterns(text: str, patterns: set[str]) -> bool:
    """
    Check whether any pattern (regex or keyword) matches the provided text.

    Args:
        text: The text to test against patterns.
        patterns: A set of string patterns. Patterns beginning with
            "re:" are treated as regular expressions; others are treated
            as plain words.

    Returns:
        True if at least one pattern matches, otherwise False.
    """
    for pat in patterns:
        if pat.startswith("re:"):
            regex: str = pat[3:].strip()
            if re.search(regex, text, flags=re.IGNORECASE):
                return True
        else:
            word: str = sanitize_text(pat)
            if word and contains_whole_word(text=text, word=word):
                return True
    return False


def compute_tag_set_from_file(
    texts: tuple[str, str],
    tag_file_path: Path,
) -> tuple[str | None, bool]:
    """
    Determine whether a tag should be applied based on a tag pattern file.

    The pattern file can start with:
      - "tag_" → positive tag patterns.
      - "notag_" → exclusion tag patterns.

    Args:
        texts: Tuple containing the normalized (title, uploader).
        tag_file_path: Path to the tag pattern file.

    Returns:
        A tuple of:
            - Tag name (or None if not applicable).
            - Boolean indicating whether the tag should be added.
    """
    title_norm, uploader_norm = texts
    filename = tag_file_path.stem
    patterns = load_patterns(file=tag_file_path)

    if filename.startswith("tag_"):
        tag_name: str = filename[len("tag_") :]
        add_tag: bool = False

        for line in patterns:
            negated: bool = line.startswith("-")
            pattern_line: str = line[1:].strip() if negated else line.strip()

            match_found: bool
            if pattern_line.startswith("re:"):
                regex: str = pattern_line[3:].strip()
                match_found = bool(
                    re.search(regex, title_norm)
                    or re.search(regex, uploader_norm)
                )
            else:
                match_found = bool(
                    contains_whole_word(title_norm, pattern_line)
                    or contains_whole_word(uploader_norm, pattern_line)
                )

            if match_found:
                add_tag = not negated
                break

        return tag_name, add_tag

    if filename.startswith("notag_"):
        tag_name = filename[len("notag_") :]
        present: bool = bool(
            matches_patterns(title_norm, set(patterns))
            or matches_patterns(uploader_norm, set(patterns))
        )
        return tag_name, not present  # add if not present

    return None, False
