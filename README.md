# 🎵 YouTube Music Fetcher & Playlist Manager

This project automates the process of **fetching, downloading, and managing YouTube music videos**.  
It integrates with the **YouTube Data API v3** to access your liked videos or any playlist you choose, and uses `yt-dlp` for high-quality downloads.  
It also retrieves **artist names, track titles, and even song lyrics** for your library.

---

## ✨ Features

- **Fetch & Download**
  - Download videos or audio from your liked videos or any playlist you specify.
  - Supports `mp3`, `wav`.
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

### 1. YouTube Data API (OAuth 2.0)
- Create a project in the [Google Cloud Console](https://console.cloud.google.com/).
- Enable the **YouTube Data API v3**.
- Create an **OAuth Client ID** with the type "Desktop app".
- Download the `client_secret.json` file and place it in project-root/CREDS.

### 2. Genius API
- Create an account on [Genius](https://genius.com/).
- Create an API client and copy your **Access Token**.
- Store it in a `.env` file:
  ```
  GENIUS_API_TOKEN=your_token_here
  ```

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

---

## 📂 Project Structure

```
├── main.py                  # Entry point of the program
├── FUNCTIONS/               # Core features: download, playlist ops, file handling
├── CONSTANTS.py              # Paths and configuration constants
├── requirements.txt          # Python dependencies
├── .env                      # API keys and tokens
├── README.md                 # This file
├── CREDS                     # client-secret and token for google authenticating
└── JSON                      # Where the big lists are downloaded
```

---

## ⚠️ Notes & Limitations
- You must be signed in with a Google account that has access to the playlists/videos you want to process.
- Private videos will be skipped unless you provide cookies for authentication.
- Lyrics fetching relies on Genius API results — not all songs will have lyrics available.
- `yt-dlp` format support depends on YouTube’s availability.

---

## 🚀 Planned Improvements
- Interactive CLI or GUI for easier use.
- Config file for persistent settings.
- Batch processing with progress bars.
- More robust metadata matching for lyrics.

---

## 📝 License
This project is open-source under the MIT License.
