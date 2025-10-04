"""
Module to load and dump into json files
the list of video infos.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol, TypeVar, Generic, final, runtime_checkable

from FUNCTIONS.HELPERS.logger import setup_logger
from FUNCTIONS.HELPERS.types_playlist import PlaylistVideoEntry

logger = setup_logger(__name__)


@runtime_checkable
class APIModel(Protocol):
    """
    Protocol that defines methods for serializing and deserializing API models.
    """

    @classmethod
    def from_api_response(cls: type[_T], data: dict[str, object]) -> _T:
        """
        Construct an instance of the model from an API response dictionary.
        """
        ...

    def to_json(self) -> dict[str, object]:
        """Serialize the instance into a JSON-compatible dictionary."""
        ...


_T = TypeVar("_T", bound=APIModel)


@final
class JSONFileHandler(Generic[_T]):
    """Generic, type-safe JSON file handler."""

    def __init__(self, model: type[_T]) -> None:
        self.model = model

    def load(self, file: Path) -> list[_T]:
        """Load a JSON file into a list of model instances."""
        if not file.exists():
            msg = f"Error: '{file}' does not exist"
            logger.error(msg)
            raise FileNotFoundError(msg)

        try:
            with file.open("r", encoding="utf-8") as f:
                raw: object = json.load(f)  # pyright: ignore[reportAny]
        except json.JSONDecodeError as e:
            msg = f"Error decoding JSON in '{file}': {e}"
            logger.error(msg)
            raise ValueError(msg) from e

        if not isinstance(raw, list):
            msg = f"Expected a JSON list in '{file}', got {type(raw).__name__}"
            logger.error(msg)
            raise ValueError(msg)

        result: list[_T] = []
        for entry in raw:  # pyright: ignore[reportUnknownVariableType]
            if isinstance(entry, self.model):
                result.append(entry)
            elif isinstance(entry, dict):
                # Safely call factory constructor
                if hasattr(self.model, "from_api_response"):
                    model_instance = self.model.from_api_response(entry)  # pyright: ignore[reportUnknownArgumentType]
                    if not isinstance(model_instance, self.model):
                        msg = (
                            "from_api_response returned invalid type:" +
                            f"{type(model_instance)}"
                        )
                        logger.error(msg)
                        raise TypeError(msg)
                    result.append(model_instance)
                else:
                    msg = f"Model '{self.model.__name__}' missing from_api_response method"
                    logger.error(msg)
                    raise TypeError(msg)
            else:
                msg = f"Unexpected entry type in '{file}': {type(entry)}"  # pyright: ignore[reportUnknownArgumentType]
                logger.error(msg)
                raise ValueError(msg)

        logger.debug(f"[Load] Loaded {len(result)} entries from '{file}'")
        return result




    def dump(self, data: list[_T], file: Path) -> None:
        """Write a list of model instances to a JSON file."""
        temp_file = file.with_suffix(file.suffix + ".bak")

        # Create a backup if file already exists
        if file.exists():
            _ = temp_file.write_bytes(file.read_bytes())

        try:
            json_ready: list[dict[str, object]] = []
            for d in data:
                if hasattr(d, "to_json"):
                    json_ready.append(d.to_json())  # type: ignore[call-arg]
                elif isinstance(d, dict):
                    json_ready.append(d)  # type: ignore[arg-type]
                else:
                    msg = f"Invalid item type for JSON dump: {type(d)}"
                    logger.error(msg)
                    raise TypeError(msg)

            with file.open("w", encoding="utf-8") as f:
                json.dump(json_ready, f, indent=2, ensure_ascii=False)

            if temp_file.exists():
                temp_file.unlink()

            logger.debug(f"[Dump] Successfully dumped {len(data)} entries to '{file}'")

        except Exception as e:
            # Restore backup if writing fails
            if temp_file.exists():
                _ = file.write_bytes(temp_file.read_bytes())
                temp_file.unlink()
            logger.exception(f"[Dump] Error dumping to '{file}': {e}")
            raise


handler = JSONFileHandler(PlaylistVideoEntry)
