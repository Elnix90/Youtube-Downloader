import os
from pathlib import Path


from FUNCTIONS.metadata import get_metadata_tag
from FUNCTIONS.helpers import VideoInfoMap, fprint

from logger import setup_logger
logger = setup_logger(__name__)






def extract_and_clean_video_ids(download_directory: Path, info: bool, test_run: bool, remove: bool) -> VideoInfoMap:
    """
    Cleans the directory by removing non-MP3 or invalid files,
    and returns a mapping of valid video IDs to metadata.

    Returns:
        VideoInfoMap: dict of video_id -> metadata (with filename added)
    """
    removed_files: dict[str, str] = {}
    valid_files: VideoInfoMap = {}
    checked_files: int = 0
    lrc_or_png: int = 0

    if not download_directory.exists():
        if info: print(f"[Clean & Extract] Directory does not exist: {download_directory}")
        logger.warning(f"[Clean & Extract] Directory does not exist: {download_directory}")
        return valid_files

    for filename in os.listdir(str(download_directory)):
        filepath = download_directory / filename
        checked_files += 1

        if not filepath.is_file():
            logger.warning(f"[Clean & Extract] Not a file, skipping : '{filepath}'")
            continue  # Skip directories or symlinks

        # Case 1: Not an MP3 (but keep .lrc and .png files)
        if not filename.lower().endswith(".mp3"):
            if filename.lower().endswith((".lrc", ".png")) and filepath.with_suffix(".mp3").exists(): # If no mp3 associated file:
                logger.debug(f"[Clean & Extract] Keeping '{filename}' (.lrc or .png)")
                lrc_or_png += 1
                continue
            removed_files[filename] = "Not mp3"
            if not test_run and remove:
                filepath.unlink(missing_ok=True)
            logger.warning(f"[Clean & Extract] Removed '{filename}': Not an MP3")
            continue

        # Case 2: MP3 file — check metadata
        data, state = get_metadata_tag(filepath)
        if state == 0 and data is not None:

            video_id = data.get("video_id")

            if "id" in data:
                del data["id"]
                data["video_id"] = video_id

            if video_id:
                filename = data.get("filename")
                valid_files[video_id] = data
                logger.debug(f"[Clean & Extract] Valid MP3: '{filename}' with ID '{video_id}'")
            else:
                removed_files[filename] = "Missing video ID in metadata"
                if not test_run and remove: os.remove(filepath)
                logger.info(f"[Clean & Extract] Removed '{filename}': Missing video ID in metadata")
        else:
            if state == 1:
                reason = "Missing or malformed metadata"
            elif state == 2:
                reason = "Corrupted or unreadable file"
            else:
                reason = "Empty data"


            removed_files[filename] = reason
            if not test_run and remove: os.remove(filepath)
            logger.info(f"[Clean & Extract] Removed '{filename}': {reason}")

        if info:
            fprint(prefix="[Clean & Extract] ",title=f"Checked {checked_files} files, removed {len(removed_files)}, kept {len(valid_files)} valid MP3s, {lrc_or_png} valid lyrics or thumbnail")

    logger.info(f"[Clean & Extract] Checked {checked_files} files, removed {len(removed_files)}, kept {len(valid_files)} valid MP3s, {lrc_or_png} valid lyrics or thumbnail")

    if info:
        if checked_files == 0:
            print("\r\033[K[Clean & Extract] No files in the directory")
        elif removed_files:
            print()
            for file, reason in removed_files.items():
                print(f" - Removed {file}: {reason}")
        else:
            print(f"\r\033[K[Clean & Extract] All {checked_files} files are valid")

    return valid_files