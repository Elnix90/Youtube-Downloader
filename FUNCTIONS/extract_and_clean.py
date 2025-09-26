from pathlib import Path


from FUNCTIONS.metadata import get_metadata_tag
from FUNCTIONS.HELPERS.helpers import VideoInfoMap
from FUNCTIONS.HELPERS.fprint import fprint

from FUNCTIONS.HELPERS.logger import setup_logger
logger = setup_logger(__name__)






def extract_and_clean_video_ids(
    download_directory: Path,
    info: bool,
    test_run: bool,
    remove: bool,
    force_mp3_presence: bool
) -> VideoInfoMap:
    """
    Cleans the directory by removing non-MP3 or invalid files,
    and returns a mapping of valid video IDs to metadata.

    Returns:
        VideoInfoMap: dict of video_id -> metadata (with filepath added)
    """
    removed_files: dict[str, str] = {}
    valid_files: VideoInfoMap = {}
    checked_files: int = 0
    lrc_or_png: int = 0

    if not download_directory.exists():
        if info: print(f"[Clean & Extract] Directory does not exist: {download_directory}")
        logger.warning(f"[Clean & Extract] Directory does not exist: {download_directory}")
        return valid_files

    for filepath in download_directory.iterdir():
        checked_files += 1

        if not filepath.is_file():
            logger.warning(f"[Clean & Extract] Not a file, skipping : '{filepath.name}'")
            continue  # Skip directories or symlinks

        # Case 1: Not an MP3 (but keep .lrc and .png files)
        if not filepath.suffix == ".mp3":
            if filepath.suffix not in (".lrc", ".png"):
                if not force_mp3_presence or filepath.with_suffix(".mp3").exists(): # If no mp3 associated file:
                    logger.verbose(f"[Clean & Extract] Keeping '{filepath.name}' (.lrc or .png)")
                    lrc_or_png += 1
                    continue
            removed_files[filepath.name] = "Not mp3"
            if not test_run and remove:
                filepath.unlink(missing_ok=True)
            logger.warning(f"[Clean & Extract] Removed '{filepath.name}': Not an MP3")
            continue

        # Case 2: MP3 file — check metadata
        data, state = get_metadata_tag(filepath)
        if state == 0 and data is not None:

            video_id = data.get("video_id")

            if "id" in data:
                del data["id"]
                data["video_id"] = video_id

            if video_id:
                data_filename: str | None = data.get("filepath")
                if isinstance(data_filename, str):
                    valid_files[video_id] = data
                    logger.verbose(f"[Clean & Extract] Valid MP3: '{data_filename}' with ID '{video_id}'")
            else:
                removed_files[filepath.name] = "Missing video ID in metadata"
                if not test_run and remove: filepath.unlink(missing_ok=True)
                logger.info(f"[Clean & Extract] Removed '{filepath.name}': Missing video ID in metadata")
        else:
            if state == 1:
                reason = "Missing or malformed metadata"
            elif state == 2:
                reason = "Corrupted or unreadable file"
            else:
                reason = "Empty data"


            removed_files[filepath.name] = reason
            if not test_run and remove: filepath.unlink(missing_ok=True)
            logger.info(f"[Clean & Extract] Removed '{filepath.name}': {reason}")

        if info:
            fprint("[Clean & Extract] ",f"Checked {checked_files} files, removed {len(removed_files)}, kept {len(valid_files)} valid MP3s, {lrc_or_png} valid lyrics or thumbnail")

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