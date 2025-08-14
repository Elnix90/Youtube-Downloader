# 🎵 YouTube Downloader

This project automates the process of fetching, downloading, and managing YouTube music videos.  
It integrates with the YouTube Data API v3 to access your liked videos or any playlist you choose, and uses `yt-dlp`.  
It also retrieves artist names, track titles, and even song lyrics for your library.

---

## Features

- **Fetch & Download**
  - Download videos or audio from your liked videos or any playlist you specify.
  - Supports `mp3` and `wav`.
  - Skips videos that are private or unavailable.

- **Playlist Management**
  - Add fetched videos to a playlist of your choice.
  - Remove private or deleted videos from playlists automatically.
  - Maintain lists of skipped or failed videos for review.

- **Metadata & Lyrics**
  - Automatically extract artist, title, and uploader information.
  - Fetch lyrics from Genius for each song (requires Genius API token).
  - Clean up messy YouTube titles (removes “lyrics”, “nightcore”, “official video”, etc.).

- **Error Handling**
  - Detects and skips private videos.
  - Keeps track of failed downloads in separate log files.
  - Gracefully handles API errors from YouTube or Genius.

---

## 📦 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/yourrepo.git
   cd yourrepo```

2. **Create and activate a virtual environment (recommended)**
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS / Linux
source venv/bin/activate
```

3. **Install dependencies**

pip install -r requirements.txt
