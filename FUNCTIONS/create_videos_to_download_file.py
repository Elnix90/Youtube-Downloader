from CONSTANTS import VIDEOS_TO_DOWNLOAD_FILE, LIKED_VIDEOS_FILE, UNAVAILABLE_VIDEOS_FILE
from FUNCTIONS.fileops import load, dump
import os
from mutagen.mp3 import MP3  # type: ignore
from mutagen.id3 import ID3  # type: ignore
from pathlib import Path
from typing import Any, List, Dict
from FUNCTIONS.metadata import get_metadata_tag




def clean_download_directory(download_directory: Path, verbose: bool = True) -> None:
    """Remove MP3 files that are corrupted or lack valid metadata."""
    removed_files: Dict[str,str] = {}
    checked_files: int = 0

    if not download_directory.exists():
        return

    for filename in os.listdir(str(download_directory)):
        if filename.lower().endswith('.mp3'):
            filepath = download_directory / filename
            data, state = get_metadata_tag(filepath)  # type: ignore
            if state in (1, 2, 3):
                if state == 1: reason = "missing or malformed metadata"
                elif state == 2: reason = "corrupted or unreadable file"
                else: reason = "data empty"
                os.remove(str(filepath))
                removed_files[filename] = reason
        else:
            pass
            removed_files[filename] = "Not mp3"
            os.remove(str(download_directory / filename))
        checked_files += 1
        if verbose: print(f"\r[Clean directory] Checked {checked_files} files.", end="", flush=True)
            

    if checked_files > 0 and verbose:
        print()
        for file, reason in removed_files.items():
            print(f" - Removed {file}: {reason}")
        else:
            print("\r\033[F\033[K[Clean directory] All files are valid.")


def extract_existing_video_ids(download_directory: Path) -> Dict[str, Dict[str, Any]]:
    """Extract video IDs from metadata in downloaded MP3 files."""
    existings: Dict[str, Dict[str, Any]] = {}

    if not download_directory.exists():
        return existings

    for filename in os.listdir(str(download_directory)):
        if filename.lower().endswith('.mp3'):
            filepath = download_directory / filename
            data, state = get_metadata_tag(filepath)
            if state == 0 and data is not None:
                video_id = data.get('id')
                if video_id is not None:
                    data['filename'] = filename
                    existings[video_id] = data

    return existings


def create_videos_to_download(download_directory: Path) -> None:
    """
    Create a download list by comparing the playlist with already downloaded files.
    Only missing videos will be added to the download list.
    """
    videos_file_path = Path(VIDEOS_TO_DOWNLOAD_FILE)
    liked_videos_file = Path(LIKED_VIDEOS_FILE)
    unavailable_file = Path(UNAVAILABLE_VIDEOS_FILE)

    if not videos_file_path.exists():
        playlist_videos: Dict[str, Any] = load(liked_videos_file)
        playlist_ids = set(playlist_videos.keys())

        clean_download_directory(download_directory)
        existings = extract_existing_video_ids(download_directory)
        print(f"Found {len(existings)} existing videos in download directory")

        # Only keep videos that are in the playlist but not already downloaded
        to_download_ids = playlist_ids - set(existings.keys())
        videos_to_download: List[str] = list(to_download_ids)

        if unavailable_file.exists():
            private_videos: List[str] = load(unavailable_file)
            videos_to_download = [vid for vid in videos_to_download if vid not in private_videos]

        dump(videos_to_download, videos_file_path)
        print(f"Videos to download file created: {len(videos_to_download)} videos to download")
    else:
        videos_to_download: List[str] = load(videos_file_path)
        print(f"Videos to download file already exists, {len(videos_to_download)} remaining")
