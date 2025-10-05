"""
Fetch and cache YouTube playlist videos using yt_dlp or the YouTube Data API.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import yt_dlp
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError
from yt_dlp.utils import DownloadError

from FUNCTIONS.HELPERS.helpers import ExtractedInfo, VideoInfoMap, YdlOpt
from FUNCTIONS.get_creditentials import get_authenticated_service
from FUNCTIONS.HELPERS.fileops import load, dump
from FUNCTIONS.HELPERS.fprint import fprint
from FUNCTIONS.HELPERS.logger import setup_logger
from FUNCTIONS.HELPERS.types_playlist import PlaylistVideoEntry

logger = setup_logger(__name__)


# ---------------------------------------------------------------------------
# yt-dlp helpers
# ---------------------------------------------------------------------------


def get_playlist_ids_with_ytdlp(url: str) -> tuple[int, VideoInfoMap | None]:
    """
    Fetch video IDs from a YouTube playlist using yt_dlp.

    Returns:
        tuple[int, VideoInfoMap] | None]: (status_code, video_list)
            - 0 → success
            - 1 → playlist private
            - 2 → other error
    """
    ydl_opts: YdlOpt = {"extract_flat": True, "quiet": True}

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # pyright: ignore[reportArgumentType]
            info = ydl.extract_info(  # pyright: ignore[reportAssignmentType]
                url, download=False
            )
            entries = info.get("entries")

            if not isinstance(entries, list):
                return 2, None

            ids: VideoInfoMap = {}
            for entry in entries:
                if isinstance(entry, dict) and isinstance(entry.get("id"), str):
                    ids[entry["id"]] = {"video_id": entry["id"]})

            return 0, ids

    except DownloadError as exc:
        if "This playlist is private" in str(exc):
            return 1, None
        return 2, None
    except Exception:
        return 2, None


# ---------------------------------------------------------------------------
# Playlist helpers
# ---------------------------------------------------------------------------


def is_special_playlist(playlist_id: str) -> bool:
    """Detect if a playlist is a YouTube special/system playlist."""
    return playlist_id.startswith(("LL", "WL", "HL", "LM", "RD", "FEmusic_liked"))


# ---------------------------------------------------------------------------
# Main fetcher
# ---------------------------------------------------------------------------


def fetch_playlist_videos(
    playlist_id: str,
    file_path: Path,
    test_run: bool,
    clean: bool = False,
    info: bool = True,
    error: bool = True,
) -> None:
    """
    Fetch playlist videos using yt_dlp, fallback to YouTube API if necessary.

    Args:
        playlist_id (str): Playlist identifier.
        file_path (Path): Path where playlist data will be saved.
        test_run (bool): If True, skip writing to disk.
        clean (bool): Force refetching even if cache exists.
        info (bool): Show progress with fprint().
        error (bool): Show API errors.
    """
    if info:
        fprint("", f"[Fetching videos] Fetching playlist '{playlist_id}'")
    logger.info(f"[Fetching videos] Fetching playlist '{playlist_id}'")

    # -----------------------------------------------------------------------
    # 1️⃣ Try using yt_dlp (fastest)
    # -----------------------------------------------------------------------
    if clean or not file_path.exists():
        all_videos: list[PlaylistVideoEntry | VideoInfo] = []

        if not is_special_playlist(playlist_id):
            status, videos = get_playlist_ids_with_ytdlp(
                f"https://www.youtube.com/playlist?list={playlist_id}"
            )

            if status == 0 and videos:
                dump(videos, file_path)
                logger.info(
                    f"[Fetching videos] {len(videos)} videos found in playlist '{playlist_id}'"
                )
                if info:
                    fprint(
                        "",
                        f"[Fetching videos] {len(videos)} videos saved (yt_dlp)",
                    )
                return

            if info:
                fprint(
                    "",
                    f"[Fetching videos] yt_dlp failed (status {status}), falling back to OAuth",
                )

        # -------------------------------------------------------------------
        # 2️⃣ Fallback: YouTube API (OAuth)
        # -------------------------------------------------------------------
        youtube: Resource = get_authenticated_service(info=info)
        next_page_token: str | None = None

        while True:
            try:
                request = youtube.playlistItems().list(  # type: ignore[call-arg, attr-defined]
                    part="snippet,contentDetails,status",
                    playlistId=playlist_id,
                    maxResults=50,
                    pageToken=next_page_token,
                )

                response: dict[str, Any] = request.execute()  # type: ignore[attr-defined]
                items = response.get("items")

                if not isinstance(items, list):
                    break

                for item in items:
                    if isinstance(item, dict):
                        entry = PlaylistVideoEntry.from_api_response(item)  # type: ignore[arg-type]
                        all_videos.append(entry)

                        if info:
                            fprint(
                                "",
                                f"[Fetching videos] {len(all_videos)} videos fetched...",
                            )

                token = response.get("nextPageToken")
                next_page_token = str(token) if isinstance(token, str) else None

                if not next_page_token:
                    break

                time.sleep(0.1)  # avoid hitting rate limits

            except HttpError as exc:
                logger.error(f"[Fetching videos] HTTP Error: {exc}")
                if error:
                    fprint("", f"[Fetching videos] Error: {exc}")

                if "quotaExceeded" in str(exc):
                    raise RuntimeError("Quota exceeded, please retry later.") from exc
                raise

        if not test_run:
            dump(all_videos, file_path)

        logger.info(
            f"[Fetching videos] {len(all_videos)} videos written to '{file_path}'"
        )

    # -----------------------------------------------------------------------
    # 3️⃣ Load from cache if exists
    # -----------------------------------------------------------------------
    else:
        cached_videos = load(file_path)
        logger.info(
            f"[Fetching videos] Loaded {len(cached_videos)} cached videos from '{file_path}'"
        )

        if info:
            fprint("", f"[Fetching videos] Loaded {len(cached_videos)} cached videos.")
