from io import BytesIO
from pathlib import Path
from typing import Literal

import requests
from mutagen.id3 import ID3
from mutagen.id3._frames import APIC
from mutagen.mp3 import MP3
from PIL import Image

from FUNCTIONS.HELPERS.logger import setup_logger

logger = setup_logger(__name__)


def download_and_pad_image(
    image_url: str, save_path: Path, thumbnail_format: Literal["pad", "crop"]
) -> bool:
    """
    Downloads an image from the provided URL, adds transparent padding to make it square,

    :param image_url: URL of the image to download.
    :param save_path: Path to save the padded image.
    :return: True if successful, False otherwise.
    """
    try:
        # Download the image
        response = requests.get(image_url)
        response.raise_for_status()

        img_bytes = BytesIO(response.content)
        with Image.open(img_bytes) as img:
            width, height = img.size
            max_side = max(width, height)

            if thumbnail_format == "pad":
                new_img = Image.new("RGBA", (max_side, max_side), (0, 0, 0, 0))
                paste_x = (max_side - width) // 2
                paste_y = (max_side - height) // 2
                new_img.paste(img, (paste_x, paste_y))

            elif thumbnail_format == "crop":
                side_length: int = min(width, height)
                left: int = (width - side_length) // 2
                top: int = (height - side_length) // 2
                right: int = left + side_length
                bottom: int = top + side_length
                new_img: Image.Image = img.crop((left, top, right, bottom))

            new_img.save(save_path, "PNG")

        logger.debug(
            f"[Down+Crop] Successfully downloaded and padded '{image_url}'"
        )
        return True

    except Exception as e:
        logger.error(f"[Down+Crop] Error while processing '{image_url}' : {e}")
        return False


def embed_image_in_mp3(
    mp3_path: Path, image_path: Path, test_run: bool
) -> bool:
    """
    Loads an image from the specified file and embeds it as cover art into an MP3 file.

    :param mp3_path: Path to the MP3 file to modify.
    :param image_path: Path to the image file to embed as the cover art.
    :return: True if embedding succeeded, False otherwise.
    """
    try:
        # Load the MP3 file
        audio: MP3 = MP3(mp3_path, ID3=ID3)
        logger.debug(f"[Embed Cover] Loaded MP3: '{mp3_path}'")

        # Add ID3 tag if not already present
        if audio.tags is None:  # pyright: ignore[reportUnknownMemberType]
            audio.add_tags()  # pyright: ignore[reportUnknownMemberType]
            logger.debug(f"[Embed Cover] ID3 tags added to '{mp3_path}'")
        else:
            logger.debug(
                f"[Embed Cover] ID3 tags already present in '{mp3_path}'"
            )

        # Open and read image data
        with open(image_path, 'rb') as img_file:
            image_data: bytes = img_file.read()
            logger.debug(f"[Embed Cover] Read image file: '{image_path}'")

        # Embed the image as cover art
        audio.tags.add(  # pyright: ignore[reportOptionalMemberAccess, reportUnknownMemberType]
            APIC(
                encoding=3,  # UTF-8
                mime="image/png",  # Set MIME type to PNG
                type=3,  # 3 = Cover (front)
                desc="Cover",
                data=image_data,
            )
        )

        # Save the MP3 with new tag
        if not test_run:
            audio.save()  # pyright: ignore[reportUnknownMemberType]
        logger.info(
            f"[Embed Cover] Successfully embedded cover into '{mp3_path.name}'"
        )
        return True

    except Exception as e:
        logger.error(
            f"[Embed Cover] Failed to embed cover into '{mp3_path.name}': {e}"
        )
        return False


def remove_image_from_mp3(
    mp3_path: Path, image_path: Path, test_run: bool
) -> bool:
    """
    Removes any embedded cover art (APIC frames) from the MP3 file
    and deletes the separate image if provided.
    """
    try:
        audio = MP3(mp3_path, ID3=ID3)
        logger.debug(f"[Remove Cover] Loaded MP3: '{mp3_path}'")

        if audio.tags is None:  # pyright: ignore[reportUnknownMemberType]
            logger.debug(f"[Remove Cover] No ID3 tags found in '{mp3_path}'")
            return True

        # Collect APIC keys
        apic_keys = [
            key for key in list(audio.tags.keys()) if key.startswith("APIC")
        ]  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType, reportUnknownVariableType]
        if not apic_keys:
            logger.debug(
                f"[Remove Cover] No APIC frames found in '{mp3_path}'"
            )
            return True

        # Delete APIC frames
        for key in apic_keys:  # pyright: ignore[reportUnknownVariableType]
            logger.debug(
                f"[Remove Cover] Removing APIC frame '{key}' from '{mp3_path}'"
            )
            if not test_run:
                del audio.tags[key]  # pyright: ignore[reportUnknownMemberType]

        if not test_run:
            audio.save(
                v2_version=3
            )  # force save as ID3v2.3 for max compatibility  # pyright: ignore[reportUnknownMemberType]
            if image_path.exists():
                image_path.unlink(missing_ok=True)

        logger.info(
            f"[Remove Cover] Successfully removed {len(apic_keys)} cover(s) from '{mp3_path.name}'"
        )  # pyright: ignore[reportUnknownArgumentType]
        return True

    except Exception as e:
        logger.error(
            f"[Remove Cover] Failed to remove cover art from '{mp3_path.name}': {e}"
        )
        return False


def has_embedded_cover(mp3_path: Path) -> bytes | None:
    """
    Checks if the given MP3 file has a non-empty embedded front cover image
    and returns its bytes if present.

    :param mp3_path: Path to the MP3 file.
    :return: Tuple of (has_cover: bool, image_bytes: Optional[bytes])
    """
    try:
        audio = MP3(mp3_path, ID3=ID3)
        if audio.tags is None:  # pyright: ignore[reportUnknownMemberType]
            logger.debug(f"[Cover Check] No ID3 tags in '{mp3_path.name}'")
            return None

        for (
            tag
        ) in (
            audio.tags.values()
        ):  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
            if (
                isinstance(tag, APIC) and tag.type == 3
            ):  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
                if (
                    tag.data and len(tag.data) > 0
                ):  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType, reportAttributeAccessIssue]
                    logger.debug(
                        f"[Cover Check] Embedded cover image found in '{mp3_path.name}'"
                    )
                    return (
                        tag.data
                    )  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType, reportAttributeAccessIssue]
                else:
                    logger.debug(
                        f"[Cover Check] Found APIC tag but it has no data in '{mp3_path.name}'"
                    )
                    return None

        logger.debug(
            f"[Cover Check] No embedded cover image found in '{mp3_path.name}'"
        )
        return None

    except Exception as e:
        logger.error(f"[Cover Check] Error reading '{mp3_path.name}': {e}")
        return None
