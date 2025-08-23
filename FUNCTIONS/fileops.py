import json
from pathlib import Path
from typing import Any, Set


def load(file: Path) -> Any:
    """Load JSON content from a file and return it as a Python object."""
    try:
        with file.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Error: {file} doesn't exist")


def dump(data: Any, file: Path) -> None:
    """Dump Python data to a JSON file, backing up the original before writing."""
    temp_file = file.with_suffix(file.suffix + ".bak")
    if file.exists():
        temp_file.write_bytes(file.read_bytes())
    try:
        with file.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        if temp_file.exists():
            temp_file.unlink() # Remove backup after successful dump
    except Exception as e:
        # Restore backup if dump fails
        if temp_file.exists():
            file.write_bytes(temp_file.read_bytes())
            temp_file.unlink()
        raise e


def load_patterns(file_path: Path) -> Set[str]:
    """Load non-comment patterns from a file into a set."""
    path = Path(file_path)
    if not path.exists():
        return set()
    patterns: Set[str] = set()
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip() and not line.strip().startswith("#"):
                patterns.add(line.strip())
    return patterns
