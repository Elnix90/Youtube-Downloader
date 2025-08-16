# 🎵 YouTube Music Fetcher & Playlist Manager

This project automates the process of **fetching, downloading, and managing YouTube music videos**.  
It integrates with the **YouTube Data API v3** to access your liked videos or any playlist you choose, and uses `yt-dlp` for high-quality downloads.  
It also retrieves **artist names, track titles, and even song lyrics** for your library.
You can also Automaticaly add albums by fetching the title and author name of the songs or video. (Fully customisable)

---

## ✨ Features

- **Fetch & Download**
  - Download videos or audio from your liked videos or any playlist you specify.
  - Supports `mp3`, `wav`, and every format permitted by yt_dlp
  - Skips videos that are private or unavailable.

- **Playlist Management**
  - Add fetched videos to a playlist of your choice.
  - Remove private or deleted videos from playlists automatically.
  - Maintain lists of skipped or failed videos for review.

- **Metadata & Lyrics**
  - Can automatically extract artist, title, and uploader information.
  - Fetch lyrics with [syncedlyrics](https://github.com/moehmeni/syncedlyrics) (no token or api required)
  - Can automaticlaly add an album to your file, depending on what's inside the filename and author name

- **Error Handling**
  - Detects and skips private videos.
  - Keeps track of failed downloads in separate log files.

---

## 📦 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/yourrepo.git
   cd yourrepo
   ```

2. **Create and activate a virtual environment** (recommended)
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS / Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

---

## 🔑 API Setup

### YouTube Data API (OAuth 2.0)
- Create a project in the [Google Cloud Console](https://console.cloud.google.com/).
- Enable the **YouTube Data API v3**.
- Create an **OAuth Client ID** with the type "Desktop app".
- Download the `client_secret.json` file and place it in project-root/CREDS.


---

## ▶️ Usage

Run the main script to fetch and process your liked videos:

```bash
python main.py
```

By default:
- The script will check your liked videos playlist.
- Add them to a playlist or skip them based on your configuration.
- Download each song in the chosen format.
- Fetch and save lyrics when available.

You can modify the main function to:
- Use a different playlist ID.
- Change the output path and file format.
- Disable playlist modifications and only download.

I will make some other differents scripts like the main.py, to propose different logics to download, like a function who downloads only the content of a playlist

---

## 📂 Project Structure

```
├── main.py                           # Main function (fecthces liked and download liked explained [here](#usage))
├── download_videos_from_playlist.py  # Download function to download a playlist
├── ALBUMS                            # List of patterns to add to an album see [here](#features) to see how
├── CONFIG                            # Same as ALBUMS, but for lyrics fetching
├── CREDS                             # client-secret and token for google authenticating
├── TAGS                              # Same as 2 before but not yet implemented
├── FUNCTIONS/                        # Core features: download, playlist ops, file handling
├── CONSTANTS.py                      # Paths constants
├── requirements.txt                  # Python dependencies
├── README.md                         # This file
└── JSON                              # Where the big lists will downloaded (may be removed in the future)
```

---

## ⚠️ Notes & Limitations
- You must be signed in with a Google account that has access to the playlists/videos you want to process.
- Private videos will be skipped unless you provide cookies for authentication.
- Lyrics fetching relies syncedlyrics not all songs will have lyrics
- `yt-dlp` format support depends on YouTube’s availability.

---

## 🚀 Planned Improvements
- Interactive CLI or GUI for easier use.
- Config file for persistent settings.
- Batch processing with progress bars.
- More robust metadata matching for lyrics.
- easier customisation of tags, albums and lyrics

---

## 📝 License
This project is open-source under the MIT License.
