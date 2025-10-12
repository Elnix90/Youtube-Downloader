# 🎵 YouTube Music Fetcher & Playlist Manager

This project automates the process of **fetching, downloading, and managing YouTube music videos**.  
It integrates with the **YouTube Data API v3** to access your liked videos or any playlist you choose, and uses `yt-dlp` to downloads.  
It also retrieves artist names, track titles, youtube thumbnails and some other metadata.
You can also automatically add lyrics or tags by fetching the title and uploader name of the songs or video (fully customizable), and remove segments via sponsorblock

---

## ✨ Features

- **Fetch & Download**
  - Download videos or audio from any playlist (default liked_videos).
  - Supports only `mp3` due to tags, lyrics and metadatas usage ~~but may extend to other formats in the future~~
  - Skips videos that are private or unavailable.

- **Metadata & Lyrics**
  - Can automatically extract artist, title, and uploader information.
  - Fetch lyrics with [syncedlyrics](https://github.com/moehmeni/syncedlyrics) (no token or api required), or the youtube subtitles if there are some, in this order: manual subtitles > syncedlyrics > auto subtitles
  - Can automatically add tags to your file, depending on what's inside the filename and uploader name, customize that here
  - can automatically remove segments marked from sponsorblock

- **Error Handling**
  - Detects and skips private videos.
  - Keeps track of failed downloads in separate log files.

- **Configuration System**
  - Uses structured TOML configuration file for easy customization
  - All settings centralized in `CONFIG/config.toml`
  - Flexible parameter override system

---

## 📦 Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/Elnix90/Youtube-Downloader.git
   cd Youtube-Downloader
   ```

2. **Create and activate a virtual environment** (recommended)

   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or on Windows:
   # venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```



## 🔑 Configuration

### Configuration File (CONFIG/config.toml)

The application uses a structured TOML configuration file. Here's what you need to configure:

**Essential settings:**

```toml
[paths]
download_path = "/your/music/folder"  # Where to save downloaded music
db_path = "music.db"                  # SQLite database file

[processing]
playlist_id = "LL"                    # "LL" = liked videos, or specific playlist ID
get_lyrics = true                     # Download lyrics automatically
add_tags = true                       # Apply automatic tagging (based on your settings)
test_run = false                      # Set to true for testing without downloading
```

**Available processing options:**

- `embed_metadata` - Add metadata to MP3 files
- `get_lyrics` - Fetch lyrics from syncedlyrics or YouTube subtitles
- `get_thumbnail` - Add thumbnails to MP3 files
- `use_sponsorblock` - Remove sponsored segments
- `add_tags` - Apply automatic tags based on title/artist patterns
- `add_album` - Organize tracks into Public/Private albums

### YouTube Data API (Optional)

For accessing private playlists or liked videos:

- Create a project in the [Google Cloud Console](https://console.cloud.google.com/)
- Enable the **YouTube Data API v3**
- Create an **OAuth Client ID** with the type "Desktop app"
- Download the `client_secret.json` file and place it in `CREDS/`

---

## ▶️ Usage


### Basic Usage

1. **Configure the application**:

   ```bash
   # Edit CONFIG/config.toml
   vim CONFIG/config.toml
   ```

2. **Set your music folder** in `CONFIG/config.toml`:

   ```toml
   [paths]
   download_path = "~/YOUTUBE/MUSICS"  # Change this path
   ```

3. **Run the application**:

   ```bash
   python main.py
   ```

### Usage Examples

**Download your liked videos with default settings:**

```bash
python main.py
```

**Test mode (no actual downloads or any file editing):**

```bash
# Edit config.toml:
[processing]
test_run = true
```

**Download a specific playlist:**

```bash
# Edit config.toml:
[processing]
playlist_id = "PLnVyge3em-a2ElGZrft3LHoh64YnGhPsh"  # Replace with your playlist ID
```

**Simple download without lyrics or tags:**

```bash
# Edit config.toml:
[processing]
get_lyrics = false
add_tags = false
use_sponsorblock = false
```

---

## 🎯 How It Works

### Workflow

1. **Authentication**: If using private playlists, the app opens your browser for YouTube OAuth
2. **Playlist Fetching**: Retrieves video information from your chosen playlist
3. **Database Management**: Stores video metadata in a SQLite database
4. **Download Process**: Downloads new videos as MP3 files using yt-dlp
5. **Enrichment**: Adds lyrics, tags, thumbnails, and metadata to each file
6. **SponsorBlock**: Removes sponsored segments if enabled


### Customization

**Tag System**: Create files in `CONFIG/TAGS/`:

- `tag_rock.txt` - Words that trigger "rock" tag
- `tag_french.txt` - Words that trigger "french" tag
- `notag_instrumental.txt` - Words that prevent tagging if word in list of words, else it gives the tag

**Pattern Cleaning**: Edit `CONFIG/PATTERNS/unwanted_patterns.txt` to improve lyrics matching by removing common words like "official", "lyrics", etc.

---

## 📂 Project Structure

```text
├── CREDS                             # Google creditentials tokens
├── .gitignore                        # Git ignore file for excluding files/folders from version control
├── CONFIG                            # Configuration directory
│   ├── PATTERNS                      # Pattern files for processing music metadata
│   ├── TAGS                          # Tagging rules directory
│   └── config_loader.py              # Loads and validates the configuration from config.toml
├── CONSTANTS.py                      # Defines constants and paths used across the project
├── DEBUG                             # Scripts for testing and/or debugging
├── FUNCTIONS                         # Core functionality of the project
│   ├── HELPERS                       # Utility/helper functions used across modules
│   └──PROCESS                        # Processing modules for different music operations
├── README.md                         # Project overview and instructions
├── main.py                           # Main entry point for the program
└── requirements.txt                  # Python dependencies
```

---

## ⚠️ Notes & Limitations

- You must be signed in with a Google account that has access to the playlist you want to process (if unavailable by yt_dlp)
- Private videos will be skipped unless you provide cookies for authentication.
- Lyrics fetching relies syncedlyrics and youtube's subtitles not all songs will have lyrics or **correct lyrics**
- Tags automatically searching is only dependent of your customisation, same for ablum
- `yt-dlp` format support depends on YouTube's availability.

---

## 🚀 Planned Improvements

- Interactive CLI or GUI for easier use
- Enhanced configuration validation and error handling
- Batch processing with progress bars (partially implemented)
- Easier customisation of tags and lyrics

---

## 📝 License

This project is open-source under the MIT License.
