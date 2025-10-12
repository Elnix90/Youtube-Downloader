"""
SQL requests module
contains function to interract esaely with the database
"""

import json
import sqlite3
from typing import Literal, cast

from constants import DB_PATH, EXCLUDE_FROM_MAIN
from FUNCTIONS.HELPERS.helpers import VideoInfo, VideoInfoKey, now_unix
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
            raise FileNotFoundError(f"{DB_PATH} does not exists, stopping execution here")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    logger.debug("[Get DB conn] Successfully connected")
    return conn


def commit_changes_to_db(conn: sqlite3.Connection, stop_on_sql_error: bool, test_run: bool = False) -> bool:
    """
    Takes the Connection object to commit a change safely, and take in count test run to avoid breaking when debugging
    """
    try:
        if not test_run:
            conn.commit()
            logger.verbose("[Commiting changes] Changes commited")
        else:
            logger.verbose("[Commiting changes] Test run was enabled, no changes commited")
        return True
    except sqlite3.OperationalError as e:
        if not stop_on_sql_error:
            logger.error(f"[Commiting changes] Error while commiting in the db: {e}")
            return False
        raise sqlite3.OperationalError(e)


def init_db(cur: sqlite3.Cursor, conn: sqlite3.Connection) -> None:
    """
    Initialize the SQLite database with all required tables and constraints.
    Includes videos, playlists, many-to-many relationships, and tag support.
    """

    # ============================================================
    #                       VIDEOS TABLE
    # ============================================================
    _ = cur.execute(
        """
        CREATE TABLE IF NOT EXISTS videos (
            -- Core identifiers
            video_id TEXT PRIMARY KEY,
            title TEXT,
            description TEXT,
            thumbnail_url TEXT,

            -- Channel / uploader info
            channel_id TEXT,
            channel_url TEXT,
            uploader TEXT,
            uploader_id TEXT,
            uploader_url TEXT,
            channel_follower_count INTEGER CHECK(channel_follower_count >= 0),

            -- YouTube statistics
            view_count INTEGER CHECK(view_count >= 0),
            comment_count INTEGER CHECK(comment_count >= 0),
            like_count INTEGER CHECK(like_count >= 0),

            -- Publication details
            upload_date TEXT,
            duration INTEGER CHECK(duration >= 0),
            duration_string TEXT,
            privacy_status TEXT,

            -- SponsorBlock / skip summary
            removed_segments_int INTEGER DEFAULT 0,
            removed_segments_duration REAL DEFAULT 0.0,

            -- Lyrics / subtitle information
            lyrics TEXT,
            subtitles TEXT,
            syncedlyrics TEXT,
            syncedlyrics_query TEXT,
            auto_subs TEXT,
            try_lyrics_if_not BOOLEAN NOT NULL CHECK (try_lyrics_if_not IN (0,1)) DEFAULT 1,
            lyrics_retries INTEGER CHECK (lyrics_retries >= 0) DEFAULT 0,

            -- Maintenance / recomputation flags
            update_thumbnail BOOLEAN NOT NULL CHECK (update_thumbnail IN (0,1)) DEFAULT 0,
            remove_thumbnail BOOLEAN NOT NULL CHECK (remove_thumbnail IN (0,1)) DEFAULT 0,
            remove_lyrics BOOLEAN NOT NULL CHECK (remove_lyrics IN (0,1)) DEFAULT 0,
            recompute_tags BOOLEAN NOT NULL CHECK (recompute_tags IN (0,1)) DEFAULT 1,
            recompute_album BOOLEAN NOT NULL CHECK (recompute_album IN (0,1)) DEFAULT 1,
            recompute_yt_info BOOLEAN NOT NULL CHECK (recompute_yt_info IN (0,1)) DEFAULT 0,

            -- Remix tracking
            remix_of TEXT,
            recompute_remix_of BOOLEAN NOT NULL CHECK (recompute_remix_of IN (0,1)) DEFAULT 1,
            confidence REAL CHECK (confidence >= 0 AND confidence <= 1),

            -- Local file info
            filename TEXT,
            status INTEGER NOT NULL CHECK (status IN (0,1,2,3)) DEFAULT 3,
            reason TEXT,

            -- Timestamps
            date_added REAL DEFAULT ((julianday('now') - 2440587.5) * 86400.0),
            date_modified REAL DEFAULT ((julianday('now') - 2440587.5) * 86400.0)
        );
        """
    )
    logger.debug("[Init DB] Initialized 'videos' table")

    # ============================================================
    #                       IDS TABLE
    # ============================================================
    _ = cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ids (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT UNIQUE NOT NULL
        );
        """
    )
    logger.debug("[Init DB] Initialized 'ids' table")

    # ============================================================
    #                       PLAYLISTS TABLE
    # ============================================================
    _ = cur.execute(
        """
        CREATE TABLE IF NOT EXISTS playlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            playlist_id TEXT UNIQUE NOT NULL,
            title TEXT,
            description TEXT,
            channel_id TEXT,
            date_added REAL DEFAULT ((julianday('now') - 2440587.5) * 86400.0)
        );
        """
    )
    logger.debug("[Init DB] Initialized 'playlists' table")

    # ============================================================
    #               PLAYLISTS - VIDEOS (RELATION)
    # ============================================================
    _ = cur.execute(
        """
        CREATE TABLE IF NOT EXISTS playlist_videos (
            playlist_id TEXT NOT NULL,
            video_id TEXT NOT NULL,
            playlist_item_id TEXT,
            position INTEGER CHECK(position >= 0),

            PRIMARY KEY (playlist_id, video_id),

            FOREIGN KEY(playlist_id) REFERENCES playlists(playlist_id)
                ON DELETE CASCADE,

            FOREIGN KEY(video_id) REFERENCES videos(video_id)
                ON DELETE CASCADE
        );
        """
    )
    logger.debug("[Init DB] Initialized 'playlist_videos' table")

    # ============================================================
    #                       REMOVED SEGMENTS
    # ============================================================
    _ = cur.execute(
        """
        CREATE TABLE IF NOT EXISTS removed_segments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT NOT NULL,
            segment_start REAL NOT NULL CHECK (segment_start >= 0),
            segment_end REAL NOT NULL CHECK (segment_end > segment_start),
            FOREIGN KEY(video_id) REFERENCES videos(video_id)
                ON DELETE CASCADE
        );
        """
    )
    logger.debug("[Init DB] Initialized 'removed_segments' table")

    # ============================================================
    #                           TAGS
    # ============================================================
    _ = cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tags (
            tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
            tag TEXT UNIQUE NOT NULL
        );
        """
    )
    logger.debug("[Init DB] Initialized 'tags' table")

    # ============================================================
    #                       VIDEO ↔ TAGS (RELATION)
    # ============================================================
    _ = cur.execute(
        """
        CREATE TABLE IF NOT EXISTS video_tags (
            video_id TEXT NOT NULL,
            tag_id INTEGER NOT NULL,
            PRIMARY KEY (video_id, tag_id),

            FOREIGN KEY(video_id) REFERENCES videos(video_id)
                ON DELETE CASCADE,

            FOREIGN KEY(tag_id) REFERENCES tags(tag_id)
                ON DELETE CASCADE
        );
        """
    )
    logger.debug("[Init DB] Initialized 'video_tags' table")

    # ============================================================
    #                           INDEXES
    # ============================================================
    _ = cur.execute("CREATE INDEX IF NOT EXISTS idx_video_status ON videos(status);")
    _ = cur.execute("CREATE INDEX IF NOT EXISTS idx_video_uploader ON videos(uploader_id);")
    _ = cur.execute("CREATE INDEX IF NOT EXISTS idx_playlist_channel ON playlists(channel_id);")
    _ = cur.execute("CREATE INDEX IF NOT EXISTS idx_playlist_video_item ON playlist_videos(playlist_item_id);")

    # ============================================================
    #                           COMMIT
    # ============================================================
    _ = commit_changes_to_db(conn, True)
    logger.info("[Init DB] Database fully initialized successfully")


def _apply_skips_and_tags(video_id: str, data: VideoInfo, cur: sqlite3.Cursor) -> None:
    # --- Skips ---
    if "skips" in data:
        _ = cur.execute("DELETE FROM removed_segments WHERE video_id = ?", (video_id,))
        for start, end in data["skips"]:
            _ = cur.execute(
                "INSERT INTO removed_segments (video_id, segment_start, segment_end) VALUES (?, ?, ?)",
                (video_id, start, end),
            )
        logger.debug(f"[DB] Applied {len(data['skips'])} removed_segments for '{video_id}'")

    # --- Tags ---
    if "tags" in data:
        _ = cur.execute("DELETE FROM video_tags WHERE video_id = ?", (video_id,))
        for tag in data["tags"]:
            _ = cur.execute("INSERT OR IGNORE INTO tags (tag) VALUES (?)", (tag,))
            _ = cur.execute("SELECT tag_id FROM tags WHERE tag = ?", (tag,))
            tag_id = cur.fetchone()[0]  # pyright: ignore[reportAny]
            _ = cur.execute(
                "INSERT OR IGNORE INTO video_tags (video_id, tag_id) VALUES (?, ?)",
                (video_id, tag_id),
            )
        logger.debug(f"[DB] Applied {len(data['tags'])} tags for '{video_id}'")


def _apply_playlists(video_id: str, data: VideoInfo, cur: sqlite3.Cursor) -> None:
    """
    Insert or update playlist and playlist_videos relations for a given video.
    """
    playlist_id = data.get("playlist_id")
    playlist_item_id = data.get("playlist_item_id")
    position = data.get("position")

    # Nothing to do if no playlist info
    if not playlist_id:
        return

    # --- Ensure playlist exists ---
    _ = cur.execute(
        """
        INSERT OR IGNORE INTO playlists (playlist_id)
        VALUES (?)
        """,
        (playlist_id,),
    )

    # --- Link video to playlist ---
    _ = cur.execute(
        """
        INSERT INTO playlist_videos (playlist_id, video_id, playlist_item_id, position)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(playlist_id, video_id) DO UPDATE SET
            playlist_item_id = excluded.playlist_item_id,
            position = excluded.position
        """,
        (playlist_id, video_id, playlist_item_id, position),
    )

    logger.debug(f"[DB] Linked video '{video_id}' to playlist '{playlist_id}'")


def insert_video_db(
    video_data: VideoInfo,
    cur: sqlite3.Cursor,
    conn: sqlite3.Connection,
    test_run: bool,
) -> None:
    """Insert a new entry in the DB"""

    video_id = video_data.get("video_id")

    _ = cur.execute("PRAGMA table_info(videos)")
    video_columns = {row["name"] for row in cur.fetchall()}  # pyright: ignore[reportAny]

    # Extract valid video fields
    exclude_from_main = {"skips", "tags", "playlist_id", "playlist_item_id", "position"}
    video_row = {k: v for k, v in video_data.items() if k in video_columns and k not in exclude_from_main}

    if "video_id" not in video_row:
        logger.error("[Insert Video] Missing 'video_id'")
        return

    placeholders = ", ".join("?" for _ in video_row)
    columns = ", ".join(video_row.keys())
    sql = f"INSERT OR IGNORE INTO videos ({columns}) VALUES ({placeholders})"
    _ = cur.execute(sql, tuple(video_row.values()))

    # --- Ids ---
    _ = cur.execute(f"INSERT OR IGNORE INTO ids ({video_id})")

    # --- Skips & Tags ---
    _apply_skips_and_tags(video_row["video_id"], video_data, cur)  # pyright: ignore[reportArgumentType]

    # --- Playlists ---
    _apply_playlists(video_row["video_id"], video_data, cur)  # pyright: ignore[reportArgumentType]

    if not test_run:
        _ = commit_changes_to_db(conn, True)
        logger.info(f"[Insert Video] Inserted '{video_row['video_id']}' with {len(video_row)} fields")
    else:
        logger.info("[Insert Video] Test_run enabled, no insert committed.")


def update_video_db(
    video_id: str,
    update_fields: VideoInfo,
    cur: sqlite3.Cursor,
    conn: sqlite3.Connection,
    test_run: bool,
) -> None:
    """
    Updates an entry in the DB
    """

    _ = cur.execute("PRAGMA table_info(videos)")
    video_columns = {row["name"] for row in cur.fetchall()}  # pyright: ignore[reportAny]

    # Security: prevent rewriting creation timestamps
    video_update_data = {k: v for k, v in update_fields.items() if k in video_columns and k not in EXCLUDE_FROM_MAIN}

    # Update modification time
    video_update_data["date_modified"] = now_unix()

    # --- Update main video record ---
    if video_update_data:
        set_clause = ", ".join(f"{k} = ?" for k in video_update_data.keys())
        values = list(video_update_data.values()) + [video_id]
        sql = f"UPDATE videos SET {set_clause} WHERE video_id = ?"
        _ = cur.execute(sql, values)

    # --- Apply dependent data ---
    _apply_skips_and_tags(video_id, update_fields, cur)
    _apply_playlists(video_id, update_fields, cur)

    _ = commit_changes_to_db(conn, True, test_run)


def remove_video(
    video_id: str,
    cur: sqlite3.Cursor,
    conn: sqlite3.Connection,
    test_run: bool,
) -> None:
    """
    Remove a video and all related data (tags, skips, playlists) from the database.
    CASCADE will clean related rows automatically.
    """
    _ = cur.execute("DELETE FROM videos WHERE video_id = ?", (video_id,))
    _ = cur.execute("DELETE FROM playlist_videos WHERE video_id = ?", (video_id,))  # safety

    if cur.rowcount > 0:
        logger.info(f"[Remove Video] Successfully removed '{video_id}' and related data")
    else:
        logger.warning(f"[Remove Video] No video found with id '{video_id}'")

    if not test_run:
        _ = commit_changes_to_db(conn, True, test_run)
        logger.debug(f"[Remove Video] Removed '{video_id}' from database")
    else:
        logger.info("[Remove Video] Test_run enabled, no removal committed.")


def get_videos_in_db(include_not_status0: bool, cur: sqlite3.Cursor) -> list[str]:
    """
    Fetch the DB and return a list of ids in the ascendind order (older before),
    at least this is what i want the real result is messy thanks to my skill issue
    """
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
    """Return a srt from a Row object, type safe"""
    value = row[key] if key in row.keys() else None
    return value if isinstance(value, str) else ""


def safe_int(row: sqlite3.Row, key: VideoInfoKey) -> int:
    """Return a int from a Row object, type safe"""
    value = row[key] if key in row.keys() else None
    return value if isinstance(value, int) else 0


def safe_status(row: sqlite3.Row, key: VideoInfoKey) -> Literal[0, 1, 2, 3]:
    """Return a status literal from a Row object, type safe"""
    value = row[key] if key in row.keys() else None
    if isinstance(value, int) and value in (0, 1, 2, 3):
        return value
    return 3  # Unknown


def safe_float(row: sqlite3.Row, key: VideoInfoKey) -> float:
    """Return a float from a Row object, type safe"""
    value = row[key] if key in row.keys() else None
    return float(value) if isinstance(value, (int, float)) else 0.0


def safe_bool(row: sqlite3.Row, key: VideoInfoKey) -> bool:
    """Return a bool from a Row object, type safe"""
    value = row[key] if key in row.keys() else None
    return bool(value) if isinstance(value, int) else False


def safe_str_list(row: sqlite3.Row, key: VideoInfoKey) -> list[str]:
    """Return a list[str] from a Row object, type safe"""
    value = row[key] if key in row.keys() else None
    if isinstance(value, str):
        try:
            parsed = json.loads(value)  # pyright: ignore[reportAny]
            if isinstance(parsed, list) and all(
                isinstance(x, str) for x in parsed  # pyright: ignore[reportUnknownVariableType]
            ):
                return parsed  # pyright: ignore[reportUnknownVariableType]
        except json.JSONDecodeError:
            return []
    return []


# -----------------------------
# Row -> VideoInfo converter
# -----------------------------
def row_to_video_info(row: sqlite3.Row) -> VideoInfo:
    """Convert a sqlite3.Row from the `videos` table into a VideoInfo dict."""
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
        "removed_segments_int": safe_int(row, "removed_segments_int"),
        "removed_segments_duration": safe_float(row, "removed_segments_duration"),
        "lyrics": safe_str(row, "lyrics"),
        "subtitles": safe_str(row, "subtitles"),
        "syncedlyrics": safe_str(row, "syncedlyrics"),
        "auto_subs": safe_str(row, "auto_subs"),
        "try_lyrics_if_not": safe_bool(row, "try_lyrics_if_not"),
        "update_thumbnail": safe_bool(row, "update_thumbnail"),
        "remove_thumbnail": safe_bool(row, "remove_thumbnail"),
        "remove_lyrics": safe_bool(row, "remove_lyrics"),
        "lyrics_retries": safe_int(row, "lyrics_retries"),
        "tags": safe_str_list(row, "tags"),
        "recompute_tags": safe_bool(row, "recompute_tags"),
        "recompute_album": safe_bool(row, "recompute_album"),
        "recompute_yt_info": safe_bool(row, "recompute_yt_info"),
        "remix_of": safe_str(row, "remix_of"),
        "recompute_remix_of": safe_bool(row, "recompute_remix_of"),
        "confidence": safe_float(row, "confidence"),
        "filename": safe_str(row, "filename"),
        "status": safe_status(row, "status"),
        "reason": safe_str(row, "reason"),
        "date_added": safe_float(row, "date_added"),
        "date_modified": safe_float(row, "date_modified"),
    }


def get_video_info_from_db(video_id: str, cur: sqlite3.Cursor) -> VideoInfo:
    """Retrieve a full VideoInfo (with skips, tags, playlists)."""
    _ = cur.execute("SELECT * FROM videos WHERE video_id = ?", (video_id,))
    row: sqlite3.Row = cur.fetchone()  # pyright: ignore[reportAny]
    if not row:
        logger.verbose(f"[Get Video Info] No entry for '{video_id}'")
        return {}

    video_info = row_to_video_info(row)

    # --- Tags ---
    _ = cur.execute(
        "SELECT t.tag FROM tags t JOIN video_tags vt ON t.tag_id = vt.tag_id WHERE vt.video_id = ?",
        (video_id,),
    )
    tags = [t["tag"] for t in cur.fetchall()]  # pyright: ignore[reportAny]
    if tags:
        video_info["tags"] = tags

    # --- Skips ---
    _ = cur.execute(
        "SELECT segment_start, segment_end FROM removed_segments WHERE video_id = ? ORDER BY segment_start",
        (video_id,),
    )
    skips = [(s["segment_start"], s["segment_end"]) for s in cur.fetchall()]  # pyright: ignore[reportAny]
    if skips:
        video_info["skips"] = skips

    # --- Ids ---
    _ = cur.execute(
        "SELECT id FROM ids WHERE ids.video_id = ?",
        (video_id,)
    )
    entry_id = cur.fetchone()  # pyright: ignore[reportAny]
    if isinstance(entry_id, int):
        video_info["entry_id"] = entry_id

    # USELESS
    # --- Playlist association ---
    # _ = cur.execute(
    #     """
    #     SELECT p.playlist_id, pv.playlist_item_id, pv.position
    #     FROM playlists p
    #     JOIN playlist_videos pv ON pv.playlist_id = p.playlist_id
    #     WHERE pv.video_id = ?
    #     """,
    #     (video_id,),
    # )
    # pl_row = cur.fetchone()
    # if pl_row:
    #     video_info["playlist_id"] = pl_row["playlist_id"]
    #     video_info["playlist_item_id"] = pl_row["playlist_item_id"]
    #     video_info["position"] = pl_row["position"]

    return video_info


def get_entry_id(video_id: str, cur: sqlite3.Cursor) -> int:
    """
    Fetch the DB and returns the corresponding entry_id (to sort correctly the videos)
    """
    return cast(
        int,
        cur.execute(
            """
            SELECT id FROM ids WHERE video_id = ?
            """,
            (video_id,)
        ).fetchone()
    )
