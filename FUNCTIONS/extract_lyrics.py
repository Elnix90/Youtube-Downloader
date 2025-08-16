import re
import os
import syncedlyrics


def clean_song_query(query):
    # Lowercase first
    query = query.lower()

    # Remove common unwanted patterns
    patterns_to_remove = [
        r'\(.*?\)', r'\[.*?\]', r'lyrics', r'official', r'official video',
        r'remix', r'video clip', r'feat\. .*', r'ft',r'edit',r'radio', r'dj', r'Dj', r'DJ', r'DJ'
    ]
    for pattern in patterns_to_remove:
        query = re.sub(pattern, '', query, flags=re.IGNORECASE)

    # Remove anything that's not a-z, A-Z, 0-9, space, or hyphen
    query = re.sub(r'[^a-zA-Z0-9\s-]', '', query)

    # Remove hyphens that are at the start or preceded by spaces, plus extra spaces
    query = re.sub(r'\s*-\s*', ' ', query)

    # Collapse multiple spaces into one and strip
    query = re.sub(r'\s+', ' ', query).strip()

    # Capitalize words
    return query.title()


def get_lyrics_from_syncedlyrics(song_query):

    anti_lyrics = ['nightcore','nightstep','amv']
    if any(anti in song_query.lower() for anti in anti_lyrics): # Probably a remix or something else so do not try do fetch the lyrics
        return None

    query = clean_song_query(song_query)

    print(" | Query: " + query,end='',flush=True)
    lyrics = syncedlyrics.search(query,plain_only=True,providers=["NetEase","Lrclib","Megalobiz"])

    #debug
    if lyrics:
        os.makedirs("Lyrics",exist_ok=True)
        with open(f"Lyrics/{query}.txt", 'w',encoding='utf-8') as f:
            f.write(lyrics)


        return lyrics
    else:
        return None
