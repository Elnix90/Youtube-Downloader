import re
from pathlib import Path


from FUNCTIONS.HELPERS.text_helpers import load_patterns, sanitize_text, contains_whole_word


def matches_patterns(text: str, patterns: set[str]) -> bool:
    """Check if any pattern (regex or keyword) matches the text"""
    for pat in patterns:
        if pat.startswith("re:"):
            regex = pat[3:].strip()
            if re.search(regex, text, flags=re.IGNORECASE):
                return True
        else:
            word = sanitize_text(pat)
            if word and contains_whole_word(text=text, word=word):
                return True
    return False


def compute_tag_set_from_file(texts: tuple[str, str], tag_file_path: Path) -> tuple[str | None, bool]:
    """Return a tag name and whether it should be added or blocked based on patterns file"""
    title_norm, uploader_norm = texts
    filename = tag_file_path.stem
    patterns = load_patterns(file=tag_file_path)
    
    if filename.startswith("tag_"):
        tag_name = filename[len("tag_"):]
        add_tag = False
        for line in patterns:
            negated = line.startswith("-")
            line = line[1:].strip() if negated else line.strip()
            if line.startswith("re:"):
                regex = line[3:].strip()
                match = re.search(regex, title_norm) or re.search(regex, uploader_norm)
            else:
                match = contains_whole_word(title_norm, line) or contains_whole_word(uploader_norm, line)
            if match:
                add_tag = not negated
                break
        return tag_name, add_tag
    
    elif filename.startswith("notag_"):
        tag_name = filename[len("notag_"):]
        present = matches_patterns(title_norm, set(patterns)) or matches_patterns(uploader_norm, set(patterns))
        return tag_name, not present  # add if not present

    return None, False