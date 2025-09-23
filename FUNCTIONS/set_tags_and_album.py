from pathlib import Path



from FUNCTIONS.metadata import read_id3_tag, write_id3_tag

from FUNCTIONS.HELPERS.logger import setup_logger
logger = setup_logger(__name__)





def extract_tags_from_str(
    text: str,
    sep: str,
    start_def: str,
    end_def: str,
    tag_sep: str
) -> tuple[str, set[str]]:
    """
    Extract tags and base text from a given string if they are embedded in the form (with default parameters, if you change them the form changes too):
    'title ~ [tag1, tag2, tag3]'
    :param text: Input string (e.g., a title).
    :param sep: Separator used before the tags block.
    :param start_def: the start of the tags block.
    :param end_def: the end of the tags block.
    :param tag_sep: the string used to separate the tags.
    :return: Tuple of (base_text, tags_set)
    """
    if not text:
        return "", set()

    if text.endswith(end_def) and sep in text:
        sep_pos = text.rfind(sep)
        base_text = text[:sep_pos].rstrip()

        start = sep_pos + len(sep + start_def)
        end = len(text) - len(end_def)
        tags_part = text[start:end]
        tags = {tag.strip().lower() for tag in tags_part.split(tag_sep) if tag.strip()}
        return base_text, tags

    return text, set()







def put_tags_in_str(
    base_text: str,
    tags: set[str],
    sep: str,
    start_def: str,
    end_def: str,
    tag_sep: str
) -> str:
    """
    Insert tags into a base string, replacing any existing tags in the form (with default parameters, if you change them the form changes too):
    'title ~ [tag1, tag2, tag3]'

    :param base_text: Input string (without enforced tags).
    :param tags: Set of tags to embed.
    :param sep: Separator used before the tags block.
    :param start_def: the start of the tags block.
    :param end_def: the end of the tags block.
    :param tag_sep: the string used to separate the tags.
    :return: String with tags embedded.
    """
    if not base_text:
        return ""

    # Remove any existing tags part
    if base_text.endswith(end_def) and sep in base_text:
        base_text = base_text[:base_text.rfind(sep)]

    if tags:
        # Ensure tags are lowercase, unique, and sorted for consistency
        clean_tags = sorted({tag.lower().strip() for tag in tags if tag.strip()})
        return f"{base_text}{sep}{start_def}{tag_sep.join(clean_tags)}{end_def}"

    return base_text







def set_tags(
    filepath: Path,
    tags: set[str],
    error: bool,
    test_run: bool,
    sep: str = " ~ ",
    start_def: str = "[",
    end_def: str = "]",
    tag_sep: str = ","
) -> bool:
    if filepath.exists():
        tags = {tag.lower() for tag in tags if tag.isalnum()}
        artist, state = read_id3_tag(filepath=filepath,frame_id="TPE1")
        if state in (0, 1):
            if isinstance(artist, list):
                artist = artist[0]

            
            base_text, tags_set = extract_tags_from_str(text=artist,sep=sep, start_def=start_def, end_def=end_def, tag_sep=tag_sep)
            new_tags: set[str] = tags_set.union(tags)

            new_artist: str = put_tags_in_str(base_text=base_text,tags=new_tags, sep=sep, start_def=start_def, end_def=end_def, tag_sep=tag_sep)

            if new_tags != tags_set:
                sucess = write_id3_tag(filepath=filepath, frame_id="TPE1", data=new_artist, test_run=test_run)
                if sucess:
                    logger.info(f"[Set Tags] Sucessfully set {len(tags)} tags into '{filepath}'")
                    return True
                else:
                    logger.error(f"[Set Tags] Error writing {len(tags)} tags into '{filepath}'")
                    return False
            else:
                logger.info(f"[Set Tags] Tags already present are the same, did nothing in '{filepath}'")
                return True
        else:
            logger.error(f"[Set Tags] Exeption during getting tags, did not try to set them in '{filepath}'")
            return False
    else:
        if error: print(f"\n[Set Tags] Filepath provided doesn't exists: '{filepath}'")
        logger.error(f"[Set Tags] Filepath provided doesn't exists: '{filepath}'")
        return False
    



def set_album(
    filepath: Path,
    album: str,
    test_run: bool = False
) -> bool:
    """
    Embed album info into MP3 file and update DB flag `update_album`.
    """

    if not filepath.exists():
        logger.error(f"[set Album] Filepath doesn't exist: '{filepath}'")
        return False

    success = write_id3_tag(filepath=filepath, frame_id="TALB", data=album, test_run=test_run)
    if success:
        logger.verbose(f"[set Album] Album set to '{album}' for '{filepath}'")
        return True
    else:
        logger.error(f"[set Album] Failed to set album '{album}' for '{filepath}'")
        return False
