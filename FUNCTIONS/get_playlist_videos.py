"""
Fetch and cache YouTube playlist videos using yt_dlp or the YouTube Data API.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, cast

import yt_dlp
from googleapiclient.errors import HttpError
from yt_dlp.utils import DownloadError

from FUNCTIONS.get_creditentials import get_authenticated_service
from FUNCTIONS.HELPERS.fileops import dump, load
from FUNCTIONS.HELPERS.fprint import fprint
from FUNCTIONS.HELPERS.helpers import (
    ExtractedPlaylistInfo,
    PlaylistVideoEntry,
    VideoInfoMap,
    YdlOpt,
)
from FUNCTIONS.HELPERS.logger import setup_logger

logger = setup_logger(__name__)

# ---------------------------------------------------------------------------
# yt-dlp helpers
# ---------------------------------------------------------------------------


def get_playlist_with_ytdlp(
    url: str,
) -> tuple[int, VideoInfoMap | None]:
    """
    Fetch video IDs and titles from a public YouTube playlist using yt_dlp.

    Returns:
        (status_code, videos)
        - 0 → success
        - 1 → playlist private
        - 2 → other error
    """
    ydl_opts: YdlOpt = {
        "extract_flat": True,  # fetch only metadata, not full videos
        "quiet": True,
        "ignoreerrors": True,
        "skip_download": True,
    }

    try:
        with yt_dlp.YoutubeDL(
            ydl_opts  # pyright: ignore[reportArgumentType]
        ) as ydl:
            info: ExtractedPlaylistInfo = cast(
                ExtractedPlaylistInfo,
                cast(object, ydl.extract_info(url, download=False)),
            )
            entries = info["entries"]

            results: VideoInfoMap = {}
            for entry in entries:

                video_id = entry.get("id")
                title = entry.get("title")

                if not isinstance(video_id, str):
                    continue

                results[video_id] = {
                    "video_id": video_id,
                    "title": str(title or ""),
                }

            return 0, results

    except DownloadError as exc:
        if "This playlist is private" in str(exc):
            return 1, None
        return 2, None
    except Exception as exc:
        logger.exception(f"yt-dlp failed: {exc}")
        return 2, None


# ---------------------------------------------------------------------------
# Playlist helpers
# ---------------------------------------------------------------------------


def is_special_playlist(playlist_id: str) -> bool:
    """Detect if a playlist is a YouTube special/system playlist."""
    return playlist_id.startswith(
        ("LL", "WL", "HL", "LM", "RD", "FEmusic_liked")
    )


# ---------------------------------------------------------------------------
# Main fetcher
# ---------------------------------------------------------------------------


def fetch_playlist_videos(
    playlist_id: str,
    file_path: Path,
    test_run: bool,
    clean: bool = False,
    info: bool = True,
) -> None:
    """
    Fetch playlist videos using yt_dlp for public playlists,
    fallback to YouTube Data API for restricted ones.
    """
    if info:
        fprint("", f"[Fetching videos] Fetching playlist '{playlist_id}'")
    logger.info(f"[Fetching videos] Fetching playlist '{playlist_id}'")

    # -----------------------------------------------------------------------
    # 1️⃣ Try yt_dlp
    # -----------------------------------------------------------------------
    if clean or not file_path.exists():
        all_videos: VideoInfoMap = {}

        if not is_special_playlist(playlist_id):
            playlist_url = (
                f"https://www.youtube.com/playlist?list={playlist_id}"
            )
            status, videos = get_playlist_with_ytdlp(playlist_url)

            if status == 0 and videos:
                if not test_run:
                    dump(videos, file_path)

                msg = f"[Fetching videos] {len(videos)} videos saved (yt_dlp)"
                if info:
                    fprint("", msg)
                logger.info(msg)
                return

            if info:
                fprint(
                    "",
                    f"[Fetching videos] yt_dlp failed (status {status}), "
                    + "falling back to YouTube API.",
                )

        # -------------------------------------------------------------------
        # 2️⃣ Fallback: YouTube Data API
        # -------------------------------------------------------------------
        youtube = get_authenticated_service(info=info)
        next_page_token: str | None = None

        while True:
            try:
                request = youtube.playlistItems().list(  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportAttributeAccessIssue]
                    part="snippet,contentDetails,status",
                    playlistId=playlist_id,
                    maxResults=50,
                    pageToken=next_page_token,
                )

                # Explicitly cast API response
                response = cast(
                    dict[str, Any], request.execute()  # pyright: ignore[reportExplicitAny, reportUnknownMemberType]
                )
                items = cast(
                    list[dict[str, Any]], response.get("items", [])  # pyright: ignore[reportExplicitAny]
                )

                for item in items:
                    entry = PlaylistVideoEntry.from_api_response(item)
                    all_videos[entry.video_id] = entry.to_json()

                    if info:
                        fprint(
                            "",
                            f"[Fetching videos] {len(all_videos)} videos fetched...",
                        )

                next_page_token = cast(
                    str | None, response.get("nextPageToken")
                )
                if not isinstance(next_page_token, str):
                    break

                time.sleep(0.1)

            except HttpError as exc:
                logger.error(f"[Fetching videos] HTTP Error: {exc}")
                if "quotaExceeded" in str(exc):
                    raise RuntimeError(
                        "Quota exceeded, please retry later."
                    ) from exc
                raise

        if not test_run:
            dump(all_videos, file_path)

        logger.info(
            f"[Fetching videos] {len(all_videos)}"
            + f"videos written to '{file_path}'",
        )

    # -----------------------------------------------------------------------
    # 3️⃣ Use cached file if exists
    # -----------------------------------------------------------------------
    else:
        cached_videos = load(file_path)
        msg = (
            f"[Fetching videos] Loaded {len(cached_videos)}"
            + f"cached videos from '{file_path}'"
        )
        if info:
            fprint("", msg)
        logger.info(msg)
