from CONSTANTS import VIDEOS_TO_DOWNLOAD_FILE, LIKED_VIDEOS_FILE,UNAVAILABLE_VIDEOS_FILE
from FUNCTIONS.fileops import load, dump
import os
from mutagen.mp3 import MP3
from mutagen.id3 import ID3
from pathlib import Path

def clean_download_directory(DOWNLOAD_DIRECTORY):
    """Remove MP3 files that are corrupted or lack valid 'Video ID :' in metadata."""
    removed_files = []
    checked_files = 0

    if not Path(DOWNLOAD_DIRECTORY).exists():
        return

    for filename in os.listdir(DOWNLOAD_DIRECTORY):
        if filename.lower().endswith('.mp3'):
            filepath = os.path.join(DOWNLOAD_DIRECTORY, filename)
            checked_files += 1
            try:
                audio = MP3(filepath, ID3=ID3)
                valid = False
                if audio.tags is not None:
                    comments = audio.tags.getall('COMM')
                    for comment in comments:
                        for line in comment.text[0].split('\n'):
                            if line.strip().startswith('Video ID :'):
                                valid = True
                                break
                        if valid:
                            break
                if not valid:
                    print(f"Deleting {filename}: missing or malformed Video ID metadata.")
                    os.remove(filepath)
                    removed_files.append(filename)
            except Exception as e:
                print(f"Deleting {filename}: corrupted or unreadable file ({str(e)}).")
                os.remove(filepath)
                removed_files.append(filename)
    print(f"\nChecked {checked_files} MP3 files.")
    if removed_files:
        print(f"Removed {len(removed_files)} invalid files:")
        for f in removed_files:
            print(f"  - {f}")
    else:
        print("All files are valid.")

def extract_existing_video_ids(DOWNLOAD_DIRECTORY):
    """Extract video IDs from comment metadata in downloaded MP3 files."""
    existing_ids = set()
    if not Path(DOWNLOAD_DIRECTORY).exists():
        return existing_ids

    for filename in os.listdir(DOWNLOAD_DIRECTORY):
        if filename.lower().endswith('.mp3'):
            filepath = os.path.join(DOWNLOAD_DIRECTORY, filename)
            try:
                audio = MP3(filepath, ID3=ID3)
                if audio.tags is not None:
                    comments = audio.tags.getall('COMM')
                    for comment in comments:
                        for line in comment.text[0].split('\n'):
                            if line.strip().startswith('Video ID :'):
                                vid = line.split(':', 1)[1].strip()
                                existing_ids.add(vid)
            except Exception:
                continue
    return existing_ids

def create_videos_to_download(DOWNLOAD_DIRECTORY):
    """
    Create a download list by comparing the playlist with already downloaded files.
    Only missing videos will be added to the download list.
    """
    if not Path(VIDEOS_TO_DOWNLOAD_FILE).exists():

        playlist_videos = load(LIKED_VIDEOS_FILE)
        playlist_ids = set(playlist_videos)

        clean_download_directory(DOWNLOAD_DIRECTORY)
        existing_ids = extract_existing_video_ids(DOWNLOAD_DIRECTORY)
        print(f"Found {len(existing_ids)} existing videos in download directory")

        # Only keep videos that are in the playlist but not already downloaded
        to_download_ids = playlist_ids - existing_ids

        videos_to_download = list(to_download_ids)

        if Path(UNAVAILABLE_VIDEOS_FILE).exists():
            private_videos = load(UNAVAILABLE_VIDEOS_FILE)
            for video in private_videos:
                if video in videos_to_download:
                    videos_to_download.remove(video)


        dump(videos_to_download, VIDEOS_TO_DOWNLOAD_FILE)
        print(f"Videos to download file created: {len(videos_to_download)} videos to download")
    else:
        videos_to_download = load(VIDEOS_TO_DOWNLOAD_FILE)
        print(f"Videos to download file already exists, {len(videos_to_download)} remaining")