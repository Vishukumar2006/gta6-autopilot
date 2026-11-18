"""SQLite Database management for GTA 6 Autonomous Pipeline."""

import sqlite3
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
from src.config import DATA_DIR, ensure_directories

DB_PATH = DATA_DIR / "autopilot.db"


class Database:
    def __init__(self, db_path: Path = DB_PATH):
        ensure_directories()
        self.db_path = str(db_path)
        self.init_db()

    @contextmanager
    def get_connection(self):
        """Yield a sqlite3 connection with WAL mode and automatic cleanup."""
        conn = sqlite3.connect(self.db_path, timeout=15.0)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def init_db(self) -> None:
        """Create tables if they do not exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA synchronous=NORMAL;")

            # Streams table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS streams (
                    stream_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    channel_name TEXT,
                    url TEXT NOT NULL,
                    view_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'DISCOVERED',
                    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP,
                    error_message TEXT
                )
            """
            )

            # Clips table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS clips (
                    clip_id TEXT PRIMARY KEY,
                    stream_id TEXT,
                    title TEXT NOT NULL,
                    hook_text TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    thumbnail_path TEXT,
                    duration REAL DEFAULT 0.0,
                    start_time REAL DEFAULT 0.0,
                    end_time REAL DEFAULT 0.0,
                    excitement_score REAL DEFAULT 0.0,
                    status TEXT DEFAULT 'RENDERED',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(stream_id) REFERENCES streams(stream_id)
                )
            """
            )

            # Publishing Queue & History table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS publications (
                    pub_id TEXT PRIMARY KEY,
                    clip_id TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    title TEXT NOT NULL,
                    caption TEXT NOT NULL,
                    hashtags TEXT NOT NULL,
                    status TEXT DEFAULT 'PENDING',
                    remote_id TEXT,
                    remote_url TEXT,
                    scheduled_at TIMESTAMP,
                    published_at TIMESTAMP,
                    error_message TEXT,
                    FOREIGN KEY(clip_id) REFERENCES clips(clip_id)
                )
            """
            )

            # System logs table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    level TEXT NOT NULL,
                    module TEXT NOT NULL,
                    message TEXT NOT NULL
                )
            """
            )

            conn.commit()

    # --- Streams ---
    def stream_exists(self, stream_id: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM streams WHERE stream_id = ?", (stream_id,))
            return cursor.fetchone() is not None

    def add_stream(
        self,
        stream_id: str,
        title: str,
        url: str,
        channel_name: str = "",
        view_count: int = 0,
    ) -> bool:
        if self.stream_exists(stream_id):
            return False
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO streams (stream_id, title, channel_name, url, view_count, status, discovered_at)
                VALUES (?, ?, ?, ?, ?, 'DISCOVERED', CURRENT_TIMESTAMP)
            """,
                (stream_id, title, channel_name, url, view_count),
            )
            conn.commit()
            return True

    def update_stream_status(
        self, stream_id: str, status: str, error_message: Optional[str] = None
    ) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.datetime.utcnow().isoformat()
            cursor.execute(
                """
                UPDATE streams
                SET status = ?, processed_at = ?, error_message = ?
                WHERE stream_id = ?
            """,
                (status, now, error_message, stream_id),
            )
            conn.commit()

    def get_recent_streams(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM streams ORDER BY discovered_at DESC LIMIT ?",
                (limit,),
            )
            return [dict(r) for r in cursor.fetchall()]

    # --- Clips ---
    def add_clip(
        self,
        clip_id: str,
        stream_id: str,
        title: str,
        hook_text: str,
        file_path: str,
        duration: float,
        start_time: float,
        end_time: float,
        excitement_score: float,
        thumbnail_path: Optional[str] = None,
        status: str = "RENDERED",
    ) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO clips (
                    clip_id, stream_id, title, hook_text, file_path,
                    thumbnail_path, duration, start_time, end_time,
                    excitement_score, status, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
                (
                    clip_id,
                    stream_id,
                    title,
                    hook_text,
                    file_path,
                    thumbnail_path,
                    duration,
                    start_time,
                    end_time,
                    excitement_score,
                    status,
                ),
            )
            conn.commit()

    def get_clips(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM clips ORDER BY created_at DESC LIMIT ?", (limit,)
            )
            return [dict(r) for r in cursor.fetchall()]

    def get_clip(self, clip_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clips WHERE clip_id = ?", (clip_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_clip_status(self, clip_id: str, status: str) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE clips SET status = ? WHERE clip_id = ?",
                (status, clip_id),
            )
            conn.commit()

    # --- Publications / Queue ---
    def add_publication(
        self,
        pub_id: str,
        clip_id: str,
        platform: str,
        title: str,
        caption: str,
        hashtags: str,
        scheduled_at: Optional[str] = None,
    ) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO publications (
                    pub_id, clip_id, platform, title, caption,
                    hashtags, status, scheduled_at
                )
                VALUES (?, ?, ?, ?, ?, ?, 'PENDING', ?)
            """,
                (pub_id, clip_id, platform, title, caption, hashtags, scheduled_at),
            )
            conn.commit()

    def get_pending_publications(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT p.*, c.file_path, c.thumbnail_path, c.hook_text
                FROM publications p
                JOIN clips c ON p.clip_id = c.clip_id
                WHERE p.status = 'PENDING'
                ORDER BY p.scheduled_at ASC
            """
            )
            return [dict(r) for r in cursor.fetchall()]

    def mark_published(
        self,
        pub_id: str,
        remote_id: str,
        remote_url: str,
    ) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.datetime.utcnow().isoformat()
            cursor.execute(
                """
                UPDATE publications
                SET status = 'PUBLISHED', remote_id = ?, remote_url = ?, published_at = ?
                WHERE pub_id = ?
            """,
                (remote_id, remote_url, now, pub_id),
            )
            conn.commit()

    def mark_publication_failed(self, pub_id: str, error_message: str) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE publications
                SET status = 'FAILED', error_message = ?
                WHERE pub_id = ?
            """,
                (error_message, pub_id),
            )
            conn.commit()

    def get_recent_publications(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT p.*, c.hook_text, c.thumbnail_path
                FROM publications p
                JOIN clips c ON p.clip_id = c.clip_id
                ORDER BY COALESCE(p.published_at, p.scheduled_at) DESC
                LIMIT ?
            """,
                (limit,),
            )
            return [dict(r) for r in cursor.fetchall()]

    # --- System Logs ---
    def log(self, level: str, module: str, message: str) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO logs (level, module, message) VALUES (?, ?, ?)",
                (level.upper(), module, message),
            )
            conn.commit()

    def get_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM logs ORDER BY id DESC LIMIT ?", (limit,)
            )
            return [dict(r) for r in cursor.fetchall()]

    # --- Dashboard Metrics ---
    def get_dashboard_stats(self) -> Dict[str, Any]:
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM streams")
            total_streams = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM clips")
            total_clips = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM publications WHERE status = 'PUBLISHED'"
            )
            total_published = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM publications WHERE status = 'PENDING'"
            )
            total_pending = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM publications WHERE status = 'FAILED'"
            )
            total_failed = cursor.fetchone()[0]

            return {
                "total_streams": total_streams,
                "total_clips": total_clips,
                "total_published": total_published,
                "total_pending": total_pending,
                "total_failed": total_failed,
            }
