import sqlite3

from FUNCTIONS.HELPERS.logger import setup_logger

logger = setup_logger(__name__)


def migrate_database_schema(conn: sqlite3.Connection, cur: sqlite3.Cursor) -> None:
    """
    Bring an existing database up to date with the current schema.
    - Creates missing tables
    - Adds missing columns
    - Does not remove or overwrite existing data
    """

    # ------------------------------------------------------------
    # 1. Create base tables if they don't exist
    # ------------------------------------------------------------

    logger.info("[DB MIGRATION] Ensuring required tables exist...")

    _ = cur.execute(
        """
        CREATE TABLE IF NOT EXISTS videos (
            video_id TEXT PRIMARY KEY,
            title TEXT,
            thumbnail_url TEXT,
            description TEXT,
            channel_id TEXT,
            channel_url TEXT,
            view_count INTEGER,
            comment_count INTEGER,
            like_count INTEGER,
            uploader TEXT,
            channel_follower_count INTEGER,
            uploader_id TEXT,
            uploader_url TEXT,
            upload_date TEXT,
            duration INTEGER,
            duration_string TEXT,
            removed_segments_int INTEGER,
            removed_segments_duration REAL,
            lyrics TEXT,
            subtitles TEXT,
            syncedlyrics TEXT,
            auto_subs TEXT,
            try_lyrics_if_not INTEGER DEFAULT 0,
            update_thumbnail INTEGER DEFAULT 0,
            remove_thumbnail INTEGER DEFAULT 0,
            remove_lyrics INTEGER DEFAULT 0,
            lyrics_retries INTEGER DEFAULT 0,
            recompute_tags INTEGER DEFAULT 0,
            recompute_album INTEGER DEFAULT 0,
            recompute_yt_info INTEGER DEFAULT 0,
            remix_of TEXT,
            recompute_remix_of INTEGER DEFAULT 0,
            confidence REAL DEFAULT 0.0,
            filename TEXT,
            status INTEGER DEFAULT 3,
            reason TEXT,
            date_added REAL DEFAULT (strftime('%s','now')),
            date_modified REAL DEFAULT (strftime('%s','now'))
        );
        """
    )

    _ = cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tags (
            tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
            tag TEXT UNIQUE
        );
        """
    )

    _ = cur.execute(
        """
        CREATE TABLE IF NOT EXISTS video_tags (
            video_id TEXT,
            tag_id INTEGER,
            PRIMARY KEY (video_id, tag_id),
            FOREIGN KEY (video_id) REFERENCES videos(video_id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags(tag_id) ON DELETE CASCADE
        );
        """
    )

    _ = cur.execute(
        """
        CREATE TABLE IF NOT EXISTS removed_segments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT NOT NULL,
            segment_start REAL,
            segment_end REAL,
            FOREIGN KEY (video_id) REFERENCES videos(video_id) ON DELETE CASCADE
        );
        """
    )

    _ = cur.execute(
        """
        CREATE TABLE IF NOT EXISTS playlists (
            playlist_id TEXT PRIMARY KEY
        );
        """
    )

    _ = cur.execute(
        """
        CREATE TABLE IF NOT EXISTS playlist_videos (
            playlist_id TEXT,
            video_id TEXT,
            playlist_item_id TEXT,
            position INTEGER,
            PRIMARY KEY (playlist_id, video_id),
            FOREIGN KEY (playlist_id) REFERENCES playlists(playlist_id) ON DELETE CASCADE,
            FOREIGN KEY (video_id) REFERENCES videos(video_id) ON DELETE CASCADE
        );
        """
    )

    # ------------------------------------------------------------
    # 2. Add missing columns to `videos`
    # ------------------------------------------------------------
    _ = cur.execute("PRAGMA table_info(videos)")
    existing_columns = {row["name"] for row in cur.fetchall()}  # pyright: ignore[reportAny]

    EXPECTED_COLUMNS = {
        "video_id": "TEXT",
        "title": "TEXT",
        "thumbnail_url": "TEXT",
        "description": "TEXT",
        "channel_id": "TEXT",
        "channel_url": "TEXT",
        "view_count": "INTEGER",
        "comment_count": "INTEGER",
        "like_count": "INTEGER",
        "uploader": "TEXT",
        "channel_follower_count": "INTEGER",
        "uploader_id": "TEXT",
        "uploader_url": "TEXT",
        "upload_date": "TEXT",
        "duration": "INTEGER",
        "duration_string": "TEXT",
        "removed_segments_int": "INTEGER",
        "removed_segments_duration": "REAL",
        "lyrics": "TEXT",
        "subtitles": "TEXT",
        "syncedlyrics": "TEXT",
        "auto_subs": "TEXT",
        "try_lyrics_if_not": "INTEGER DEFAULT 0",
        "update_thumbnail": "INTEGER DEFAULT 0",
        "remove_thumbnail": "INTEGER DEFAULT 0",
        "remove_lyrics": "INTEGER DEFAULT 0",
        "lyrics_retries": "INTEGER DEFAULT 0",
        "recompute_tags": "INTEGER DEFAULT 0",
        "recompute_album": "INTEGER DEFAULT 0",
        "recompute_yt_info": "INTEGER DEFAULT 0",
        "remix_of": "TEXT",
        "recompute_remix_of": "INTEGER DEFAULT 0",
        "confidence": "REAL DEFAULT 0.0",
        "filename": "TEXT",
        "status": "INTEGER DEFAULT 3",
        "reason": "TEXT",
        "date_added": "REAL DEFAULT (strftime('%s','now'))",
        "date_modified": "REAL DEFAULT (strftime('%s','now'))",
    }

    added_cols: list[str] = []
    for col, col_type in EXPECTED_COLUMNS.items():
        if col not in existing_columns:
            _ = cur.execute(f"ALTER TABLE videos ADD COLUMN {col} {col_type}")
            added_cols.append(col)

    if added_cols:
        logger.info(f"[DB MIGRATION] Added missing columns to videos: {added_cols}")
    else:
        logger.debug("[DB MIGRATION] No missing columns in videos.")

    conn.commit()
    logger.info("[DB MIGRATION] Schema migration completed successfully.")
