"""End-to-End Pipeline Integration Test."""

import unittest
import tempfile
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import SystemConfig
from src.database import Database
from src.engine import AutopilotEngine


class TestEndToEndPipeline(unittest.TestCase):
    def test_full_autonomous_cycle(self):
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "test_e2e.db"
            db = Database(db_path)
            config = SystemConfig()
            config.low_spec_mode = True
            config.social.dry_run = True
            config.stream.max_streams_per_cycle = 1

            engine = AutopilotEngine(config, db)

            # Run complete cycle
            summary = engine.run_full_cycle()

            self.assertGreaterEqual(summary["new_streams"], 1)
            self.assertGreaterEqual(summary["clips_generated"], 1)
            self.assertGreaterEqual(summary["publications_processed"], 1)

            # Verify Database state
            stats = db.get_dashboard_stats()
            self.assertGreaterEqual(stats["total_streams"], 1)
            self.assertGreaterEqual(stats["total_clips"], 1)
            self.assertGreaterEqual(stats["total_published"], 1)

            clips = db.get_clips(10)
            self.assertTrue(len(clips) > 0)
            first_clip = clips[0]
            self.assertTrue(Path(first_clip["file_path"]).exists())
            self.assertGreater(first_clip["duration"], 0.0)
            self.assertGreater(len(first_clip["hook_text"]), 0)


if __name__ == "__main__":
    unittest.main()
