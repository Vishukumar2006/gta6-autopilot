"""Unit tests for HighlightDetector."""

import unittest
import tempfile
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import SystemConfig
from src.highlight_detector import HighlightDetector


class TestHighlightDetector(unittest.TestCase):
    def setUp(self):
        self.config = SystemConfig()
        self.detector = HighlightDetector(self.config)

    def test_detect_highlights_boundaries(self):
        with tempfile.TemporaryDirectory() as td:
            dummy_file = Path(td) / "dummy.mp4"
            with open(dummy_file, "wb") as f:
                f.write(b"MOCK_VIDEO_DATA" * 1024)

            highlights = self.detector.detect_highlights(
                dummy_file, stream_title="GTA 6 Leaked Gameplay", max_clips=2
            )
            self.assertGreater(len(highlights), 0)
            self.assertLessEqual(len(highlights), 2)

            hl = highlights[0]
            self.assertGreaterEqual(hl.start_time, 0.0)
            self.assertGreater(hl.end_time, hl.start_time)
            self.assertGreater(hl.excitement_score, 0.0)
            self.assertIn("hook_text", hl.suggested_hook)


if __name__ == "__main__":
    unittest.main()
