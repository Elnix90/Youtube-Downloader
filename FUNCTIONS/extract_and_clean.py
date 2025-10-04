"""
Checks the directory and reads the files that are present,
or removes those that aren't well formatted or unreadable.
"""

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

    Args:
        download_directory: Path to the directory containing MP3 files.
        info: Whether to print info messages.
        test_run: If True, do not actually remove files.
        remove: Whether to remove invalid files.
        force_mp3_presence: If True, only keep .lrc/.png if corresponding MP3 exists.

    Returns:
        VideoInfoMap: mapping of video_id -> metadata (with filepath added)
    """
    removed_files: dict[str, str] = {}
    valid_files: VideoInfoMap = {}
    checked_files: int = 0
    lrc_or_png: int = 0

    if not download_directory.exists():
        message = f"[Clean & Extract] Directory does not exist: {download_directory}"
        if info:
            print(message)
        logger.warning(message)
        return valid_files

    for filepath in download_directory.iterdir():
        checked_files += 1

        if not filepath.is_file():
            logger.warning(f"[Clean & Extract] Not a file, skipping: '{filepath.name}'")
            continue

        # Case 1: Not an MP3 (but allow .lrc or .png)
        if filepath.suffix != ".mp3":
            if filepath.suffix in (".lrc", ".png"):
                if not force_mp3_presence or filepath.with_suffix(".mp3").exists():
                    logger.verbose(
                        f"[Clean & Extract] Keeping '{filepath.name}' " +
                        "(.lrc or .png)" + 
                        " (with associated mp3 file)" if not force_mp3_presence else ""
                    )
                    lrc_or_png += 1
                    continue

            removed_files[filepath.name] = "Not MP3"
            if not test_run and remove:
                filepath.unlink(missing_ok=True)
            logger.warning(f"[Clean & Extract] Removed '{filepath.name}': Not an MP3")
            continue

        # Case 2: MP3 file — check metadata
        data, state = get_metadata_tag(filepath)
        if state == 0 and data is not None:
            logger.verbose(f"[Clean & Extract] state is 0 for file: {filepath.name}")
            video_id = data.get("video_id")

            if "id" in data:
                del data["id"]
                data["video_id"] = video_id
                logger.verbose(f"[Clean & Extract] sucessfully renamed id to video_id from data for : {filepath.name}")

            if video_id:
                data_filename = data.get("filename")
                if isinstance(data_filename, str):
                    valid_files[video_id] = data
                    logger.verbose(
                        f"[Clean & Extract] Valid MP3: '{data_filename}' with ID '{video_id}'"
                    )
                else:
                    logger.error(f"[Clean & Extract] data_filename isn't str for: {filepath.name}")
            else:
                removed_files[filepath.name] = "Missing video ID in metadata"
                if not test_run and remove:
                    filepath.unlink(missing_ok=True)
                logger.info(
                    f"[Clean & Extract] Removed '{filepath.name}': Missing video ID in metadata"
                )
        else:
            if state == 1:
                reason = "Missing or malformed metadata"
            elif state == 2:
                reason = "Corrupted or unreadable file"
            else:
                reason = "Empty data"

            removed_files[filepath.name] = reason
            if not test_run and remove:
                filepath.unlink(missing_ok=True)
            logger.info(f"[Clean & Extract] Removed '{filepath.name}': {reason}")

        if info:
            fprint(
                "[Clean & Extract] ",
                f"Checked {checked_files} files, removed {len(removed_files)}, " +
                f"kept {len(valid_files)} valid MP3s, " +
                f"{lrc_or_png} valid lyrics or thumbnails"
            )

    logger.info(
        f"[Clean & Extract] Checked {checked_files} files, removed {len(removed_files)}, " +
        f"kept {len(valid_files)} valid MP3s, {lrc_or_png} valid lyrics or thumbnails"
    )

    if info:
        if checked_files == 0:
            print("\r\033[K[Clean & Extract] No files in the directory")
        elif removed_files:
            print()
            for file_name, reason in removed_files.items():
                print(f" - Removed {file_name}: {reason}")
        else:
            print(f"\r\033[K[Clean & Extract] All {checked_files} files are valid")

    return valid_files
