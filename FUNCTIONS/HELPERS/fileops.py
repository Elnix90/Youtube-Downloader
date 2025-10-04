"""
Module to load and dump into JSON files
the list of video infos.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import (
    Any,
    Generic,
    Protocol,
    TypeVar,
    cast,
    final,
    runtime_checkable,
)

from FUNCTIONS.HELPERS.logger import setup_logger
from FUNCTIONS.HELPERS.types_playlist import PlaylistVideoEntry

logger = setup_logger(__name__)


# ---------------------------------------------------------------------
# Type-safe API model protocol
# ---------------------------------------------------------------------

_I_contra = TypeVar("_I_contra", contravariant=True)
_T = TypeVar("_T", bound="APIModel")


@runtime_checkable
class APIModel(Protocol):
    """
    Protocol for JSON-serializable API models.
    """

    @classmethod
    def from_api_response(cls: type[_T], data: dict[str, object]) -> _T:
        """Construct instance from API response dict."""
        ...  # pylint: disable=unnecessary-ellipsis

    def to_json(self) -> dict[str, object]:
        """Serialize instance into JSON-compatible dict."""
        ...  # pylint: disable=unnecessary-ellipsis


# ---------------------------------------------------------------------
# Generic JSON file handler
# ---------------------------------------------------------------------


@final
class JSONFileHandler(Generic[_T]):
    """Generic, type-safe JSON file handler."""

    def __init__(self, model: type[_T]) -> None:
        self.model = model

    def load(self, file: Path) -> list[_T]:
        """Load a JSON file into model instances."""
        if not file.exists():
            msg = f"Error: '{file}' does not exist"
            logger.error(msg)
            raise FileNotFoundError(msg)

        try:
            with file.open("r", encoding="utf-8") as f:
                raw = cast(list[dict[str, object]], json.load(f))
        except json.JSONDecodeError as exc:
            msg = f"Error decoding JSON in '{file}': {exc}"
            logger.error(msg)
            raise ValueError(msg) from exc

        result: list[_T] = []
        for entry in raw:
            if isinstance(entry, self.model):
                result.append(entry)

            if hasattr(self.model, "from_api_response"):
                model_instance = self.model.from_api_response(entry)
                if not isinstance(model_instance, self.model):
                    msg = (
                        f"Invalid type from from_api_response: "
                        f"{type(model_instance)}"
                    )
                    logger.error(msg)
                    raise TypeError(msg)
                result.append(model_instance)
            else:
                msg = (
                    f"Model '{self.model.__name__}' missing "
                    "'from_api_response' method"
                )
                logger.error(msg)
                raise TypeError(msg)
        # else:
        #     msg = f"Unexpected entry type in '{file}': {type(entry)}"
        #     logger.error(msg)
        #     raise ValueError(msg)

        logger.debug(f"[Load] Loaded {len(result)} entries from '{file}'")
        return result

    def dump(self, data: list[_T], file: Path) -> None:
        """Write model instances to JSON file safely with backup."""
        temp_file = file.with_suffix(file.suffix + ".bak")

        if file.exists():
            _ = temp_file.write_bytes(file.read_bytes())

        try:
            json_ready: list[dict[str, object]] = []
            for d in data:
                if hasattr(d, "to_json"):
                    json_ready.append(d.to_json())  # type: ignore[call-arg]
                elif isinstance(d, dict):
                    json_ready.append(d)
                else:
                    msg = f"Invalid type for JSON dump: {type(d)}"
                    logger.error(msg)
                    raise TypeError(msg)

            with file.open("w", encoding="utf-8") as f:
                json.dump(json_ready, f, indent=2, ensure_ascii=False)

            if temp_file.exists():
                temp_file.unlink()

            logger.debug(
                f"[Dump] Successfully dumped {len(data)} entries to '{file}'"
            )

        except OSError as exc:
            if temp_file.exists():
                _ = file.write_bytes(temp_file.read_bytes())
                temp_file.unlink()
            logger.exception(f"[Dump] OS error dumping to '{file}': {exc}")
            raise


# Instantiate handler
# pylint: disable=line-too-long
handler: JSONFileHandler[Any] = JSONFileHandler(
    PlaylistVideoEntry
)  # pyright: ignore[reportExplicitAny]
# pylint: enable=line-too-long
