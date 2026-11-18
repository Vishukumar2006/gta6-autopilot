"""Unit tests for VideoEditor."""

import unittest
import tempfile
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import SystemConfig
from src.video_editor import VideoEditor


class TestVideoEditor(unittest.TestCase):
    def setUp(self):
        self.config = SystemConfig()
        self.editor = VideoEditor(self.config)

    def test_render_clip_and_thumbnail(self):
        with tempfile.TemporaryDirectory() as td:
            dummy_in = Path(td) / "input.mp4"
            with open(dummy_in, "wb") as f:
                f.write(b"RAW_VIDEO_CONTENT" * 512)

            out_clip = self.editor.render_vertical_clip(
                input_path=dummy_in,
                start_time=0.0,
                duration=15.0,
                hook_text="WAIT FOR IT! 😱",
                output_name="test_clip_1",
            )
            self.assertTrue(out_clip.exists())
            self.assertGreater(out_clip.stat().st_size, 0)

            thumb = self.editor.generate_thumbnail(out_clip, "test_clip_1")
            self.assertTrue(thumb.exists())
            self.assertGreater(thumb.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
