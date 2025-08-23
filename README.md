# 🎵 YouTube Music Fetcher & Playlist Manager

This project automates the process of **fetching, downloading, and managing YouTube music videos**.  
It integrates with the **YouTube Data API v3** to access your liked videos or any playlist you choose, and uses `yt-dlp` for high-quality downloads.  
It also retrieves **artist names, track titles, and even song lyrics** for your library.
You can also Automaticaly add lyrics or tags by fetching the title and uploader name of the songs or video (Fully customisable), and remove segments via sponsorblock


---

## ✨ Features

- **Fetch & Download**
  - Download videos or audio from your liked videos or any playlist you specify.
  - Supports only `mp3` due to tags, lyrics and metadatas usage but may extend to other formats in the future
  - Skips videos that are private or unavailable.

- **Playlist Management**
  - Add fetched videos to a playlist of your choice.
  - Remove private or deleted videos from playlists automatically.
  - Maintain lists of skipped or failed videos for review.

- **Metadata & Lyrics**
  - Can automatically extract artist, title, and uploader information.
  - Fetch lyrics with [syncedlyrics](https://github.com/moehmeni/syncedlyrics) (no token or api required)
  - Can automaticlaly add tags to your file, depending on what's inside the filename and uploader name
  - can automaticly remove segments marked from sponsorblock

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

4. **Set your environnement variables**
    Create a .env file with the following content:
    ```env
    musicpath=path/to/your/list/musi.json
    downloadpath=path/where/the/files/will/be/downloaded
    playlistid=the_id_of_your_playlist
    ```
    Only downloadpath is really needed, as it will raise an error if not set, the 2 other are optionnal depending of what function you use
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
# There are 3 pre-build functions: 

  1. **process_new_liked_videos :** (Mainly abandonned to main_list_process dev)

  - The script will check your liked videos playlist.
  - Add them to a playlist or skip them based on your configuration.
  - Download each song in the chosen format.
  - Fetch and save lyrics when available.

  You can modify the main function to:
  - Use a different playlist ID.
  - Change the output path and file format.
  - Disable playlist modifications and only download.

  I will make some other differents scripts like the main.py, to propose different logics to download, like a function who downloads only the content of a playlist

  2. **download_videos_from_playlist :**

  - I think this one's clear, but for more infos: download every video from a playlist

  3. **main_list_process :**
  - This is the very heart of my code now, it uses a Json list to know state of files, and videos downloaded.
  - You can add tags to the list from your phone for exeample and the next time you run the programm, they will be added to your files



---

## 📂 Project Structure

```
├── main.py                           # Main function (fetches liked and download liked explained [here](#usage))
├── .env                              # Your environnemnt variable file
├── CONFIG                            # List of patterns to correctly fecth lyrics, by cleaning the messy title of youtube
├── CREDS                             # client-secret and token for google authentication
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
- Tags automaticly searching is only dependent of your customisation
- `yt-dlp` format support depends on YouTube’s availability.

---

## 🚀 Planned Improvements
- Interactive CLI or GUI for easier use -> maybe in 2 years lol
- Config file for persistent settings.
- Batch processing with progress bars. -> Already a part of it is done, with global ETA and download progress
- easier customisation of tags and lyrics
- Usage of logging module for cleaner output -> My system must be improved cause i got issues with synced lyrics and they where resolved with logging module, see firsts lines of [extract_lyrics.py](https://github.com/Elnix90/Youtube-Downloader/blob/master/FUNCTIONS/extract_lyrics.py)

---

## 📝 License
This project is open-source under the MIT License.
