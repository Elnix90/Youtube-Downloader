from pathlib import Path
from typing import Any, Dict, Tuple, Optional
import json
from mutagen.mp3 import MP3  # type: ignore
from mutagen.id3 import ID3
from mutagen.id3 import TXXX  # type: ignore
from mutagen.id3._frames import TCON, TPE1, TIT2


def get_metadata_tag(filepath: Path, tag: str = 'metadata') -> Tuple[Dict[str, Any] | None, int]:
    """Return metadata from an MP3 file, and a state code (0=ok, 1=malformed, 2=corrupted, 3=empty data)."""
    try:
        audio: MP3 | None = MP3(str(filepath), ID3=ID3)
        if audio.tags is not None: # type: ignore
            comments = audio.tags.getall('TXXX') # type: ignore
            for comment in comments: # type: ignore
                if isinstance(comment, TXXX) and comment.desc.lower() == tag.lower(): # type: ignore
                    try:
                        data = json.loads(comment.text[0]) # type: ignore
                    except Exception:
                        return None, 1
                    if data: return data, 0
                    else: return None, 3
    except Exception:
        return None, 2
    return None, 1



def write_metadata_tag(filepath: Path, metadata: Dict[str, Any], tag: str = 'metadata') -> bool:
        """Write metadata to an MP3 file under the specified tag."""
        try:
            audio: MP3 | None = MP3(str(filepath), ID3=ID3)  # type: ignore
            if audio.tags is None: # type: ignore
                audio.add_tags() # type: ignore
            metadata_str = json.dumps(metadata, ensure_ascii=True)
            audio.tags.add(TXXX(encoding=3, desc=tag, text=metadata_str))  # type: ignore
            audio.save() # type: ignore
            return True
        except Exception as e:
            print(f"\nError writing metadata to {filepath}: {e}")
            return False






def get_title_tag(filepath: Path) -> Tuple[Optional[str], int]:
    """
    Return the title from an MP3 file, and a state code:
      0 = ok
      1 = not found
      2 = corrupted/unreadable
    """
    try:
        audio: MP3 | None = MP3(str(filepath), ID3=ID3)
        if audio.tags is not None:  # type: ignore
            title_frame = audio.tags.get("TIT2")  # type: ignore
            if title_frame is not None:
                return str(title_frame.text[0]), 0  # type: ignore
            else:
                return None, 1
    except Exception:
        return None, 2
    return None, 1



def write_title_tag(filepath: Path, title: str) -> bool:
    """
    Write a title to an MP3 file (overwrites existing title).
    Returns True on success, False on failure.
    """
    try:
        audio: MP3 | None = MP3(str(filepath), ID3=ID3)  # type: ignore
        if audio.tags is None:  # type: ignore
            audio.add_tags()  # type: ignore
        audio.tags["TIT2"] = TIT2(encoding=3, text=title)  # type: ignore
        audio.save()  # type: ignore
        return True
    except Exception as e:
        print(f"\nError writing title to {filepath}: {e}")
        return False



def get_artist_tags(filepath: Path) -> Tuple[Optional[str], int]:
    """Read artist field from MP3"""
    try:
        audio: MP3 | None = MP3(str(filepath), ID3=ID3)
        if audio.tags is not None:  # type: ignore
            artist_frame = audio.tags.get("TPE1")  # type: ignore
            if artist_frame is not None and artist_frame.text:  # type: ignore
                return str(artist_frame.text[0]), 0  # type: ignore
            return None, 1
    except Exception:
        return None, 2
    return None, 1



def write_artist_tags(filepath: Path, artist_str: str) -> bool:
    """Write tags to the artist field of an MP3 using ~ [tag1,tag2] format."""
    try:
        audio: MP3 | None = MP3(str(filepath), ID3=ID3)  # type: ignore
        if audio.tags is None:  # type: ignore
            audio.add_tags()  # type: ignore
        audio.tags["TPE1"] = TPE1(encoding=3, text=artist_str)  # type: ignore
        audio.save()  # type: ignore
        return True
    except Exception as e:
        print(f"Error writing artist tags: {e}")
        return False



def get_genre_tag(filepath: Path) -> tuple[Optional[str], int]:
    """Read genre string from MP3."""
    try:
        audio: MP3 | None = MP3(str(filepath), ID3=ID3)
        if audio.tags is not None:  # type: ignore
            genre_frame = audio.tags.get("TCON")  # type: ignore
            if genre_frame is not None and genre_frame.text:  # type: ignore
                return str(genre_frame.text[0]), 0 # type: ignore
            return None, 1
    except Exception:
        return None, 2
    return None, 1



def write_genre_tag(filepath: Path, genre: str) -> bool:
    """Write genre string to MP3."""
    try:
        audio: MP3 | None = MP3(str(filepath), ID3=ID3)  # type: ignore
        if audio.tags is None:  # type: ignore
            audio.add_tags()  # type: ignore
        audio.tags["TCON"] = TCON(encoding=3, text=genre)  # type: ignore
        audio.save()  # type: ignore
        return True
    except Exception:
        return False