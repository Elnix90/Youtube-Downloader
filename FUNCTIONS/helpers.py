import time
import shutil
from typing import TypedDict, Literal
import unicodedata
import re
from pathlib import Path

from CONSTANTS import NOT_OVERLAP_FPRINT

from logger import setup_logger
logger = setup_logger(__name__)






class VideoInfo(TypedDict, total=False):
    video_id: str
    # id: int
    title: str
    thumbnail_url: str
    description: str
    channel_id: str
    channel_url: str
    view_count: int
    comment_count: int
    like_count: int
    uploader: str
    channel_follower_count: int
    uploader_id: str
    uploader_url: str
    upload_date: str
    duration: int
    duration_string: str

    removed_segments_int: int
    removed_segments_duration: float
    skips: list[tuple[float, float]]

    lyrics: str
    subtitles: str
    syncedlyrics: str
    auto_subs: str
    try_lyrics_if_not: bool
    lyrics_retries: int

    update_thumbnail: bool
    remove_thumbnail: bool

    remove_lyrics: bool

    tags: list[str]
    recompute_tags: bool
    recompute_album: bool

    remix_of: str

    filename: str
    status: Literal[0,1,2,3] # downloaded / unavailable / private / unknown
    reason: str # If the file is downloaded and fails this key is added with why it has failed

    date_added: int
    date_modified: int


VideoInfoMap = dict[str, VideoInfo]



class ExtractedInfo(TypedDict, total=False):
    id: str | None
    fulltitle: str | None
    title: str | None
    thumbnail: str | None
    description: str | None
    channel_id: str | None
    channel_url: str | None
    view_count: int | None
    comment_count: int | None
    like_count: int | None
    uploader: str | None
    channel_follower_count: int | None
    uploader_id: str | None
    uploader_url: str | None
    upload_date: str | None
    duration: int | None
    duration_string: str | None
    language: str | None
    language_code: str | None
    subtitles: dict[str, list[dict[str, str]]] | None
    automatic_captions: dict[str, list[dict[str, str]]] | None



youtube_required_info: set[str] = {
    "video_id",
    "title",
    "thumbnail_url",
    "channel_id",
    "channel_url",
    "duration",
    "uploader",
    "upload_date",
    "duration_string"
}


class Postprocessor(TypedDict, total=False):
    key: str
    preferredcodec: str
    preferredquality: str





class QuietLogger:
    def debug(self, msg: str) -> None:  # pyright: ignore[reportUnusedParameter]
        return None

    def warning(self, msg: str) -> None:  # pyright: ignore[reportUnusedParameter]
        return None

    def error(self, msg: str) -> None:  # pyright: ignore[reportUnusedParameter]
        return None





class Ydl_opt(TypedDict, total=False):
    outtmpl: dict[str, str]
    quiet: bool
    noprogress: bool
    no_warnings: bool
    ignoreerrors: bool
    logger: QuietLogger
    verbose: bool
    
    format: str
    postprocessor_args: list[str]
    add_metadata: bool
    embed_metadata: bool
    postprocessors: list[Postprocessor]
    # progress_hooks: list[Callable[[dict[str, Any]], None]]
    http_headers: dict[str, str]
    extractor_args: dict[str, list[str]]
    fragment_retries: int
    retries: int
    
    writesubtitles: bool
    writeautomaticsub: bool
    subtitlesformat: str
    subtitleslangs: list[str]






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

    logger.debug(f"[Sanitize Filename] Sanitized '{old_filename}' to '{text}'")
    return text.title()







def fprint(prefix: str, title: str, overwrite: bool = True,flush: bool = True) -> None:
    term_width: int = shutil.get_terminal_size(fallback=(80, 20)).columns
    max_len: int = term_width - len(prefix)
    if max_len < 1:
        max_len = 1
    if len(title) > max_len:
        title = title[:max_len-1] + "…"
        space_nb = 0
    else:
        space_nb = max_len - len(title)

    print(f"{'\r\033[K' if overwrite else ''}{prefix}{title}{' ' * space_nb}",end="" if not NOT_OVERLAP_FPRINT else "\n",flush=flush)







def wait(progress_prefix: str, eta_str: str, d: int = 0):
    if d:
        logger.info(f"[PAUSE] Pausing {d} seconds...")
        for i in range(d,-1,-1):
            fprint(progress_prefix + " | " + eta_str, f" | [WAIT] Waiting {i} seconds...")
            time.sleep(1)






def contains_whole_word(text: str, word: str) -> bool:
    """
    Return True if `word` exists as a whole word inside `text`.
    Case-insensitive.
    """
    if not text or not word:
        return False
    pattern = r"\b" + re.escape(word) + r"\b"
    return re.search(pattern, text, flags=re.IGNORECASE) is not None




def lyrics_lrc_path_for_mp3(mp3_path: Path) -> Path:
    """Return the corresponding .lrc path for an mp3 Path"""
    return mp3_path.with_suffix(".lrc")


def thumbnail_png_path_for_mp3(mp3_path: Path) -> Path:
    """Return the corresponding .png path for an mp3 Path"""
    return mp3_path.with_suffix(".png")




