import os
from pathlib import Path
from typing import List, Set

from CONSTANTS import LIKED_VIDEOS_FILE
from FUNCTIONS.fileops import load
from FUNCTIONS.create_videos_to_download_file import get_metadata_tag


def final_verification(download_directory: Path) -> bool:
    """
    Checks:
      1. Every file in the download directory is valid and matches an ID in the playlist.
      2. Every ID in the playlist has a corresponding file in the download directory.
    """
    print("== Final Verification ==")

    # Load playlist (can be dict[str, Any] or list[str])
    liked_videos:  List[str] = load(Path(LIKED_VIDEOS_FILE))



    playlist_ids = set(liked_videos)

    # Scan download directory
    files: List[str] = [
        f for f in os.listdir(download_directory) if f.lower().endswith('.mp3')
    ]
    found_ids: Set[str] = set()
    orphaned_files: List[str] = []
    corrupted_files: List[str] = []

    for filename in files:
        filepath: Path = download_directory / filename
        data, status = get_metadata_tag(filepath)
        if status == 0 and data is not None:
            video_id: str = str(data.get("id", ""))
            found_ids.add(video_id)
            if video_id not in playlist_ids:
                orphaned_files.append(filename)
        else:
            corrupted_files.append(filename)

    # Find missing files (IDs in playlist, but no file present)
    missing_ids: Set[str] = playlist_ids - found_ids

    # Print summary
    print(f"\nChecked {len(files)} files in {download_directory}")
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
