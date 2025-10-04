"""
Helper module, contains some helper functions
used all across the project
"""

from datetime import datetime
from pathlib import Path
from typing import Literal, TypeAlias, TypedDict


class VideoInfo(TypedDict, total=False):
    """
    Types for VideoInfo dict
    """

    video_id: str
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
    syncedlyrics_query: str
    auto_subs: str
    try_lyrics_if_not: bool
    lyrics_retries: int

    update_thumbnail: bool
    remove_thumbnail: bool

    remove_lyrics: bool

    tags: list[str]
    recompute_tags: bool
    recompute_album: bool
    recompute_yt_info: bool

    remix_of: str
    recompute_remix_of: bool
    confidence: float

    filename: str
    status: Literal[0, 1, 2, 3]  # downloaded / unavailable / private / unknown
    reason: str  # Why download has failed

    date_added: float
    date_modified: float


VideoInfoKey = Literal[
    "video_id",
    "title",
    "thumbnail_url",
    "description",
    "channel_id",
    "channel_url",
    "view_count",
    "comment_count",
    "like_count",
    "uploader",
    "channel_follower_count",
    "uploader_id",
    "uploader_url",
    "upload_date",
    "duration",
    "duration_string",
    "removed_segments_int",
    "removed_segments_duration",
    "skips",
    "lyrics",
    "subtitles",
    "syncedlyrics",
    "syncedlyrics_query",
    "auto_subs",
    "try_lyrics_if_not",
    "lyrics_retries",
    "update_thumbnail",
    "remove_thumbnail",
    "remove_lyrics",
    "tags",
    "recompute_tags",
    "recompute_album",
    "recompute_yt_info",
    "remix_of",
    "recompute_remix_of",
    "confidence",
    "filename",
    "status",
    "reason",
    "date_added",
    "date_modified",
]


VideoInfoMap: TypeAlias = dict[str, VideoInfo]


class ExtractedInfo(TypedDict, total=False):
    """
    Type safe extracted infos from yt-dlp
    """

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
    "duration_string",
}


class Postprocessor(TypedDict, total=False):
    """
    Defines the types for Postprocessors args for yt_dlp type check
    """

    key: str
    preferredcodec: str
    preferredquality: str


class QuietLogger:
    """
    Used to shut yt-dlp and mannually handle errors or warnings
    """

    def debug(self, _msg: str) -> None:
        """
        Empty method to catch debug output of yt-dlp
        """

    def warning(self, _msg: str) -> None:
        """
        Empty method to catch warning output of yt-dlp
        """

    def error(self, _msg: str) -> None:
        """
        Empty method to catch error output of yt-dlp
        """


class YdlOpt(TypedDict, total=False):
    """
    Type safe options for yt-dlp download
    """

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
    http_headers: dict[str, str]
    extractor_args: dict[str, list[str]]
    fragment_retries: int
    retries: int

    writesubtitles: bool
    writeautomaticsub: bool
    subtitlesformat: str
    subtitleslangs: list[str]

    proxy: str


def lyrics_lrc_path_for_mp3(mp3_path: Path) -> Path:
    """Return the corresponding .lrc path for an mp3 Path"""
    return mp3_path.with_suffix(".lrc")


def thumbnail_png_path_for_mp3(mp3_path: Path) -> Path:
    """Return the corresponding .png path for an mp3 Path"""
    return mp3_path.with_suffix(".png")


def remove_data_from_video_info(
    data: VideoInfo, to_remove: list[str]
) -> VideoInfo:
    """
    Removes data passed in to_remove from a VideoInfo dict,
    returns the nex dict
    """
    for r in to_remove:
        if r in data:
            del data[r]
    return data


def timestamp_to_id3_unique(
    ts: float | int, include_time: bool = False
) -> str:
    """
    Convert a Unix timestamp to a unique, sortable string
    compatible with ID3-style date formats.

    Args:
        ts (float | int): Unix timestamp.
        include_time (bool): If True, include hours, minutes, and seconds.

    Returns:
        str: Date string in format 'YYYY-MM-DD' or 'YYYY-MM-DD_HH-MM-SS'.
    """
    dt = datetime.fromtimestamp(ts)
    if include_time:
        return dt.strftime("%Y-%m-%d_%H-%M-%S")
    else:
        return dt.strftime("%Y-%m-%d")


def normalize_skips(info: VideoInfo) -> VideoInfo:
    """
    Transforms skips from VideoInfo that can be list due to json parsing to
    real tuples for later iteration
    """
    if "skips" in info:
        info["skips"] = list(info["skips"])
        # info["skips"] = [(x, y) for x, y in info["skips"]]
    return info
