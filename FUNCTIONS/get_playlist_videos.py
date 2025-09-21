from googleapiclient.errors import HttpError
from pathlib import Path
from FUNCTIONS.fileops import load, dump


from FUNCTIONS.get_creditentials import get_authenticated_service
from FUNCTIONS.helpers import fprint

from logger import setup_logger
logger = setup_logger(__name__)

import yt_dlp


def get_playlist_ids_with_ytdlp(url: str) -> tuple[int, list[str] | None]:
    """
    Try to fetch playlist video IDs with yt_dlp.
    
    Returns:
      - (0, list_of_ids) if successful
      - (1, None) if playlist requires login/private
      - (2, None) if some other error occurred
    """
    ydl_opts = {"extract_flat": True, "quiet": True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # pyright: ignore[reportArgumentType]
            info = ydl.extract_info(url, download=False)
            if "entries" not in info or not info["entries"]:
                return 1, None  # likely private or unavailable
            ids = [entry.get("id") for entry in info["entries"] if entry.get("id")]  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType, reportGeneralTypeIssues]
            return 0, ids  # pyright: ignore[reportUnknownVariableType]
    except yt_dlp.utils.DownloadError as e:  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportAttributeAccessIssue]
        if "This playlist is private" in str(e):  # pyright: ignore[reportUnknownArgumentType]
            return 1, None
        return 2, None
    except Exception:
        return 2, None


def is_special_playlist(playlist_id: str) -> bool:
    """
    Check if a playlist is one of YouTube's special/system playlists.
    """
    specials = ("LL", "WL", "HL", "LM", "RD", "FEmusic_liked")
    return playlist_id.startswith(specials)


def fetch_playlist_videos(
    playlist_id: str,
    file: Path,
    clean: bool = False,
    info: bool = True,
    errors: bool = True
) -> None:

    if info: fprint(prefix="", title=f"[Fetching videos] Fetching videos from playlist '{playlist_id}'")
    logger.info(f"[Fetching videos] Fetching videos from playlist '{playlist_id}'")

    file_path = Path(file)
    if clean or (not file_path.exists()):
        all_videos: list[str] = []

        # Try yt_dlp first if not a special playlist
        if not is_special_playlist(playlist_id):
            status, ids = get_playlist_ids_with_ytdlp(f"https://www.youtube.com/playlist?list={playlist_id}")
            if status == 0 and ids:
                all_videos = ids
                dump(data=all_videos, file=file_path)
                if info: print(f"\r[Fetching videos] {len(all_videos)} videos found in playlist : '{playlist_id}'")
                logger.info(f"[Fetching videos] {len(all_videos)} videos found in playlist :' {playlist_id}'")
                return
            elif info: print(f"\r[Fetching videos] yt_dlp failed (status {status}), falling back to OAuth client")

        # OAuth fallback (or special playlists)
        youtube = get_authenticated_service(info=info)
        next_page_token: str | None = None
        while True:
            try:
                request = youtube.playlistItems().list(  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue, reportUnknownVariableType]
                    part="contentDetails",
                    playlistId=playlist_id,
                    maxResults=50,
                    pageToken=next_page_token
                )
                response= request.execute()  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
                items = response.get('items', [])  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
                for item in items:  # pyright: ignore[reportUnknownVariableType]
                    content_details = item.get('contentDetails', {})  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
                    vid_id: str = content_details.get('videoId', "")  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
                    if vid_id:
                        all_videos.append(vid_id)  # pyright: ignore[reportUnknownArgumentType]
                        if info: fprint(prefix="", title=f"[Fetching videos] {len(all_videos)} videos found in playlist : '{playlist_id}'")
                next_page_token = response.get('nextPageToken')  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
                if not next_page_token:
                    break
            except HttpError as e:
                if errors: print(f"\n[Fetching videos] Error while fetching playlist videos: {e}")
                logger.error(f"[Fetching videos] Error while fetching playlist videos: {e}")
                if "quotaExceeded" in str(e):
                    raise Exception("[Fetching videos] Quota exceeded, please change your token or retry in 24h")
                else:
                    raise

        dump(data=all_videos, file=file_path)
        if info: print()
        logger.info(f"[Fetching videos] {len(all_videos)} videos found in playlist : '{playlist_id}'")
    else:
        videos: list[str] = load(file_path)
        logger.info(f"[Fetching videos] {len(videos)} videos found in file '{file_path}'")
        if info: print(f"\r\033[K[Fetching videos] {len(videos)} videos found in file '{file_path}'")
