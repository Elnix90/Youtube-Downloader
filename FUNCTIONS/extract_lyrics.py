import re
import unicodedata
import os
import syncedlyrics
from pathlib import Path
from CONSTANTS import UNWANTED_PATTERNS_FILE,SKIP_LYRICS_PATERN_FILE
from FUNCTIONS.fileops import load_patterns



def clean_song_query(query):
    query = query.lower()

    # Normalize accents: à, é, ê -> a, e, e
    query = unicodedata.normalize('NFKD', query)
    query = query.encode('ASCII', 'ignore').decode('utf-8')

    # Remove unwanted patterns first
    patterns_to_remove = load_patterns(UNWANTED_PATTERNS_FILE)
    for pattern in patterns_to_remove:
        query = re.sub(pattern, '', query, flags=re.IGNORECASE)

    # Remove anything that's not a-z, A-Z, 0-9, space, or hyphen
    query = re.sub(r'[^a-zA-Z0-9\s-]', '', query)

    # Remove hyphens surrounded by spaces
    query = re.sub(r'\s*-\s*', ' ', query)

    # Collapse multiple spaces and strip edges
    query = re.sub(r'\s+', ' ', query).strip()

    # Capitalize words
    return query.title()


def get_lyrics_from_syncedlyrics(song_query):

    anti_lyrics = load_patterns(SKIP_LYRICS_PATERN_FILE)
    if any(anti in song_query.lower() for anti in anti_lyrics):
        return None, "Skipped due to unwanted pattern found", ""

    query = clean_song_query(song_query)

    print(" | Query: " + query,end='',flush=True)
    lyrics = syncedlyrics.search(query,plain_only=True,providers=["NetEase","Lrclib","Megalobiz"])

    #debug
    if lyrics:
        os.makedirs("Lyrics",exist_ok=True)
        with open(f"Lyrics/{query}.txt", 'w',encoding='utf-8') as f:
            f.write(lyrics)


        return lyrics, "Found", query
    else:
        return None, "Not found", query
