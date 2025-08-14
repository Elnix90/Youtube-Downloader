import re
import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
GENIUS_API_TOKEN = os.getenv("GENIUS_API_TOKEN")


def extract_lyrics(raw_text):
    """
    Remove all text before the actual lyrics start.
    Lyrics typically start with [Intro], [Verse], [Chorus], or first lyric line.
    """
    lines = raw_text.splitlines()
    cleaned_lines = []

    lyrics_started = False
    for line in lines:
        line = line.strip()
        if not line:
            continue  # skip empty lines

        # Detect start of lyrics
        if not lyrics_started:
            if re.match(r'\[.*\]', line) or re.match(r'^[A-Za-z].*', line):
                lyrics_started = True
            else:
                continue  # skip everything before lyrics

        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)

def clean_song_query(query):
    query = query.lower()
    patterns_to_remove = [
        r'\(.*?\)', r'\[.*?\]', r'lyrics', r'official', r'official video',
        r'remix', r'nightcore', r'video clip', r'feat\. .*'
    ]
    for pattern in patterns_to_remove:
        query = re.sub(pattern, '', query, flags=re.IGNORECASE)
    query = re.sub(r'[^a-zA-Z0-9\s-]', '', query)
    query = re.sub(r'\s+', ' ', query).strip()
    return query.title()

def get_lyrics_from_genius(song_query):
    if not GENIUS_API_TOKEN:
        print("Error: Genius API token not set")
        return None

    headers = {"Authorization": f"Bearer {GENIUS_API_TOKEN}"}
    base_url = "https://api.genius.com/search"

    def search(query):
        try:
            response = requests.get(base_url, headers=headers, params={"q": query}, timeout=10)
            response.raise_for_status()
            hits = response.json().get("response", {}).get("hits", [])
            if not hits:
                return None

            song_url = hits[0]["result"]["url"]
            html = requests.get(song_url, timeout=10).text
            soup = BeautifulSoup(html, "html.parser")
            lyrics_divs = soup.find_all("div", {"data-lyrics-container": "true"})
            if not lyrics_divs:
                return None
            lyrics = "\n".join(div.get_text(separator="\n").strip() for div in lyrics_divs)
            return lyrics or None

        except requests.RequestException as e:
            print(f"Request error: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

    # Try original query
    lyrics = search(song_query)
    if lyrics:
        return extract_lyrics(lyrics)

    # Try cleaned query
    cleaned_query = clean_song_query(song_query)
    if cleaned_query != song_query:
        lyrics = search(cleaned_query)
        if lyrics:
            return extract_lyrics(lyrics)
        
    return "Lyrics not found"