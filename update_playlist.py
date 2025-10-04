from CONSTANTS import CONFIG
from DEBUG.add_videos_to_playlist import add_videos

playlist_id = CONFIG['other']['music_playlist_id']


if __name__ == "__main__" and playlist_id is not None:
    add_videos(
        playlist_id,
        CONFIG['other']["clean"],
        CONFIG['processing']["test_run"],
        CONFIG['processing']["info"],
        CONFIG['processing']["error"],
    )
