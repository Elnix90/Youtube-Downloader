import os
from pathlib import Path
from CONSTANTS import ALBUMS_DIR,TAGS_DIR
from FUNCTIONS.fileops import load_patterns



def get_album(title,author_name):
    if Path(ALBUMS_DIR).exists():
        for file in os.listdir(ALBUMS_DIR):
            if file[:5] == "album":
                album_name = file[6:-4]
                patterns = load_patterns(ALBUMS_DIR / file)
                if any((pattern in title.lower() for pattern in patterns) or (pattern in author_name.lower() for pattern in patterns)):
                    return album_name

    return "Private"




def get_tags(title,author_name):
    if Path(TAGS_DIR).exists():
        tags = []
        for file in os.listdir(TAGS_DIR):
            if file[:3] == "tag":
                tag_name = file[4:-4]
                patterns = load_patterns(ALBUMS_DIR / file)
                if any((pattern in title.lower() for pattern in patterns) or (pattern in author_name.lower() for pattern in patterns)):
                    tags.append(tag_name)
        

    return []