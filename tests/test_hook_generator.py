"""Unit tests for Hook & SEO Generator."""

import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.hook_generator import HookGenerator


class TestHookGenerator(unittest.TestCase):
    def test_generate_hook(self):
        hook_pkg = HookGenerator.generate_hook("leak")
        self.assertIn("hook_text", hook_pkg)
        self.assertIn("title", hook_pkg)
        self.assertIn("description", hook_pkg)
        self.assertIn("caption", hook_pkg)
        self.assertIn("hashtags", hook_pkg)
        self.assertIn("#gta6", hook_pkg["hashtags"].lower())
        self.assertGreater(len(hook_pkg["hook_text"]), 5)

    def test_detect_category(self):
        self.assertEqual(HookGenerator.detect_category_from_text("NEW LEAK FOUND"), "leak")
        self.assertEqual(HookGenerator.detect_category_from_text("Insane water physics test"), "physics")
        self.assertEqual(HookGenerator.detect_category_from_text("Streamer funny rage compilation"), "funny")
        self.assertEqual(HookGenerator.detect_category_from_text("GTA 6 Cop chase gameplay"), "action")


if __name__ == "__main__":
    unittest.main()
