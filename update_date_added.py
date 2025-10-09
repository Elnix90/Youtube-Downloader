"""
Set the date added of every file in the db in the same
order as in the list got from yt, to sort them by last
added or whatever order there are in the playlist.
"""

from CONSTANTS import PLAYLIST_VIDEOS_FILE
from DEBUG.update_date_added import update_date_added
from FUNCTIONS.sql_requests import get_db_connection

if __name__ == "__main__":
    with get_db_connection() as conn:
        cur = conn.cursor()
        update_date_added(PLAYLIST_VIDEOS_FILE, cur, conn)
