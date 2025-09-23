import sqlite3
import time
from typing import Literal
import json


from CONSTANTS import DB_PATH
from FUNCTIONS.HELPERS.helpers import VideoInfo, VideoInfoKey, remove_data_from_video_info


from FUNCTIONS.HELPERS.logger import setup_logger
logger = setup_logger(__name__)






def get_db_connection(create_if_not: bool = True) -> sqlite3.Connection:
    """
    Connect to the SQLite database. If the DB file does not exist, create it.
    """
    
    if not DB_PATH.exists():
        if create_if_not:
            logger.info(f"[Get DB conn] Database file not found, creating: {DB_PATH}")
            DB_PATH.parent.mkdir(parents=True, exist_ok=True)  # ensure parent folder exists
            # This will create an empty SQLite database
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            logger.debug("[Get DB conn] New database created")
            return conn
        else:
            raise FileNotFoundError (f"{DB_PATH} does not exists, stopping execution here")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    logger.debug("[Get DB conn] Successfully connected")
    return conn




def init_db(cur: sqlite3.Cursor, conn: sqlite3.Connection):


    _ = cur.execute("""
        CREATE TABLE IF NOT EXISTS videos (
        video_id TEXT UNIQUE PRIMARY KEY,
        title TEXT,
        thumbnail_url TEXT,
        description TEXT,
        channel_id TEXT,
        channel_url TEXT,
        view_count INTEGER CHECK(view_count >= 0),
        comment_count INTEGER CHECK(comment_count >= 0),
        like_count INTEGER CHECK(like_count >= 0),
        uploader TEXT,
        channel_follower_count INTEGER CHECK (channel_follower_count >= 0),
        uploader_id TEXT,
        uploader_url TEXT,
        upload_date TEXT,
        duration INTEGER CHECK(duration >= 0),
        duration_string TEXT,

        removed_segments_int INT,
        removed_segments_duration REAL,

        lyrics TEXT,
        subtitles TEXT,
        syncedlyrics TEXT,
        syncedlyrics_query TEXT,
        auto_subs TEXT,
        try_lyrics_if_not BOOLEAN NOT NULL CHECK (try_lyrics_if_not IN (0,1)) DEFAULT (1),
        lyrics_retries INTEGER CHECK (lyrics_retries >= 0) DEFAULT (0),

        update_thumbnail BOOLEAN NOT NULL CHECK (update_thumbnail IN (0,1)) DEFAULT (0),
        remove_thumbnail BOOLEAN NOT NULL CHECK (remove_thumbnail IN (0,1)) DEFAULT (0),
        remove_lyrics BOOLEAN NOT NULL CHECK (remove_lyrics IN (0,1)) DEFAULT (0),

        recompute_tags BOOLEAN NOT NULL CHECK (recompute_tags IN (0,1)) DEFAULT (1),
        recompute_album BOOLEAN NOT NULL CHECK (recompute_album IN (0,1)) DEFAULT (1),
        recompute_yt_info BOOLEAN NOT NULL CHECK (recompute_yt_info IN (0,1)) DEFAULT (0),

        remix_of TEXT,
        filename TEXT,
        status INTEGER NOT NULL CHECK (status in (0,1,2,3)) DEFAULT (3),
        reason TEXT,

        date_added REAL DEFAULT ((julianday('now') - 2440587.5) * 86400.0),
        date_modified REAL DEFAULT ((julianday('now') - 2440587.5) * 86400.0)
    )
    """)
    logger.debug("[Init DB] Initialized videos")





    _ = cur.execute("""
    CREATE TABLE IF NOT EXISTS removed_segments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        video_id TEXT NOT NULL,
        segment_start REAL NOT NULL,
        segment_end REAL NOT NULL,
        FOREIGN KEY(video_id) REFERENCES videos(video_id) ON DELETE CASCADE
    )
    """)
    logger.debug("[Init DB] Initialized removed_segments")




    _ = cur.execute("""
    CREATE TABLE IF NOT EXISTS tags (
        tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
        tag TEXT UNIQUE NOT NULL
    )
    """)
    logger.debug("[Init DB] Initialized tags")




    _ = cur.execute("""
    CREATE TABLE IF NOT EXISTS video_tags (
        video_id TEXT NOT NULL,
        tag_id INTEGER NOT NULL,
        PRIMARY KEY (video_id, tag_id),
        FOREIGN KEY(video_id) REFERENCES videos(video_id) ON DELETE CASCADE,
        FOREIGN KEY(tag_id) REFERENCES tags(tag_id) ON DELETE CASCADE
    )
    """)
    logger.debug("[Init DB] Initialized video_tags")

    conn.commit()









def _apply_skips_and_tags(video_id: str, data: VideoInfo, cur: sqlite3.Cursor) -> None:
    # --- Skips ---
    if "skips" in data:
        _ = cur.execute("DELETE FROM removed_segments WHERE video_id = ?", (video_id,))
        for start, end in data["skips"]:
            _ = cur.execute(
                "INSERT INTO removed_segments (video_id, segment_start, segment_end) VALUES (?, ?, ?)",
                (video_id, start, end)
            )
        logger.debug(f"[DB] Applied {len(data['skips'])} removed_segments for '{video_id}'")

    # --- Tags ---
    if "tags" in data:
        _ = cur.execute("DELETE FROM video_tags WHERE video_id = ?", (video_id,))
        for tag in data["tags"]:
            _ = cur.execute("INSERT OR IGNORE INTO tags (tag) VALUES (?)", (tag,))
            _ = cur.execute("SELECT tag_id FROM tags WHERE tag = ?", (tag,))
            tag_id = cur.fetchone()[0]  # pyright: ignore[reportAny]
            _ = cur.execute("INSERT OR IGNORE INTO video_tags (video_id, tag_id) VALUES (?, ?)", (video_id, tag_id))
        logger.debug(f"[DB] Applied {len(data['tags'])} tags for '{video_id}'")






def insert_video_db(video_data: VideoInfo, cur: sqlite3.Cursor, conn: sqlite3.Connection) -> None:
    _ = cur.execute("PRAGMA table_info(videos)")
    video_columns = {row["name"] for row in cur.fetchall()}  # pyright: ignore[reportAny]

    # Extract valid fields
    video_row = {k: v for k, v in video_data.items() if k in video_columns and k not in {"skips", "tags"}}
    if "video_id" not in video_row:
        logger.error("[Insert Video] Missing 'video_id'")
        return

    placeholders = ", ".join("?" for _ in video_row)
    columns = ", ".join(video_row.keys())
    sql = f"INSERT OR IGNORE INTO videos ({columns}) VALUES ({placeholders})"
    _ = cur.execute(sql, tuple(video_row.values()))

    _apply_skips_and_tags(video_id=video_row["video_id"], data=video_data, cur=cur)  # pyright: ignore[reportArgumentType]
    conn.commit()
    logger.info(f"[Insert Video] Inserted '{video_row['video_id']}' with {len(video_row)} fields")







def update_video_db(video_id: str, update_fields: VideoInfo, cur: sqlite3.Cursor, conn: sqlite3.Connection) -> None:
    _ = cur.execute("PRAGMA table_info(videos)")
    video_columns = {row["name"] for row in cur.fetchall()}  # pyright: ignore[reportAny]

    # Secutity to avoid rewriting date added
    update_fields = remove_data_from_video_info(update_fields,["date_added","date_updated"])

    # Update only valid DB fields
    EXCLUDE_FOR_MAIN = {"skips", "tags"}
    video_update_data = {k: v for k, v in update_fields.items() if k in video_columns and k not in EXCLUDE_FOR_MAIN}
    
    video_update_data["date_modified"] = time.time()

    if video_update_data:
        set_clause = ", ".join(f"{k} = ?" for k in video_update_data.keys())
        values = list(video_update_data.values()) + [video_id]
        sql = f"UPDATE videos SET {set_clause} WHERE video_id = ?"
        _ = cur.execute(sql, values)

    _apply_skips_and_tags(video_id=video_id, data=update_fields, cur=cur)
    conn.commit()
    logger.debug(f"[Update Video] Updated '{video_id}' with {len(video_update_data)} fields")







def remove_video(video_id: str, cur: sqlite3.Cursor, conn: sqlite3.Connection) -> None:
    """
    Remove a video and all its related data from the database.
    Cascades take care of related rows in removed_segments and video_tags.
    """
    _ = cur.execute("DELETE FROM videos WHERE video_id = ?", (video_id,))
    if cur.rowcount > 0:
        logger.info(f"[Remove Video] Successfully removed video_id '{video_id}' and related data")
    else:
        logger.warning(f"[Remove Video] No video found with video_id '{video_id}'")
    conn.commit()








def get_videos_in_list(include_not_status0: bool,cur: sqlite3.Cursor) -> list[str]:
    if include_not_status0:
        _ = cur.execute("SELECT video_id FROM videos ORDER BY date_added DESC")
    else:
        _ = cur.execute("SELECT video_id FROM videos WHERE status IN (0,3) ORDER BY date_added ASC")
    rows = cur.fetchall()
    return [row["video_id"] for row in rows]  # pyright: ignore[reportAny]






# -----------------------------
# Safe helper functions
# -----------------------------
def safe_str(row: sqlite3.Row, key: VideoInfoKey) -> str:
    value = row[key] if key in row.keys() else None
    return value if isinstance(value, str) else ""


def safe_int(row: sqlite3.Row, key: VideoInfoKey) -> int:
    value = row[key] if key in row.keys() else None
    return value if isinstance(value, int) else 0

def safe_status(row: sqlite3.Row, key: VideoInfoKey) -> Literal[0, 1, 2, 3]:
    value = row[key] if key in row.keys() else None
    if isinstance(value, int) and value in (0, 1, 2, 3):
        return value
    return 3 # Unknown

def safe_lyrics_to_use(row: sqlite3.Row, key: VideoInfoKey) -> Literal[0, 1, 2]:
    value = row[key] if key in row.keys() else None
    if isinstance(value, int) and value in (0, 1, 2):
        return value
    return 0

def safe_float(row: sqlite3.Row, key: VideoInfoKey) -> float:
    value = row[key] if key in row.keys() else None
    return float(value) if isinstance(value, (int, float)) else 0.0


def safe_bool(row: sqlite3.Row, key: VideoInfoKey) -> bool:
    value = row[key] if key in row.keys() else None
    return bool(value) if isinstance(value, int) else False



def safe_str_list(row: sqlite3.Row, key: VideoInfoKey) -> list[str]:
    value = row[key] if key in row.keys() else None
    if isinstance(value, str):
        try:
            parsed = json.loads(value)  # pyright: ignore[reportAny]
            if isinstance(parsed, list) and all(isinstance(x, str) for x in parsed):  # pyright: ignore[reportUnknownVariableType]
                return parsed  # pyright: ignore[reportUnknownVariableType]
        except Exception:
            return []
    return []


# -----------------------------
# Row -> VideoInfo converter
# -----------------------------
def row_to_video_info(row: sqlite3.Row) -> VideoInfo:
    """
    Convert a sqlite3.Row from the `videos` table into a VideoInfo dict.
    """

    return {
        "video_id": safe_str(row, "video_id"),
        "title": safe_str(row, "title"),
        "thumbnail_url": safe_str(row, "thumbnail_url"),
        "description": safe_str(row, "description"),
        "channel_id": safe_str(row, "channel_id"),
        "channel_url": safe_str(row, "channel_url"),
        "view_count": safe_int(row, "view_count"),
        "comment_count": safe_int(row, "comment_count"),
        "like_count": safe_int(row, "like_count"),
        "uploader": safe_str(row, "uploader"),
        "channel_follower_count": safe_int(row, "channel_follower_count"),
        "uploader_id": safe_str(row, "uploader_id"),
        "uploader_url": safe_str(row, "uploader_url"),
        "upload_date": safe_str(row, "upload_date"),
        "duration": safe_int(row, "duration"),
        "duration_string": safe_str(row, "duration_string"),

        "removed_segments_int": safe_int(row,"removed_segments_int"),
        "removed_segments_duration": safe_float(row,"removed_segments_duration"),

        "lyrics": safe_str(row, "lyrics"),
        "subtitles": safe_str(row, "subtitles"),
        "syncedlyrics": safe_str(row, "syncedlyrics"),
        "auto_subs": safe_str(row, "auto_subs"),
        "try_lyrics_if_not": safe_bool(row, "try_lyrics_if_not"),

        "update_thumbnail": safe_bool(row, "update_thumbnail"),
        "remove_thumbnail": safe_bool(row, "remove_thumbnail"),

        "remove_lyrics": safe_bool(row, "remove_lyrics"),
        "lyrics_retries": safe_int(row,"lyrics_retries"),

        "tags": safe_str_list(row, "tags"),

        "recompute_tags": safe_bool(row, "recompute_tags"),
        "recompute_album": safe_bool(row, "recompute_album"),
        "recompute_yt_info": safe_bool(row, "recompute_yt_info"),

        "remix_of": safe_str(row, "remix_of"),

        "filename": safe_str(row, "filename"),
        "status": safe_status(row, "status"),
        "reason": safe_str(row, "reason"),

        "date_added": safe_float(row, "date_added"),
        "date_modified": safe_float(row, "date_modified"),
    }







def get_video_info_from_db(video_id: str, cur: sqlite3.Cursor) -> VideoInfo:
    """
    Fetch a video's metadata (including tags and removed_segments)
    from the database and return it as a VideoInfo dict.
    Only non-null fields are included in the result.
    """
    # --- Fetch main video row ---
    _ = cur.execute("SELECT * FROM videos WHERE video_id = ?", (video_id,))
    row: sqlite3.Row = cur.fetchone()  # pyright: ignore[reportAny]
    if not row:
        logger.verbose(f"[Get Video Info] No entry found for video_id '{video_id}'")
        return {}

    # Only add keys with non-null values
    video_info: VideoInfo = row_to_video_info(row=row)


    # --- Fetch tags ---
    _ = cur.execute("""
        SELECT t.tag
        FROM tags t
        JOIN video_tags vt ON t.tag_id = vt.tag_id
        WHERE vt.video_id = ?
    """, (video_id,))
    tags = [tag_row["tag"] for tag_row in cur.fetchall()]  # pyright: ignore[reportAny]
    if tags:
        video_info["tags"] = tags

    # --- Fetch removed segments ---
    _ = cur.execute("""
        SELECT segment_start, segment_end
        FROM removed_segments
        WHERE video_id = ?
        ORDER BY segment_start
    """, (video_id,))
    skips: list[tuple[float, float]] = [(seg_row["segment_start"], seg_row["segment_end"]) for seg_row in cur.fetchall()]  # pyright: ignore[reportAny]
    if skips:
        video_info["skips"] = skips

    logger.verbose(f"[Get Video Info] Retrieved info for video_id '{video_id}'")

    video_info_copy = video_info.copy()


    for key, value in video_info_copy.items():
        if value is None or (isinstance(value, str) and value == ""):
            del video_info[key]


    return video_info





