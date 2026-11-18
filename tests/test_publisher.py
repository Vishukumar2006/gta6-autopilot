"""Unit tests for SocialPublisher."""

import unittest
import tempfile
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import SystemConfig
from src.database import Database
from src.publisher import SocialPublisher


class TestSocialPublisher(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp_dir.name) / "test.db")
        self.config = SystemConfig()
        self.config.social.dry_run = True
        self.publisher = SocialPublisher(self.config, self.db)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_schedule_and_process_queue(self):
        # Create a mock video file
        clip_file = Path(self.temp_dir.name) / "clip.mp4"
        with open(clip_file, "wb") as f:
            f.write(b"MOCK_CLIP")

        self.db.add_clip(
            clip_id="test_clip_pub",
            stream_id="stream_xyz",
            title="Crazy GTA 6 Police Chase",
            hook_text="POLICE AI TOO SMART! 🚔",
            file_path=str(clip_file),
            duration=25.0,
            start_time=0.0,
            end_time=25.0,
            excitement_score=9.2,
        )

        # Schedule to YouTube and Instagram
        pub_ids = self.publisher.schedule_clip(
            clip_id="test_clip_pub",
            title="Crazy GTA 6 Police Chase #Shorts",
            caption="Check out this chase!",
            hashtags="#gta6 #reels",
            platforms=["youtube", "instagram"],
            delay_minutes=0,
        )
        self.assertEqual(len(pub_ids), 2)

        # Process pending queue
        res = self.publisher.process_pending_queue()
        self.assertEqual(res["processed"], 2)
        self.assertEqual(res["published"], 2)
        self.assertEqual(res["failed"], 0)

        # Check publications table
        pubs = self.db.get_recent_publications(10)
        self.assertEqual(len(pubs), 2)
        for p in pubs:
            self.assertEqual(p["status"], "PUBLISHED")
            self.assertTrue(p["remote_url"].startswith("http"))


if __name__ == "__main__":
    unittest.main()
