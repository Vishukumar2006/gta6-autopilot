"""Unit tests for SQLite database operations."""

import unittest
import tempfile
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.database import Database


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.db = Database(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_stream_crud(self):
        # Stream exists check
        self.assertFalse(self.db.stream_exists("stream_123"))

        # Add stream
        added = self.db.add_stream(
            stream_id="stream_123",
            title="GTA 6 Live Gameplay",
            url="https://youtube.com/watch?v=123",
            channel_name="GamerChannel",
            view_count=500,
        )
        self.assertTrue(added)
        self.assertTrue(self.db.stream_exists("stream_123"))

        # Duplicate stream rejected
        added_again = self.db.add_stream(
            stream_id="stream_123",
            title="Duplicate",
            url="https://youtube.com/watch?v=123",
        )
        self.assertFalse(added_again)

        # Update status
        self.db.update_stream_status("stream_123", "PROCESSED")
        streams = self.db.get_recent_streams(10)
        self.assertEqual(len(streams), 1)
        self.assertEqual(streams[0]["status"], "PROCESSED")

    def test_clip_crud(self):
        self.db.add_clip(
            clip_id="clip_001",
            stream_id="stream_123",
            title="Epic GTA 6 Stunt",
            hook_text="WAIT FOR THE END! 😱",
            file_path="/path/to/clip.mp4",
            duration=30.0,
            start_time=10.0,
            end_time=40.0,
            excitement_score=9.5,
        )

        clip = self.db.get_clip("clip_001")
        self.assertIsNotNone(clip)
        self.assertEqual(clip["hook_text"], "WAIT FOR THE END! 😱")
        self.assertEqual(clip["status"], "RENDERED")

        # Update clip status
        self.db.update_clip_status("clip_001", "POSTED")
        clip_updated = self.db.get_clip("clip_001")
        self.assertEqual(clip_updated["status"], "POSTED")

    def test_publication_queue(self):
        self.db.add_clip(
            clip_id="clip_002",
            stream_id="stream_123",
            title="GTA 6 Leak",
            hook_text="SECRET REVEALED",
            file_path="/path/to/clip2.mp4",
            duration=25.0,
            start_time=0.0,
            end_time=25.0,
            excitement_score=8.8,
        )

        self.db.add_publication(
            pub_id="pub_yt_1",
            clip_id="clip_002",
            platform="youtube",
            title="GTA 6 Leak #Shorts",
            caption="Check this out!",
            hashtags="#gta6 #shorts",
        )

        pending = self.db.get_pending_publications()
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["platform"], "youtube")

        # Mark published
        self.db.mark_published(
            pub_id="pub_yt_1",
            remote_id="yt_video_abc",
            remote_url="https://youtube.com/shorts/yt_video_abc",
        )

        pending_after = self.db.get_pending_publications()
        self.assertEqual(len(pending_after), 0)

        # Dashboard stats check
        stats = self.db.get_dashboard_stats()
        self.assertEqual(stats["total_published"], 1)
        self.assertEqual(stats["total_pending"], 0)


if __name__ == "__main__":
    unittest.main()
