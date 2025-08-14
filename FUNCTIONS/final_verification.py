import os
from mutagen.mp3 import MP3
from mutagen.id3 import ID3
from CONSTANTS import LIKED_VIDEOS_FILE
from FUNCTIONS.fileops import load

def extract_video_id_from_file(filepath):
    """
    Extract the Video ID from the MP3 comment metadata.
    Returns the video ID string or None if not found.
    """
    try:
        audio = MP3(filepath, ID3=ID3)
        if audio.tags is not None:
            comments = audio.tags.getall('COMM')
            for comment in comments:
                for line in comment.text[0].split('\n'):
                    if line.strip().startswith('Video ID :'):
                        return line.split(':', 1)[1].strip()
    except Exception:
        return None
    return None

def final_verification(DOWNLOAD_DIRECTORY):
    """
    Checks:
      1. Every file in the download directory is valid and matches an ID in the playlist.
      2. Every ID in the playlist has a corresponding file in the download directory.
    """
    print("== Final Verification ==")
    # Load playlist
    liked_videos = load(LIKED_VIDEOS_FILE)
    if isinstance(liked_videos, dict):
        playlist_ids = set(liked_videos.keys())
    else:
        playlist_ids = set(liked_videos)

    # Scan download directory
    files = [f for f in os.listdir(DOWNLOAD_DIRECTORY) if f.lower().endswith('.mp3')]
    found_ids = set()
    orphaned_files = []
    corrupted_files = []

    for filename in files:
        filepath = os.path.join(DOWNLOAD_DIRECTORY, filename)
        video_id = extract_video_id_from_file(filepath)
        if not video_id:
            corrupted_files.append(filename)
            continue
        found_ids.add(video_id)
        if video_id not in playlist_ids:
            orphaned_files.append(filename)

    # Find missing files (IDs in playlist, but no file)
    missing_ids = playlist_ids - found_ids

    # Print summary
    print(f"\nChecked {len(files)} files in {DOWNLOAD_DIRECTORY}")
    print(f"Valid files with matching IDs: {len(found_ids) - len(orphaned_files)}")
    if corrupted_files:
        print(f"\nCorrupted or invalid files ({len(corrupted_files)}):")
        for f in corrupted_files:
            print(f"  - {f}")
    if orphaned_files:
        print(f"\nOrphaned files (not in playlist) ({len(orphaned_files)}):")
        for f in orphaned_files:
            print(f"  - {f}")
    if missing_ids:
        print(f"\nMissing files for these playlist IDs ({len(missing_ids)}):")
        for vid in missing_ids:
            print(f"  - {vid}")
    if not corrupted_files and not orphaned_files and not missing_ids:
        print("\nAll files and IDs are consistent and valid!")
        return True
    return False
