"""
fprint function, used to automaticliy and cleanly print
overlapping lines to have a beatiful console output
"""

import shutil

from CONSTANTS import OVERLAP_FPRINT
from FUNCTIONS.HELPERS.logger import setup_logger
from FUNCTIONS.HELPERS.text_helpers import sanitize_text

logger = setup_logger(__name__)


def fprint(
    prefix: str,
    title: str,
    *to_sanitize: str,
    overwrite: bool = True,
    flush: bool = True,
) -> None:
    """
    Print a formatted message with optional substitution of '?' placeholders
    by sanitized strings passed in *to_sanitize.
    """
    term_width: int = shutil.get_terminal_size(fallback=(80, 20)).columns
    max_len: int = term_width - len(prefix)
    if max_len < 1:
        max_len = 1

    # replace each "?" in title with a sanitized arg
    sanitized_title = title
    for value in to_sanitize:
        if "?" in sanitized_title:

            s_text: str = sanitize_text(value)
            if not s_text:
                s_text = "sanitized_name"

            sanitized_title = sanitized_title.replace("?", s_text, 1)
        else:
            logger.warning(
                "[fprint] '?' wasn't found in sanitised title "
                + f"'{sanitized_title}' for value '{value}'"
            )

    if len(sanitized_title) > max_len:
        sanitized_title = sanitized_title[: max_len - 1] + "…"
        space_nb = 0
    else:
        space_nb = max_len - len(sanitized_title)

    print(
        f"{'\r\033[K' if overwrite else ''}"
        + f"{prefix}"
        + f"{sanitized_title}"
        + f"{' ' * space_nb}",
        end="" if overwrite or OVERLAP_FPRINT else "\n",
        flush=flush,
    )
