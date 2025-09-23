import json
from pathlib import Path
from typing import cast



from FUNCTIONS.HELPERS.logger import setup_logger
logger = setup_logger(__name__)






def load(file: Path) -> list[str]:
    """Load JSON content from a file and return it as a list of strings"""
    try:
        with file.open("r", encoding="utf-8") as f:
            raw = json.load(f)  # pyright: ignore[reportAny]

        if isinstance(raw, list) and all(isinstance(val, str) for val in raw):  # pyright: ignore[reportUnknownVariableType]
            logger.verbose(f"[Load] Successfully loaded '{file}'")
            return cast(list[str], raw)

        logger.warning(f"[Load] Invalid format in '{file}', expected list[str]")
        return []

    except FileNotFoundError:
        raise FileNotFoundError(f"Error: '{file}' doesn't exist")
    except json.JSONDecodeError as e:
        raise ValueError(f"Error: '{file}' cannot be decoded -> {e}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error loading '{file}': {e}")





def dump(data: list[str], file: Path) -> None:
    """Dump Python data to a JSON file, backing up the original before writing"""
    temp_file = file.with_suffix(file.suffix + ".bak")
    if file.exists():
        _ = temp_file.write_bytes(file.read_bytes())
    try:
        with file.open("w", encoding="utf-8") as f:
            logger.verbose(f"[Dump] Sucessfully dumped new data '{file}'")
            json.dump(data, f, indent=2)
        if temp_file.exists():
            temp_file.unlink() # Remove backup after successful dump
    except Exception as e:
        # Restore backup if dump fails
        if temp_file.exists():
            _ = file.write_bytes(temp_file.read_bytes())
            temp_file.unlink()
        raise e








