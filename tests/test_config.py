"""Unit tests for configuration management."""

import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import SystemConfig, VideoConfig, StreamConfig, SocialConfig


class TestConfig(unittest.TestCase):
    def test_default_config(self):
        cfg = SystemConfig()
        self.assertTrue(cfg.low_spec_mode)
        self.assertEqual(cfg.port, 8080)
        self.assertEqual(cfg.video.low_spec_width, 720)
        self.assertEqual(cfg.video.low_spec_height, 1280)
        self.assertTrue(cfg.social.dry_run)

    def test_serialization(self):
        cfg = SystemConfig()
        d = cfg.to_dict()
        self.assertIn("video", d)
        self.assertIn("stream", d)
        self.assertIn("social", d)

        cfg2 = SystemConfig.from_dict(d)
        self.assertEqual(cfg2.port, cfg.port)
        self.assertEqual(cfg2.low_spec_mode, cfg.low_spec_mode)

    def test_save_and_load(self, tmp_path=None):
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "test_config.json"
            cfg = SystemConfig(port=9999, low_spec_mode=False)
            cfg.save(f)

            loaded = SystemConfig.load(f)
            self.assertEqual(loaded.port, 9999)
            self.assertFalse(loaded.low_spec_mode)


if __name__ == "__main__":
    unittest.main()
