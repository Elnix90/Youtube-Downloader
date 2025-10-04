"""
Strongly typed data models for YouTube playlist video entries.
Includes helpers for parsing API responses into dataclasses.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypedDict

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
    published_at: str
    title: str
    description: str
    thumbnails: Thumbnails
    video_owner_channel_title: str
    video_owner_channel_id: str
    privacy_status: str
    video_published_at: str
    note: str

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
            published_at=str(snippet.get("publishedAt", "")),
            title=str(snippet.get("title", "")),
            description=str(snippet.get("description", "")),
            thumbnails=thumbnails,
            video_owner_channel_title=str(
                snippet.get("videoOwnerChannelTitle", "")
            ),
            video_owner_channel_id=str(snippet.get("videoOwnerChannelId", "")),
            privacy_status=str(status.get("privacyStatus", "")),
            video_published_at=str(content.get("videoPublishedAt", "")),
            note=str(content.get("note", "")),
        )

    # -----------------------------------------------------------------------
    # Serializers
    # -----------------------------------------------------------------------

    def to_json(self) -> dict[str, Any]:  # pyright: ignore[reportExplicitAny]
        """Return a serializable dictionary for JSON dumping."""
        return {
            "playlist_item_id": self.playlist_item_id,
            "video_id": self.video_id,
            "playlist_id": self.playlist_id,
            "position": self.position,
            "published_at": self.published_at,
            "title": self.title,
            "description": self.description,
            "thumbnails": self.thumbnails,
            "video_owner_channel_title": self.video_owner_channel_title,
            "video_owner_channel_id": self.video_owner_channel_id,
            "privacy_status": self.privacy_status,
            "video_published_at": self.video_published_at,
            "note": self.note,
        }
