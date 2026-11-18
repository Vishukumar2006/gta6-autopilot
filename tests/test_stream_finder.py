"""Unit tests for StreamFinder."""

import unittest
import tempfile
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import SystemConfig
from src.database import Database
from src.stream_finder import StreamFinder


class TestStreamFinder(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp_dir.name) / "test.db")
        self.config = SystemConfig()
        self.finder = StreamFinder(self.config, self.db)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_search_and_deduplication(self):
        # First discovery
        streams = self.finder.search_live_streams()
        self.assertGreater(len(streams), 0)
        for s in streams:
            self.assertIn("stream_id", s)
            self.assertIn("title", s)
            self.assertIn("url", s)
            self.assertTrue(self.db.stream_exists(s["stream_id"]))

        # Second discovery with same simulated streams should find 0 new (deduplication)
        new_streams = self.finder.search_live_streams()
        self.assertEqual(len(new_streams), 0)


if __name__ == "__main__":
    unittest.main()
