# 🎵 YouTube Music Fetcher & Playlist Manager

This project automates the process of **fetching, downloading, and managing YouTube music videos**.  
It integrates with the **YouTube Data API v3** to access your liked videos or any playlist you choose, and uses `yt-dlp` to downloads.  
It also retrieves artist names, track titles, youtube thumbnails and some other metadata.
You can also automatically add lyrics or tags by fetching the title and uploader name of the songs or video (fully customizable), and remove segments via sponsorblock

---

## ✨ Features

- **Fetch & Download**
  - Download videos or audio from any playlist (default liked_videos).
  - Supports only `mp3` due to tags, lyrics and metadatas usage but may extend to other formats in the future
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
  - All settings centralized in `config.toml`
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

4. **Configure the application**

   ```bash
   # Copy the example configuration
   cp config.toml.example config.toml
   
   # Edit config.toml and modify at least:
   # - paths.download_path = "/your/music/folder"
   # - paths.db_path = "music.db" (or your preferred location)
   ```

---

## 🔑 Configuration

### Configuration File (config.toml)

The application uses a structured TOML configuration file. Here's what you need to configure:

**Essential settings:**

```toml
[paths]
download_path = "/your/music/folder"  # REQUIRED: Where to save downloaded music
db_path = "music.db"                  # SQLite database file

[processing]
playlist_id = "LL"                    # "LL" = liked videos, or specific playlist ID
get_lyrics = true                     # Download lyrics automatically
add_tags = true                       # Apply automatic tagging
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

### 🚀 Quick Start Guide

**New to this project?** Check out our comprehensive **[Quick Start Guide](QUICK_START.md)** with step-by-step examples and common configurations!

### Basic Usage

1. **Configure the application**:

   ```bash
   # Copy example config and edit it
   cp config.toml.example config.toml
   nano config.toml  # or your preferred editor
   ```

2. **Set your music folder** in `config.toml`:

   ```toml
   [paths]
   download_path = "/home/user/Music/YouTube"  # Change this path
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

**Test mode (no actual downloads):**

```bash
# Edit config.toml:
[processing]
test_run = true

# Then run:
python main.py
```

**Download a specific playlist:**

```bash
# Edit config.toml:
[processing]
playlist_id = "PLrAl6cYLGFcOlKGLDLpSlink_2Dwarf1V"  # Replace with your playlist ID

# Then run:
python main.py
```

**Simple download without lyrics or tags:**

```bash
# Edit config.toml:
[processing]
get_lyrics = false
add_tags = false
use_sponsorblock = false

# Then run:
python main.py
```

### Advanced Usage

You can also override configuration programmatically by modifying `main.py`:

```python
if __name__ == "__main__":
    # Use all default settings from config.toml
    main_list_process()
    
    # Or override specific parameters:
    # main_list_process(
    #     playlist_id="PLrAl6cYLGFcOlKGLDLpSlink_2Dwarf1V",
    #     test_run=True,
    #     get_lyrics=False
    # )
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

### File Organization

The application creates this folder structure:

```text
├── config.toml                    # Your configuration
├── music.db                       # SQLite database
├── /your/music/folder/            # Downloaded MP3 files
├── JSON/                          # Temporary playlist data
├── LOGS/                          # Detailed operation logs
├── CREDS/                         # YouTube API credentials (if used)
└── CONFIG/                        # Pattern files for tagging
    ├── PATTERNS/                  # Text patterns for cleaning
    └── TAGS/                      # Tag assignment rules
```

### Customization

**Tag System**: Create files in `CONFIG/TAGS/`:

- `tag_rock.txt` - Words that trigger "rock" tag
- `tag_french.txt` - Words that trigger "french" tag
- `notag_instrumental.txt` - Words that prevent tagging

**Pattern Cleaning**: Edit `CONFIG/PATTERNS/unwanted_patterns.txt` to improve lyrics matching by removing common words like "official", "lyrics", etc.

---

## 📂 Project Structure

```text
├── main.py                           # Main function
├── config.toml                       # Configuration file (TOML format)
├── config.toml.example               # Configuration template
├── config_loader.py                  # Configuration loading utilities
├── logger.py                         # Logger initializer
├── CONSTANTS.py                      # Project constants and paths
├── requirements.txt                  # Python dependencies
├── CONFIG/                           # Configuration files
│   ├── PATTERNS/                     # Text patterns for processing
│   │   ├── unwanted_patterns.txt     # Words to remove from titles
│   │   ├── remix_patterns.txt        # Remix detection patterns
│   │   ├── private_patterns.txt      # Private album patterns
│   │   └── trusted_artists.txt       # Trusted artist names
│   └── TAGS/                         # Tag assignment rules
│       ├── tag_*.txt                 # Files that add specific tags
│       └── notag_*.txt               # Files that prevent tagging
├── FUNCTIONS/                        # Core functionality modules
│   ├── get_playlist_videos.py       # YouTube playlist fetching
│   ├── download.py                   # Video downloading logic
│   ├── metadata.py                   # Metadata extraction and embedding
│   ├── lyrics.py                     # Lyrics fetching and processing
│   ├── tags_system.py                # Automatic tagging system
│   ├── sql_requests.py               # Database operations
│   └── PROCESS/                      # Processing pipeline modules
├── CREDS/                            # API credentials (not tracked)
├── JSON/                             # Temporary data files
└── LOGS/                             # Application logs
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
- Support for additional audio formats

---

## 📝 Migration from .env

If you're upgrading from a previous version that used `.env` files, see `MIGRATION.md` for detailed migration instructions.

## 📝 License

This project is open-source under the MIT License.
