"""
Migrate an old database to the latest version
"""

import sqlite3

from FUNCTIONS.HELPERS.logger import setup_logger
from FUNCTIONS.sql_requests import commit_changes_to_db

logger = setup_logger(__name__)


def migrate_database_schema(conn: sqlite3.Connection, cur: sqlite3.Cursor) -> None:
    """
    Bring an existing database up to date with the current schema.
    - Creates missing tables
    - Adds missing columns (matching init_db)
    - Does not remove or overwrite existing data
    """

    logger.info("[DB MIGRATION] Ensuring required tables and columns exist...")

    # ------------------------------------------------------------
    # 1. Create base tables if they don't exist (exactly as in init_db)
    # ------------------------------------------------------------

    _ = cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS videos (
            video_id TEXT PRIMARY KEY,
            title TEXT,
            description TEXT,
            thumbnail_url TEXT,
            channel_id TEXT,
            channel_url TEXT,
            uploader TEXT,
            uploader_id TEXT,
            uploader_url TEXT,
            channel_follower_count INTEGER CHECK(channel_follower_count >= 0),
            view_count INTEGER CHECK(view_count >= 0),
            comment_count INTEGER CHECK(comment_count >= 0),
            like_count INTEGER CHECK(like_count >= 0),
            upload_date TEXT,
            duration INTEGER CHECK(duration >= 0),
            duration_string TEXT,
            privacy_status TEXT,
            removed_segments_int INTEGER DEFAULT 0,
            removed_segments_duration REAL DEFAULT 0.0,
            lyrics TEXT,
            subtitles TEXT,
            syncedlyrics TEXT,
            syncedlyrics_query TEXT,
            auto_subs TEXT,
            try_lyrics_if_not BOOLEAN NOT NULL CHECK (try_lyrics_if_not IN (0,1)) DEFAULT 1,
            lyrics_retries INTEGER CHECK (lyrics_retries >= 0) DEFAULT 0,
            update_thumbnail BOOLEAN NOT NULL CHECK (update_thumbnail IN (0,1)) DEFAULT 0,
            remove_thumbnail BOOLEAN NOT NULL CHECK (remove_thumbnail IN (0,1)) DEFAULT 0,
            remove_lyrics BOOLEAN NOT NULL CHECK (remove_lyrics IN (0,1)) DEFAULT 0,
            recompute_tags BOOLEAN NOT NULL CHECK (recompute_tags IN (0,1)) DEFAULT 1,
            recompute_album BOOLEAN NOT NULL CHECK (recompute_album IN (0,1)) DEFAULT 1,
            recompute_yt_info BOOLEAN NOT NULL CHECK (recompute_yt_info IN (0,1)) DEFAULT 0,
            remix_of TEXT,
            recompute_remix_of BOOLEAN NOT NULL CHECK (recompute_remix_of IN (0,1)) DEFAULT 1,
            confidence REAL CHECK (confidence >= 0 AND confidence <= 1),
            filename TEXT,
            status INTEGER NOT NULL CHECK (status IN (0,1,2,3)) DEFAULT 3,
            reason TEXT,
            date_added REAL DEFAULT ((julianday('now') - 2440587.5) * 86400.0),
            date_modified REAL DEFAULT ((julianday('now') - 2440587.5) * 86400.0)
        );

        CREATE TABLE IF NOT EXISTS playlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            playlist_id TEXT UNIQUE NOT NULL,
            title TEXT,
            description TEXT,
            channel_id TEXT,
            date_added REAL DEFAULT ((julianday('now') - 2440587.5) * 86400.0)
        );

        CREATE TABLE IF NOT EXISTS playlist_videos (
            playlist_id TEXT NOT NULL,
            video_id TEXT NOT NULL,
            playlist_item_id TEXT,
            position INTEGER CHECK(position >= 0),
            PRIMARY KEY (playlist_id, video_id),
            FOREIGN KEY(playlist_id) REFERENCES playlists(playlist_id) ON DELETE CASCADE,
            FOREIGN KEY(video_id) REFERENCES videos(video_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS removed_segments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT NOT NULL,
            segment_start REAL NOT NULL CHECK (segment_start >= 0),
            segment_end REAL NOT NULL CHECK (segment_end > segment_start),
            FOREIGN KEY(video_id) REFERENCES videos(video_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS tags (
            tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
            tag TEXT UNIQUE NOT NULL
        );

        CREATE TABLE IF NOT EXISTS video_tags (
            video_id TEXT NOT NULL,
            tag_id INTEGER NOT NULL,
            PRIMARY KEY (video_id, tag_id),
            FOREIGN KEY(video_id) REFERENCES videos(video_id) ON DELETE CASCADE,
            FOREIGN KEY(tag_id) REFERENCES tags(tag_id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_video_status ON videos(status);
        CREATE INDEX IF NOT EXISTS idx_video_uploader ON videos(uploader_id);
        CREATE INDEX IF NOT EXISTS idx_playlist_channel ON playlists(channel_id);
        CREATE INDEX IF NOT EXISTS idx_playlist_video_item ON playlist_videos(playlist_item_id);
        """
    )

    # ------------------------------------------------------------
    # 2. Add missing columns to videos table (sync with init_db)
    # ------------------------------------------------------------
    _ = cur.execute("PRAGMA table_info(videos)")
    existing_columns = {row["name"] for row in cur.fetchall()}  # pyright: ignore[reportAny]

    expected_columns = {
        # Core identifiers
        "video_id": "TEXT",
        "title": "TEXT",
        "description": "TEXT",
        "thumbnail_url": "TEXT",

        # Channel / uploader info
        "channel_id": "TEXT",
        "channel_url": "TEXT",
        "uploader": "TEXT",
        "uploader_id": "TEXT",
        "uploader_url": "TEXT",
        "channel_follower_count": "INTEGER CHECK(channel_follower_count >= 0)",

        # YouTube statistics
        "view_count": "INTEGER CHECK(view_count >= 0)",
        "comment_count": "INTEGER CHECK(comment_count >= 0)",
        "like_count": "INTEGER CHECK(like_count >= 0)",

        # Publication details
        "upload_date": "TEXT",
        "duration": "INTEGER CHECK(duration >= 0)",
        "duration_string": "TEXT",
        "privacy_status": "TEXT",

        # SponsorBlock / skip summary
        "removed_segments_int": "INTEGER DEFAULT 0",
        "removed_segments_duration": "REAL DEFAULT 0.0",

        # Lyrics / subtitle information
        "lyrics": "TEXT",
        "subtitles": "TEXT",
        "syncedlyrics": "TEXT",
        "syncedlyrics_query": "TEXT",
        "auto_subs": "TEXT",
        "try_lyrics_if_not": "BOOLEAN NOT NULL CHECK (try_lyrics_if_not IN (0,1)) DEFAULT 1",
        "lyrics_retries": "INTEGER CHECK (lyrics_retries >= 0) DEFAULT 0",

        # Maintenance / recomputation flags
        "update_thumbnail": "BOOLEAN NOT NULL CHECK (update_thumbnail IN (0,1)) DEFAULT 0",
        "remove_thumbnail": "BOOLEAN NOT NULL CHECK (remove_thumbnail IN (0,1)) DEFAULT 0",
        "remove_lyrics": "BOOLEAN NOT NULL CHECK (remove_lyrics IN (0,1)) DEFAULT 0",
        "recompute_tags": "BOOLEAN NOT NULL CHECK (recompute_tags IN (0,1)) DEFAULT 1",
        "recompute_album": "BOOLEAN NOT NULL CHECK (recompute_album IN (0,1)) DEFAULT 1",
        "recompute_yt_info": "BOOLEAN NOT NULL CHECK (recompute_yt_info IN (0,1)) DEFAULT 0",

        # Remix tracking
        "remix_of": "TEXT",
        "recompute_remix_of": "BOOLEAN NOT NULL CHECK (recompute_remix_of IN (0,1)) DEFAULT 1",
        "confidence": "REAL CHECK (confidence >= 0 AND confidence <= 1)",

        # Local file info
        "filename": "TEXT",
        "status": "INTEGER NOT NULL CHECK (status IN (0,1,2,3)) DEFAULT 3",
        "reason": "TEXT",

        # Timestamps
        "date_added": "REAL DEFAULT ((julianday('now') - 2440587.5) * 86400.0)",
        "date_modified": "REAL DEFAULT ((julianday('now') - 2440587.5) * 86400.0)",
    }

    added: list[str] = []
    for col, col_type in expected_columns.items():
        if col not in existing_columns:
            _ = cur.execute(f"ALTER TABLE videos ADD COLUMN {col} {col_type}")
            added.append(col)

    if added:
        logger.info(f"[DB MIGRATION] Added missing columns to videos: {added}")
    else:
        logger.debug("[DB MIGRATION] No new columns were added.")

    _ = commit_changes_to_db(conn, True)
    logger.info("[DB MIGRATION] Database schema now synchronized with init_db().")
