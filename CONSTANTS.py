from pathlib import Path

JSON_DIR = Path("JSON")
CRED_DIR = Path("CREDS")

CLIENT_SECRETS_FILE = CRED_DIR / "client_secret_cm.json"
TOKEN_FILE = CRED_DIR / "token.json"

LIKED_VIDEOS_FILE = JSON_DIR / "liked_videos.json"
PLAYLIST_VIDEOS_FILE = JSON_DIR / "playlist_videos.json"
PLAYLIST_VIDEOS_INFOS_FILE = JSON_DIR / "playlist_videos_infos.json"
VIDEOS_TO_LIKE_FILE = JSON_DIR / "videos_to_like.json"
VIDEOS_TO_ADD_IN_PLAYLIST_FILE = JSON_DIR / "videos_to_add_in_playlist.json"
VIDEOS_TO_DOWNLOAD_FILE = JSON_DIR / "videos_to_download.json"
VIDEOS_INFOS_FILE = JSON_DIR / "video_infos.json"
ERROR_DOWNLOADED_FILE = JSON_DIR / "error_downloaded.json"
ERROR_LIKED_FILE = JSON_DIR / "error_liked.json"
ERROR_ADDED_FILE = JSON_DIR / "error_added.json"
UNAVAILABLE_VIDEOS_FILE = JSON_DIR / "unavailable_videos.json"