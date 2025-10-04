from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict

# --- TypedDict structures for YouTube API responses ---


class ThumbnailItem(TypedDict):
    url: str
    width: int
    height: int


class Thumbnails(TypedDict, total=False):
    default: ThumbnailItem
    medium: ThumbnailItem
    high: ThumbnailItem
    standard: ThumbnailItem
    maxres: ThumbnailItem


class Snippet(TypedDict, total=False):
    title: str
    description: str
    publishedAt: str
    playlistId: str
    position: int
    thumbnails: Thumbnails
    videoOwnerChannelTitle: str
    videoOwnerChannelId: str


class PlaylistItem(TypedDict, total=False):
    id: str
    snippet: Snippet
    status: dict[str, str]
    contentDetails: dict[str, str]


# --- Dataclass model for internal use ---


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

    @classmethod
    def from_api_response(cls, data: dict[str, object]) -> PlaylistVideoEntry:
        """Construct from an API response dictionary."""
        item = data

        snippet = item.get("snippet", {}) if isinstance(item.get("snippet"), dict) else {}  # pyright: ignore[reportUnknownVariableType]
        content_details = (  # pyright: ignore[reportUnknownVariableType]
            item.get("contentDetails", {}) if isinstance(item.get("contentDetails"), dict) else {}
        )
        status = item.get("status", {}) if isinstance(item.get("status"), dict) else {}  # pyright: ignore[reportUnknownVariableType]

        thumbnails = snippet.get("thumbnails", {})  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue, reportUnknownVariableType]
        if not isinstance(thumbnails, dict):
            thumbnails = {}

        return cls(
            playlist_item_id=str(item.get("id", "")),
            video_id=str(content_details.get("videoId", "")),  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType, reportAttributeAccessIssue]
            playlist_id=str(snippet.get("playlistId", "")),  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType, reportAttributeAccessIssue]
            position=int(snippet.get("position", 0)),  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType, reportAttributeAccessIssue]
            published_at=str(snippet.get("publishedAt", "")),  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType, reportAttributeAccessIssue]
            title=str(snippet.get("title", "")),  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType, reportAttributeAccessIssue]
            description=str(snippet.get("description", "")),  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType, reportAttributeAccessIssue]
            thumbnails=thumbnails,  # pyright: ignore[reportArgumentType]
            video_owner_channel_title=str(snippet.get("videoOwnerChannelTitle", "")),  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType, reportAttributeAccessIssue]
            video_owner_channel_id=str(snippet.get("videoOwnerChannelId", "")),  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType, reportAttributeAccessIssue]
            privacy_status=str(status.get("privacyStatus", "")),  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType, reportAttributeAccessIssue]
            video_published_at=str(content_details.get("videoPublishedAt", "")),  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType, reportAttributeAccessIssue]
            note=str(content_details.get("note", "")),  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType, reportAttributeAccessIssue]
        )

    def to_json(self) -> dict[str, object]:
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

