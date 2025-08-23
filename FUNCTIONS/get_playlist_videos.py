from typing import Any, List, Union, Dict
from googleapiclient.errors import HttpError # type: ignore
from pathlib import Path
from FUNCTIONS.fileops import load, dump


def fetch_playlist_videos(
    youtube: Any,
    playlist_id: str,
    file: Union[str, Path],
    clean: bool = False,
    verbose: bool = True,
    errors:bool = True
) -> List[str]:
    print(f"[Fetching videos] Fetching videos from playlist {playlist_id}", end='')

    file_path = Path(file)
    if clean or (not file_path.exists()):
        all_videos: List[str] = []
        next_page_token: Union[str, None] = None

        while True:
            try:
                request = youtube.playlistItems().list(
                    part="contentDetails",
                    playlistId=playlist_id,
                    maxResults=50,
                    pageToken=next_page_token
                )
                response: Dict[str, Any] = request.execute()

                items: List[Dict[str, Any]] = response.get('items', [])
                for item in items:
                    content_details: Dict[str, Any] = item.get('contentDetails', {})
                    vid_id: str = content_details.get('videoId', "")
                    if vid_id:
                        all_videos.append(vid_id)
                        if verbose : print(f"\r[Fetching videos] {len(all_videos)} videos found in playlist : {playlist_id}", end="", flush=True)

                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break

            except HttpError as e:
                if errors : print(f"Error while fetching playlist videos: {e}")
                if "quotaExceeded" in str(e):
                    raise Exception("Quota exceeded, please change your token or retry in 24h")
                else:
                    raise

        dump(all_videos, file_path)
        print()
        return all_videos
    else:
        videos: List[str] = load(file_path)
        if verbose : print(f"\r\033[K[Fetching videos] {len(videos)} videos found in file {file_path}")
        return videos