"""Unit tests for Dashboard REST API and Server."""

import unittest
import urllib.request
import json
import time
import tempfile
from pathlib import Path
from src.config import SystemConfig
from src.database import Database
from src.engine import AutopilotEngine
from src.dashboard import run_dashboard_server


class TestDashboard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.db = Database(Path(cls.temp_dir.name) / "test_dash.db")
        cls.config = SystemConfig(port=8899, host="127.0.0.1")
        cls.config.social.dry_run = True
        cls.engine = AutopilotEngine(cls.config, cls.db)

        # Launch server in non-blocking mode
        cls.server = run_dashboard_server(
            cls.config, cls.engine, cls.db, block=False
        )
        time.sleep(0.4)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "server") and cls.server:
            try:
                cls.server.shutdown()
                cls.server.server_close()
            except Exception:
                pass
        time.sleep(0.2)
        try:
            cls.temp_dir.cleanup()
        except Exception:
            pass

    def test_get_dashboard_html(self):
        url = f"http://127.0.0.1:{self.config.port}/"
        with urllib.request.urlopen(url, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            html = resp.read().decode("utf-8")
            self.assertIn("GTA VI", html)
            self.assertIn("AUTOPILOT PIPELINE", html)
            self.assertIn("Mobile Control Active", html)

    def test_api_status(self):
        url = f"http://127.0.0.1:{self.config.port}/api/status"
        with urllib.request.urlopen(url, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIn("is_running", data)
            self.assertIn("low_spec_mode", data)
            self.assertIn("mobile_url", data)

    def test_api_stats(self):
        url = f"http://127.0.0.1:{self.config.port}/api/stats"
        with urllib.request.urlopen(url, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIn("total_streams", data)
            self.assertIn("total_clips", data)

    def test_action_toggle_autopilot(self):
        url = f"http://127.0.0.1:{self.config.port}/api/action/toggle_autopilot"
        req = urllib.request.Request(url, data=b"{}", method="POST")
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["status"], "success")


if __name__ == "__main__":
    unittest.main()
