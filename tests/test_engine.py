"""Unit tests for AutopilotEngine orchestrator."""

import unittest
import tempfile
import time
from pathlib import Path
from src.config import SystemConfig
from src.database import Database
from src.engine import AutopilotEngine


class TestAutopilotEngine(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp_dir.name) / "test_engine.db")
        self.config = SystemConfig()
        self.config.low_spec_mode = True
        self.config.social.dry_run = True
        self.config.stream.max_streams_per_cycle = 1
        self.engine = AutopilotEngine(self.config, self.db)

    def tearDown(self):
        if self.engine.is_running:
            self.engine.stop()
        self.temp_dir.cleanup()

    def test_engine_start_stop(self):
        self.assertFalse(self.engine.is_running)
        self.engine.run_full_cycle = lambda: {}  # mock cycle for start/stop test
        self.engine.start()
        self.assertTrue(self.engine.is_running)
        time.sleep(0.05)
        self.engine.stop()
        self.assertFalse(self.engine.is_running)

    def test_process_stream_and_queue(self):
        mock_stream = {
            "stream_id": "test_stream_001",
            "title": "GTA 6 INSANE COP CHASE",
            "url": "https://youtube.com/watch?v=mock_stream_1",
            "channel_name": "TestChannel",
            "view_count": 5000,
        }
        self.db.add_stream(
            stream_id=mock_stream["stream_id"],
            title=mock_stream["title"],
            url=mock_stream["url"],
            channel_name=mock_stream["channel_name"],
            view_count=mock_stream["view_count"],
        )

        clips = self.engine.process_stream(mock_stream)
        self.assertGreater(len(clips), 0)

        # Check DB records
        db_clips = self.db.get_clips(10)
        self.assertGreater(len(db_clips), 0)

        pending_pubs = self.db.get_pending_publications()
        self.assertGreater(len(pending_pubs), 0)

    def test_run_full_cycle(self):
        summary = self.engine.run_full_cycle()
        self.assertIn("cycle", summary)
        self.assertIn("new_streams", summary)
        self.assertIn("clips_generated", summary)
        self.assertIn("publications_processed", summary)
        self.assertEqual(summary["cycle"], 1)


if __name__ == "__main__":
    unittest.main()
