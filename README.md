# 🎵 YouTube Music Fetcher & Playlist Manager

This project automates the process of **fetching, downloading, and managing YouTube music videos**.  
It integrates with the **YouTube Data API v3** to access your liked videos or any playlist you choose, and uses `yt-dlp` to downloads.  
It also retrieves artist names, track titles, youtube thumbnails and some other metadata.
You can also Automaticaly add lyrics or tags by fetching the title and uploader name of the songs or video (Fully customisable), and remove segments via sponsorblock


---

## ✨ Features

- **Fetch & Download**
  - Download videos or audio from any playlist (default liked_videos).
  - Supports only `mp3` due to tags, lyrics and metadatas usage but may extend to other formats in the future
  - Skips videos that are private or unavailable.

- **Metadata & Lyrics**
  - Can automatically extract artist, title, and uploader information.
  - Fetch lyrics with [syncedlyrics](https://github.com/moehmeni/syncedlyrics) (no token or api required), or the youtube subtitles if there are some, in this order: manual subtitles > syncedlyrics > auto subtitles
  - Can automaticlaly add tags to your file, depending on what's inside the filename and uploader name, cuctomise that here
  - can automaticly remove segments marked from sponsorblock

- **Error Handling**
  - Detects and skips private videos.
  - Keeps track of failed downloads in separate log files.


---

## 📦 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Elnix90/Youtube-Downloader.git
   cd Youtube-Downloader
   ```

2. **Create and activate a virtual environment** (recommended) (linux) (f*ck windows if you have only windows install linux)
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set your environnement variables**
    Create a .env file with the following content:
    ```env
    dbpath=music.db
    downloadpath=/path/where/you/download
    ```
---

## 🔑 API Setup (only if you want to fetch your liked videos or a private playlist that you own)

### YouTube Data API (OAuth 2.0) 
- Create a project in the [Google Cloud Console](https://console.cloud.google.com/).
- Enable the **YouTube Data API v3**.
- Create an **OAuth Client ID** with the type "Desktop app".
- Download the `client_secret.json` file and place it in project-root/CREDS.


---

## ▶️ Usage

Run the main (main.py) script to fetch and process your playlist videos:

```bash
python main.py
```

## Behavior

### [main.py](https://github.com/Elnix90/Youtube-Downloader/blob/database/main.py)
The main script will call google to connect to your account to fetch your musics, open the link, and log in to your browser, then close the tab. You'll see thzat the downloading function is working (in theory). It will,one by one add your playlist musics to your database, while creating it if it doensét exists yet, and fill it with your data. When a nex video is downloading the database should be filled with a lot of infos from yt_dlp.
If you lose your database, the data is also written direclty in the mp3 files, in a json format, to recover in case of data loosing and to not have to redownload. If you want to modify some data, do it in the database and run the script, it will update the mp3 files and do what you wrote, (like if you wanted to delete the lyrics)
  - You can add tags to the database from your phone for exeample and the next time you run the programm, they will be added to your files





---

## 📂 Project Structure

```
├── main.py                           # Main function ([usage](#usage))
├──logger.py                          # logger initializer, to log everything that happends (you can enable or disable console logs in CONSTANTS)
├── .env                              # Your environnemnt variable file
├── CONFIG                            # List of patterns to correctly fecth lyrics, by cleaning the messy title of youtube
    ├── ALBUM                         # Private and public txt files, the keywords in public will make the processed file album 'Puclic' if his title or author name contains one or more keys, same for 'Private' but it is the default choice, and a public cannot be also private so, if a private is detected, it is private, even if it was counted as public
    ├── PATERNS                       # List of patterns useful for tags, albums and lyrics fetching
    ├── TAGS                          # Every file that you put here in the format 'tag_tagname.txt' or 'notag_tagname.txt' and containing multiple lines uncommented will be processed to apply tags to a file. This is the same logic as Albums but a file can contain multiple tags
├── CREDS                             # client-secret and token for google authentication
├── TAGS                              # Same as 2 before but not yet implemented
├── FUNCTIONS/                        # Core features: download, playlist ops, file handling
    ├── PROCESS                       # The heart of the code, contains all the differents functions that are called in process_all.py, or main if you prefer to compute the code, downlaod and apply the tags, etc...
├── CONSTANTS.py                      # Paths constants
├── requirements.txt                  # Python dependencies
├── README.md                         # This file
└── JSON                              # Where the big lists will downloaded (may be removed in the future)
```

---

## ⚠️ Notes & Limitations
- You must be signed in with a Google account that has access to the playlist you want to process (if unavailable by yt_dlp)
- Private videos will be skipped unless you provide cookies for authentication.
- Lyrics fetching relies syncedlyrics and youtube's subtitles not all songs will have lyrics or **correct lyrics**
- Tags automaticly searching is only dependent of your customisation, same for ablum
- `yt-dlp` format support depends on YouTube’s availability.

---

## 🚀 Planned Improvements
- Interactive CLI or GUI for easier use -> maybe in 2 years lol
- Config file for persistent settings.
- Batch processing with progress bars. -> Already a part of it is done, with global ETA and download progress
- easier customisation of tags and lyrics

---

## 📝 License
This project is open-source under the MIT License.
