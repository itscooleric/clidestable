"""Tests for clidestable.server — Flask API and routes."""

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, MagicMock

from clidestable.server import create_app


class TestAPI(unittest.TestCase):
    """Tests for the REST API endpoints."""

    def setUp(self) -> None:
        self.tmpdir = TemporaryDirectory()
        # Patch subprocess.Popen to avoid starting real ttyd
        self.popen_patcher = patch("clidestable.stall.subprocess.Popen")
        self.mock_popen = self.popen_patcher.start()
        self.mock_popen.return_value = MagicMock(pid=42)

        self.app = create_app(log_dir=self.tmpdir.name, base_port=7701)
        self.app.testing = True
        self.client = self.app.test_client()

    def tearDown(self) -> None:
        self.popen_patcher.stop()
        self.tmpdir.cleanup()

    def test_list_stalls_empty(self) -> None:
        """GET /api/stalls returns empty list initially."""
        resp = self.client.get("/api/stalls")
        data = json.loads(resp.data)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(data["stalls"], [])

    def test_create_stall(self) -> None:
        """POST /api/stalls creates a stall."""
        resp = self.client.post("/api/stalls",
            data=json.dumps({"name": "edge"}),
            content_type="application/json")
        data = json.loads(resp.data)
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(data["ok"])
        self.assertEqual(data["stall"]["name"], "edge")
        self.assertEqual(data["stall"]["port"], 7701)

    def test_create_stall_no_name(self) -> None:
        """POST /api/stalls without name returns 400."""
        resp = self.client.post("/api/stalls",
            data=json.dumps({}),
            content_type="application/json")
        self.assertEqual(resp.status_code, 400)

    def test_create_duplicate_stall(self) -> None:
        """POST /api/stalls with existing name returns 409."""
        self.client.post("/api/stalls",
            data=json.dumps({"name": "edge"}),
            content_type="application/json")
        with patch("os.kill", return_value=None):
            resp = self.client.post("/api/stalls",
                data=json.dumps({"name": "edge"}),
                content_type="application/json")
        self.assertEqual(resp.status_code, 409)

    def test_list_after_create(self) -> None:
        """GET /api/stalls shows created stalls."""
        self.client.post("/api/stalls",
            data=json.dumps({"name": "edge"}),
            content_type="application/json")
        resp = self.client.get("/api/stalls")
        data = json.loads(resp.data)
        self.assertEqual(len(data["stalls"]), 1)
        self.assertEqual(data["stalls"][0]["name"], "edge")

    def test_destroy_stall(self) -> None:
        """DELETE /api/stalls/<name> destroys the stall."""
        self.client.post("/api/stalls",
            data=json.dumps({"name": "edge"}),
            content_type="application/json")
        with patch("os.kill"):
            resp = self.client.delete("/api/stalls/edge")
        data = json.loads(resp.data)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(data["ok"])

    def test_destroy_nonexistent(self) -> None:
        """DELETE /api/stalls/<name> returns 404 for missing stall."""
        resp = self.client.delete("/api/stalls/nope")
        self.assertEqual(resp.status_code, 404)

    def test_stall_log(self) -> None:
        """GET /api/stalls/<name>/log returns log content."""
        # Write a fake log
        log_path = Path(self.tmpdir.name) / ".sdale-edge.log"
        log_path.write_text("── 12:00:00 $ echo hello\nhello\n")

        resp = self.client.get("/api/stalls/edge/log")
        data = json.loads(resp.data)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("hello", data["log"])

    def test_dashboard_200(self) -> None:
        """GET / returns 200."""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)

    def test_split_view_200(self) -> None:
        """GET /view returns 200."""
        resp = self.client.get("/view")
        self.assertEqual(resp.status_code, 200)

    def test_log_view_200(self) -> None:
        """GET /log/<name> returns 200."""
        resp = self.client.get("/log/edge")
        self.assertEqual(resp.status_code, 200)


class TestCLI(unittest.TestCase):
    """Tests for the CLI entry point."""

    def test_version(self) -> None:
        """--version outputs version string."""
        from clidestable.cli import main
        import sys
        with self.assertRaises(SystemExit) as ctx:
            sys.argv = ["clidestable", "--version"]
            main()
        self.assertEqual(ctx.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
