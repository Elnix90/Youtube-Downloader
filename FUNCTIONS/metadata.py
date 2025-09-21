from pathlib import Path
from typing import Literal
import json

from mutagen.mp3 import MP3
from mutagen.id3 import ID3, Frames  # pyright: ignore[reportUnknownVariableType]
from mutagen.id3._frames import TXXX
from mutagen._util import MutagenError

from FUNCTIONS.helpers import VideoInfo

from logger import setup_logger
logger = setup_logger(__name__)






def get_metadata_tag(filepath: Path, tag: str = 'metadata') -> tuple[VideoInfo | None, Literal[0,1,2,3]]:
    """Return metadata from an MP3 file, and a state code
    Returns:
        0 -> ok
        1 -> empty data
        2 -> malformed
        3 -> corrupted
    """
    try:
        audio: MP3 | None = MP3(str(filepath), ID3=ID3)
        if audio.tags is not None:  # pyright: ignore[reportUnknownMemberType]
            comments = audio.tags.getall('TXXX')  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
            for comment in comments:   # pyright: ignore[reportUnknownVariableType]
                if isinstance(comment, TXXX) and comment.desc.lower() == tag.lower():  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
                    try:
                        data = json.loads(comment.text[0])   # pyright: ignore[reportUnknownMemberType, reportAny, reportUnknownArgumentType, reportAttributeAccessIssue]
                    except Exception as e:
                        logger.warning(f"[Get Metadata Tag] Exception during converting to python dict: {e}")
                        return None, 2
                    if data:
                        logger.verbose(f"[Get Metadata Tag] Sucessfully loaded metadata from '{filepath}'")
                        return data, 0
                    else:
                        logger.info(f"[Get Metadata Tag] Empty data in file '{filepath}'")

            logger.info(f"[Get Metadata Tag] No TXXX:{tag} tag field in '{filepath}'")
            return None, 2

        logger.warning(f"[Get Metadata Tag] No audio.tags tags in '{filepath}'")
        return None, 2

    except Exception as e:
        logger.warning(f"[Get Metadata Tag] Failed to read data, file '{filepath}' corrupted : {e}")
        return None, 3







def repair_mp3_file(filepath: Path, test_run: bool) -> bool:
    """
    Attempts to repair a possibly corrupted MP3 file by re-saving its
    tags using mutagen. 
    
    Returns:
        True if file is healthy or repaired successfully.
        False if file is corrupted and repair failed, indicating re-download needed.
    """
    try:
        audio = MP3(str(filepath), ID3=ID3)
        # Attempt to access tags to trigger loading/validation
        _ = audio.tags    # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]

        # Try saving tags to fix minor corruptions or header problems
        if not test_run: audio.save()   # pyright: ignore[reportUnknownMemberType]
        logger.verbose(f"[Repair MP3] File '{filepath}' is healthy or repaired successfully")
        return True

    except MutagenError as e:
        logger.error(f"[Repair MP3] Mutagen error on file '{filepath}': {e}")
        return False
    except Exception as e:
        logger.error(f"[Repair MP3] Unexpected error on file '{filepath}': {e}")
        return False







def read_id3_tag(filepath: Path, frame_id: str) -> tuple[list[str] | str, Literal[0, 1, 2]]:
    """
    Read ID3 tag frame text from the MP3 file.

    Returns:
        - List of strings if multiple text entries exist,
        - Single string if only one entry,
        - tuple (data, status_code):
            0 -> success
            1 -> no data
            2 -> exception/error
    """
    try:
        audio = MP3(str(filepath), ID3=ID3)
        if audio.tags is not None:  # pyright: ignore[reportUnknownMemberType]
            frame = audio.tags.get(frame_id) # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
            if frame:
                if hasattr(frame, 'text'): # pyright: ignore[reportUnknownArgumentType]
                    text = frame.text  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
                    if isinstance(text, list):
                        logger.verbose(f"[Read Tag] Sucessfuly readed tag '{frame_id}' from '{filepath}'")
                        return text, 0  # pyright: ignore[reportUnknownVariableType]
                    else:
                        logger.verbose(f"[Read Tag] Sucessfuly readed tag '{frame_id}' from '{filepath}'")
                        return [text], 0
                elif hasattr(frame, 'data'):  # pyright: ignore[reportUnknownArgumentType]
                    logger.verbose(f"[Read Tag] Sucessfuly readed tag '{frame_id}' from '{filepath}'")
                    return frame.data, 0  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        
        logger.info(f"[Read Tag] No '{frame_id}' tag to read from '{filepath}'")
        return [], 1
    except Exception as e:
        logger.error(f"[Read Tag] Failed to read tag '{frame_id}' from '{filepath}': {e}")
        return [], 2







def write_id3_tag(filepath: Path, frame_id: str, data: str | list[str] | set[str], test_run: bool) -> bool:
    """
    Write ID3 tag frame text to the MP3 file.

    Args:
      - filepath: path to MP3 file
      - frame_id: ID3 frame id (e.g. 'TCON' for genre, 'TPE1' for artist)
      - data: string or iterable of strings to write as tag text

    Returns:
      - True if success, False otherwise
    """
    try:
        audio = MP3(str(filepath), ID3=ID3)
        if audio.tags is None:  # pyright: ignore[reportUnknownMemberType]
            audio.add_tags()    # pyright: ignore[reportUnknownMemberType]

        # Normalize to list of strings
        if isinstance(data, (list, set)):
            text_data = list(data)
        else:
            text_data = [data]

        # Handle custom TXXX frame explicitly
        if frame_id.startswith("TXXX:"):
            desc = frame_id.replace("TXXX:", "")
            audio.tags.add(TXXX(encoding=3, desc=desc, text=text_data))  # pyright: ignore[reportUnknownMemberType, reportOptionalMemberAccess]
        else:
            frame_class = Frames.get(frame_id)  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]

            if frame_class is None:
                logger.warning(f"[Write Tag] Frame '{frame_id}' not found. Using 'TXXX' custom frame")
                text_data = ["; ".join(text_data)]  # collapse to single string
                audio.tags.add(TXXX(encoding=3, desc=frame_id, text=text_data))  # pyright: ignore[reportUnknownMemberType, reportOptionalMemberAccess]
            else:
                # Standard frame
                audio.tags.add(frame_class(encoding=3, text=text_data))  # pyright: ignore[reportUnknownMemberType, reportOptionalMemberAccess]

        if not test_run:
            audio.save()  # pyright: ignore[reportUnknownMemberType]

        logger.verbose(f"[Write Tag] Successfully written tag '{frame_id}' into '{filepath.name}'")
        return True

    except Exception as e:
        logger.error(f"[Write Tag] Failed to write tag '{frame_id}' into '{filepath.name}': {e}")
        return False



