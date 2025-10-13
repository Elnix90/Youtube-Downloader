"""
Helper module, contains some helper functions
used all across the project
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal, NotRequired, TypeAlias, TypedDict

from constants import ENTRY_ID_SEPARATOR

# ---------------------------------------------------------------------------
# TypedDict structures for YouTube API responses
# ---------------------------------------------------------------------------


class ThumbnailItem(TypedDict):
    """Represents a single thumbnail variant."""

    url: str
    width: int
    height: int


class Thumbnails(TypedDict, total=False):
    """Available thumbnails for a video."""

    default: ThumbnailItem
    medium: ThumbnailItem
    high: ThumbnailItem
    standard: ThumbnailItem
    maxres: ThumbnailItem


class Snippet(TypedDict, total=False):
    """YouTube snippet object inside a playlist item."""

    title: str
    description: str
    publishedAt: str
    playlistId: str
    position: int
    thumbnails: Thumbnails
    videoOwnerChannelTitle: str
    videoOwnerChannelId: str


class PlaylistItem(TypedDict, total=False):
    """Top-level playlist item from the YouTube API."""

    id: str
    snippet: Snippet
    status: dict[str, str]
    contentDetails: dict[str, str]


class VideoInfo(TypedDict, total=False):
    """
    Types for VideoInfo dict
    """

    entry_id: int

    position: int
    playlist_item_id: str
    playlist_id: str

    video_id: str
    title: str
    thumbnails: Thumbnails
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
    privacy_status: str

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
    "id",
    "position",
    "playlist_item_id",
    "playlist_id",
    "video_id",
    "title",
    "thumbnails",
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
    "privacy_status",
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


# ---------------------------------------------------------------------------
# Base info type for a single flat video item
# ---------------------------------------------------------------------------


class ExtractedInfo(TypedDict, total=False):
    """Type-safe representation of one video entry from yt-dlp."""

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


# ---------------------------------------------------------------------------
# Playlist extraction result (the dict returned by yt_dlp.extract_info)
# ---------------------------------------------------------------------------


class ExtractedPlaylistInfo(TypedDict):
    """Type-safe structure for yt-dlp playlist extraction result."""

    _type: NotRequired[str]
    id: NotRequired[str]
    title: NotRequired[str]
    uploader: NotRequired[str]
    extractor_key: NotRequired[str]
    extractor: NotRequired[str]
    entries: list[ExtractedInfo]


ExtractedInfoMap: TypeAlias = dict[str, ExtractedInfo]

# ---------------------------------------------------------------------------
# Dataclass model for internal use
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class PlaylistVideoEntry:
    """Strongly typed model for a YouTube playlist video entry."""

    playlist_item_id: str
    video_id: str
    playlist_id: str
    position: int
    upload_date: str
    title: str
    description: str
    thumbnails: Thumbnails
    video_owner_channel_title: str
    video_owner_channel_id: str
    privacy_status: str
    video_published_at: str

    # -----------------------------------------------------------------------
    # Builders
    # -----------------------------------------------------------------------

    @classmethod
    def from_api_response(
        cls,
        data: PlaylistItem,
    ) -> PlaylistVideoEntry:
        """
        Construct a PlaylistVideoEntry from a YouTube API response.
        Ensures type safety and defaults for missing fields.
        """
        snippet = data.get("snippet", {})
        content = data.get("contentDetails", {})
        status = data.get("status", {})
        thumbnails = snippet.get("thumbnails", {})

        return cls(
            playlist_item_id=str(data.get("id", "")),
            video_id=str(content.get("videoId", "")),
            playlist_id=str(snippet.get("playlistId", "")),
            position=int(snippet.get("position", 0)),
            upload_date=str(snippet.get("publishedAt", "")),
            title=str(snippet.get("title", "")),
            description=str(snippet.get("description", "")),
            thumbnails=thumbnails,
            video_owner_channel_title=str(snippet.get("videoOwnerChannelTitle", "")),
            video_owner_channel_id=str(snippet.get("videoOwnerChannelId", "")),
            privacy_status=str(status.get("privacyStatus", "")),
            video_published_at=str(content.get("videoPublishedAt", "")),
        )

    # -----------------------------------------------------------------------
    # Serializers
    # -----------------------------------------------------------------------

    def to_json(self) -> VideoInfo:
        """Return a serializable dictionary for JSON dumping."""
        return {
            "playlist_item_id": self.playlist_item_id,
            "video_id": self.video_id,
            "playlist_id": self.playlist_id,
            "position": self.position,
            "title": self.title,
            "description": self.description,
            "thumbnails": self.thumbnails,
            "uploader": self.video_owner_channel_title,
            "uploader_id": self.video_owner_channel_id,
            "privacy_status": self.privacy_status,
            "upload_date": self.video_published_at or self.upload_date,
        }


youtube_required_info = {
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
    Type-safe configuration for yt-dlp extraction/download.
    Mirrors the options supported by YoutubeDL(params=...).
    """

    # --- Output & file templates ---
    outtmpl: str | dict[str, str]
    cachedir: bool
    _screen_file: object  # for capturing yt-dlp screen output (e.g., io.StringIO)

    # --- General behavior ---
    quiet: bool
    no_warnings: bool
    noprogress: bool
    ignoreerrors: bool
    verbose: bool
    logger: QuietLogger

    # --- Proxy / network ---
    proxy: str | None
    retries: int
    fragment_retries: int
    http_headers: dict[str, str]

    # --- Subtitles ---
    writesubtitles: bool
    writeautomaticsub: bool
    subtitlesformat: str
    subtitleslangs: list[str]

    # --- Extraction / format ---
    format: str
    extract_flat: bool
    skip_download: bool
    extractor_args: dict[str, list[str]]

    # --- Postprocessing ---
    add_metadata: bool
    embed_metadata: bool
    postprocessors: list[dict[str, object]]
    postprocessor_args: list[str]

    # --- Authentication / cookies ---
    cookiesfrombrowser: tuple[str, ...]  # e.g., ("firefox",)
    cookiefile: str

    # --- Internal / custom extensions ---
    outtmpl_na_placeholder: str


def lyrics_lrc_path_for_mp3(mp3_path: Path) -> Path:
    """Return the corresponding .lrc path for an mp3 Path"""
    return mp3_path.with_suffix(".lrc")


def thumbnail_png_path_for_mp3(mp3_path: Path) -> Path:
    """Return the corresponding .png path for an mp3 Path"""
    return mp3_path.with_suffix(".png")


def remove_data_from_video_info(data: VideoInfo, to_remove: list[str]) -> VideoInfo:
    """
    Removes data passed in to_remove from a VideoInfo dict,
    returns the nex dict
    """
    for r in to_remove:
        if r in data:
            del data[r]
    return data


def timestamp_to_id3_unique(ts: float | int, include_time: bool = False) -> str:
    """
    Convert a Unix timestamp to a unique, sortable string
    compatible with ID3-style date formats.

    Args:
        ts (float | int): Unix timestamp.
        include_time (bool): If True, include hours, minutes, and seconds.

    Returns:
        str: Date string in format 'YYYY-MM-DD' or 'YYYY-MM-DD_HH-MM-SS'.
    """
    # If ts is in milliseconds, convert to seconds
    if ts > 1e12:  # simple heuristic
        ts = ts / 1000

    dt = datetime.fromtimestamp(ts)
    if include_time:
        return dt.strftime("%Y-%m-%d_%H-%M-%S")

    return dt.strftime("%Y-%m-%d")


def normalize_skips(info: VideoInfo) -> VideoInfo:
    """
    Transforms skips from VideoInfo that can be list due to json parsing to
    real tuples for later iteration
    """
    if "skips" in info:
        # info["skips"] = list(info["skips"])
        info["skips"] = [(x, y) for x, y in info["skips"]]
    return info


def now_unix() -> float:
    """Return current Unix timestamp as float for SQLite."""
    return time.time()


def has_entry_id_prefix(title: str, entry_id: str) -> bool:
    """Return True if title starts with '<entry_id>{SEP}' or equals entry_id."""
    if not title:
        return False
    return title == entry_id or title.startswith(f"{entry_id}{ENTRY_ID_SEPARATOR}")
