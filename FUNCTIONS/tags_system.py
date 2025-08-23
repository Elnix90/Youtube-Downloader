from pathlib import Path
from typing import Set, Optional
import re

from CONSTANTS import TAGS_DIR
from FUNCTIONS.metadata import get_artist_tags,write_artist_tags



def contains_whole_word(text: str, word: str) -> bool:
    pattern = rf'\b{re.escape(word)}\b'
    return re.search(pattern, text, flags=re.IGNORECASE) is not None



def compute_tags(title: str, uploader: str) -> Set[str]:
    tags: Set[str] = set()

    if not TAGS_DIR.exists() or not TAGS_DIR.is_dir():
        return tags

    for tag_file in TAGS_DIR.glob("*.txt"):
        # Determine if this is a positive (tag_) or negative (notag_) file
        filename = tag_file.stem

        if filename.startswith("tag_"):
            tag_name = filename[len("tag_"):]
            try:
                lines = tag_file.read_text(encoding="utf-8").splitlines()
            except Exception:
                continue

            for line in lines:
                if "#" not in line:
                    word = line.strip()
                    if word and (contains_whole_word(title, word) or contains_whole_word(uploader, word)):
                        tags.add(tag_name)
                        break

        elif filename.startswith("notag_"):
            tag_name = filename[len("notag_"):]
            try:
                lines = tag_file.read_text(encoding="utf-8").splitlines()
            except Exception:
                continue

            present = False
            for line in lines:
                if "#" not in line:
                    word = line.strip()
                    if word and (contains_whole_word(title, word) or contains_whole_word(uploader, word)):
                        present = True
                        break
            if not present:
                tags.add(tag_name)
                
    return tags



def get_tags(filepath: Path) -> Set[str]:
    sep: str = " ~ ["
    title, state = get_artist_tags(filepath)
    if state == 0 and isinstance(title, str):
        if title.endswith("]") and sep in title:
            start = title.rfind(sep) + len(sep)
            end = len(title) - 1  # position before the closing ']'
            tags_part = title[start:end]
            tags = set([tag.strip() for tag in tags_part.split(",") if tag.strip()])
            return tags
    return set()



def set_tags(filepath: Path, tags: set[str]) -> Optional[str]:
    if filepath.exists():
        sep: str = " ~ ["
        # Ensure all tags are lowercase and unique
        tags = {tag.lower() for tag in tags if tag.isalnum()}
        title, state = get_artist_tags(filepath)
        if state == 0 and isinstance(title, str):
            # Remove existing tags part from name if present
            if title.endswith("]") and sep in title:
                title = title[:title.rfind(sep)]

            # If there are no tags and the name has, remove the tags part
            if tags:
                new_title = f"{title}{sep}{', '.join(sorted(tags))}]"
            else:
                new_title = title

            if new_title != title:
                write_artist_tags(filepath,new_title)
                return new_title + filepath.suffix


