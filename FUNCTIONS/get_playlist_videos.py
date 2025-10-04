from pathlib import Path

import yt_dlp
from googleapiclient.discovery import Resource  # type: ignore[import-untyped]
from googleapiclient.errors import HttpError
from yt_dlp.utils import DownloadError  # type: ignore[attr-defined]

from FUNCTIONS.get_creditentials import get_authenticated_service
from FUNCTIONS.HELPERS.fileops import handler
from FUNCTIONS.HELPERS.fprint import fprint
from FUNCTIONS.HELPERS.logger import setup_logger
from FUNCTIONS.HELPERS.types_playlist import PlaylistVideoEntry

logger = setup_logger(__name__)


def get_playlist_ids_with_ytdlp(url: str) -> tuple[int, list[str] | None]:
    """Fetch video IDs from a playlist using yt_dlp."""
    ydl_opts: dict[str, object] = {"extract_flat": True, "quiet": True}
    try:
        with yt_dlp.YoutubeDL(
            ydl_opts
        ) as ydl:  # pyright: ignore[reportArgumentType]
            info: dict[str, object] = ydl.extract_info(
                url, download=False
            )  # pyright: ignore[reportAssignmentType]
            entries = info.get("entries")

            if not isinstance(entries, list):
                return 1, None

            ids: list[str] = [
                entry["id"]
                for entry in entries  # pyright: ignore[reportUnknownVariableType]
                if isinstance(entry, dict)
                and isinstance(
                    entry.get("id"), str
                )  # pyright: ignore[reportUnknownMemberType]
            ]
            return 0, ids

    except DownloadError as e:
        if "This playlist is private" in str(e):
            return 1, None
        return 2, None
    except Exception:
        return 2, None


def is_special_playlist(playlist_id: str) -> bool:
    """Detect special/system playlists."""
    return playlist_id.startswith(
        ("LL", "WL", "HL", "LM", "RD", "FEmusic_liked")
    )


def fetch_playlist_videos(
    playlist_id: str,
    file: Path,
    test_run: bool,
    clean: bool = False,
    info: bool = True,
    error: bool = True,
) -> None:
    """Fetch playlist videos (yt-dlp → fallback OAuth) and save as JSON."""
    if info:
        fprint(
            "",
            f"[Fetching videos] Fetching videos from playlist '{playlist_id}'",
        )
    logger.info(
        f"[Fetching videos] Fetching videos from playlist '{playlist_id}'"
    )

    if clean or not file.exists():
        all_videos: list[PlaylistVideoEntry] = []

        if not is_special_playlist(playlist_id):
            status, ids = get_playlist_ids_with_ytdlp(
                f"https://www.youtube.com/playlist?list={playlist_id}"
            )
            if status == 0 and ids:
                all_videos = [
                    PlaylistVideoEntry(
                        playlist_item_id="",
                        video_id=vid_id,
                        playlist_id=playlist_id,
                        position=0,
                        published_at="",
                        title="",
                        description="",
                        thumbnails={},
                        video_owner_channel_title="",
                        video_owner_channel_id="",
                        privacy_status="",
                        video_published_at="",
                        note="",
                    )
                    for vid_id in ids
                ]
                handler.dump(all_videos, file)
                logger.info(
                    f"[Fetching videos] {len(all_videos)} videos found in playlist '{playlist_id}'"
                )
                return
            elif info:
                fprint(
                    "",
                    f"[Fetching videos] yt_dlp failed (status {status}), falling back to OAuth",
                )

        youtube: Resource = get_authenticated_service(info=info)
        next_page_token: str | None = None

        while True:
            try:
                request = youtube.playlistItems().list(  # type: ignore[attr-defined]  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue, reportUnknownVariableType]
                    part="snippet,contentDetails,status",
                    playlistId=playlist_id,
                    maxResults=50,
                    pageToken=next_page_token,
                )
                response: dict[str, object] = (
                    request.execute()
                )  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
                items = response.get(
                    "items"
                )  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]

                if not isinstance(items, list):
                    break

                for (
                    item
                ) in items:  # pyright: ignore[reportUnknownVariableType]
                    if isinstance(item, dict):
                        all_videos.append(
                            PlaylistVideoEntry.from_api_response(item)
                        )  # pyright: ignore[reportUnknownArgumentType]
                        if info:
                            fprint(
                                "",
                                f"[Fetching videos] {len(all_videos)} videos fetched...",
                            )

                token = response.get(
                    "nextPageToken"
                )  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
                next_page_token = (
                    str(token) if isinstance(token, str) else None
                )

                if not next_page_token:
                    break

            except HttpError as e:
                logger.error(f"HTTP Error: {e}")
                if error:
                    fprint("", f"[Fetching videos] Error: {e}")
                if "quotaExceeded" in str(e):
                    raise RuntimeError(
                        "Quota exceeded, please retry later."
                    ) from e
                raise

        if not test_run:
            handler.dump(all_videos, file)
        logger.info(
            f"[Fetching videos] {len(all_videos)} videos written to '{file}'"
        )

    else:
        videos = handler.load(file)
        logger.info(
            f"[Fetching videos] {len(videos)} cached videos loaded from '{file}'"
        )
        if info:
            fprint(
                "", f"[Fetching videos] Loaded {len(videos)} cached videos."
            )
