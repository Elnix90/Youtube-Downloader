import json
from pathlib import Path
from typing import Literal

from mutagen.id3 import ID3
from mutagen.id3._frames import TXXX
from mutagen.mp3 import MP3

from FUNCTIONS.HELPERS.helpers import VideoInfo
from FUNCTIONS.HELPERS.logger import setup_logger

logger = setup_logger(__name__)


def write_metadata_to_json(
    filepath: Path, file: Path, tag: str = 'metadata'
) -> tuple[VideoInfo | None, Literal[0, 1, 2, 3]]:
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
            comments = audio.tags.getall(
                'TXXX'
            )  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
            for (
                comment
            ) in comments:  # pyright: ignore[reportUnknownVariableType]
                if (
                    isinstance(comment, TXXX)
                    and comment.desc.lower() == tag.lower()
                ):  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
                    try:
                        data = json.loads(
                            comment.text[0]
                        )  # pyright: ignore[reportUnknownMemberType, reportAny, reportUnknownArgumentType, reportAttributeAccessIssue]
                    except Exception as e:
                        logger.warning(
                            f"[Get Metadata Tag] Exception during converting to python dict: {e}"
                        )
                        return None, 2
                    if data:
                        with open(file, "w") as f:
                            _ = f.write(json.dumps(data, indent=4))
                        logger.info(
                            f"[Get Metadata Tag] Sucessfully loaded metadata from '{filepath}'"
                        )
                        return data, 0
                    else:
                        logger.warning(
                            f"[Get Metadata Tag] Empty data in file '{filepath}'"
                        )
            logger.warning(
                f"[Get Metadata Tag] No TXXX:{tag} tag field in '{filepath}'"
            )
            return None, 2
        logger.warning(
            f"[Get Metadata Tag] No audio.tags tags in '{filepath}'"
        )
        return None, 2
    except Exception as e:
        logger.warning(
            f"[Get Metadata Tag] Failed to read data, file '{filepath}' corrupted : {e}"
        )
        return None, 3
