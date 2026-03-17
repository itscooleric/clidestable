"""Tests for clidestable.stall — stall manager."""

import os
import signal
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from clidestable.stall import Stall, StallManager


class TestStall(unittest.TestCase):
    """Tests for the Stall dataclass."""

    def test_alive_with_no_pid(self) -> None:
        """Stall with no pid is not alive."""
        stall = Stall(name="test", port=7701, pid=None)
        self.assertFalse(stall.alive)

    def test_alive_with_dead_pid(self) -> None:
        """Stall with a dead pid is not alive."""
        stall = Stall(name="test", port=7701, pid=999999)
        self.assertFalse(stall.alive)

    @patch("os.kill")
    def test_alive_with_running_pid(self, mock_kill: MagicMock) -> None:
        """Stall with a running pid is alive."""
        mock_kill.return_value = None  # no exception = process exists
        stall = Stall(name="test", port=7701, pid=42)
        self.assertTrue(stall.alive)
        mock_kill.assert_called_with(42, 0)

    def test_to_dict(self) -> None:
        """to_dict includes all fields."""
        stall = Stall(name="edge", port=7701, pid=None, log_path=Path("/tmp/test.log"))
        d = stall.to_dict()
        self.assertEqual(d["name"], "edge")
        self.assertEqual(d["port"], 7701)
        self.assertFalse(d["alive"])
        self.assertEqual(d["log_path"], "/tmp/test.log")


class TestStallManager(unittest.TestCase):
    """Tests for the StallManager."""

    def setUp(self) -> None:
        self.tmpdir = TemporaryDirectory()
        self.log_dir = self.tmpdir.name

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    @patch("clidestable.stall.subprocess.Popen")
    def test_create_stall(self, mock_popen: MagicMock) -> None:
        """Create allocates a port and starts ttyd."""
        mock_proc = MagicMock()
        mock_proc.pid = 42
        mock_popen.return_value = mock_proc

        mgr = StallManager(log_dir=self.log_dir, base_port=7701)
        stall = mgr.create("edge")

        self.assertEqual(stall.name, "edge")
        self.assertEqual(stall.port, 7701)
        self.assertEqual(stall.pid, 42)
        mock_popen.assert_called_once()
        # Verify ttyd command
        cmd = mock_popen.call_args[0][0]
        self.assertEqual(cmd[0], "ttyd")
        self.assertIn("--port", cmd)
        self.assertIn("7701", cmd)

    @patch("clidestable.stall.subprocess.Popen")
    def test_create_increments_port(self, mock_popen: MagicMock) -> None:
        """Each stall gets a different port."""
        mock_popen.return_value = MagicMock(pid=1)

        mgr = StallManager(log_dir=self.log_dir, base_port=7701)
        s1 = mgr.create("edge")
        s2 = mgr.create("edge2")

        self.assertEqual(s1.port, 7701)
        self.assertEqual(s2.port, 7702)

    @patch("clidestable.stall.subprocess.Popen")
    def test_create_duplicate_raises(self, mock_popen: MagicMock) -> None:
        """Creating a stall with the same name raises ValueError."""
        mock_proc = MagicMock(pid=42)
        mock_popen.return_value = mock_proc

        mgr = StallManager(log_dir=self.log_dir)
        mgr.create("edge")

        with patch("os.kill", return_value=None):  # make it appear alive
            with self.assertRaises(ValueError):
                mgr.create("edge")

    @patch("clidestable.stall.subprocess.Popen")
    def test_destroy_stall(self, mock_popen: MagicMock) -> None:
        """Destroy removes the stall and kills the process."""
        mock_popen.return_value = MagicMock(pid=42)

        mgr = StallManager(log_dir=self.log_dir)
        mgr.create("edge")

        with patch("os.kill") as mock_kill:
            result = mgr.destroy("edge")
            self.assertTrue(result)
            mock_kill.assert_any_call(42, signal.SIGTERM)

        self.assertIsNone(mgr.get("edge"))

    def test_destroy_nonexistent(self) -> None:
        """Destroying a nonexistent stall returns False."""
        mgr = StallManager(log_dir=self.log_dir)
        self.assertFalse(mgr.destroy("nope"))

    @patch("clidestable.stall.subprocess.Popen")
    def test_get_stall(self, mock_popen: MagicMock) -> None:
        """Get returns the stall or None."""
        mock_popen.return_value = MagicMock(pid=1)

        mgr = StallManager(log_dir=self.log_dir)
        mgr.create("edge")

        self.assertIsNotNone(mgr.get("edge"))
        self.assertIsNone(mgr.get("nope"))

    def test_get_log_empty(self) -> None:
        """get_log returns empty string when no log file."""
        mgr = StallManager(log_dir=self.log_dir)
        self.assertEqual(mgr.get_log("edge"), "")

    def test_get_log_with_content(self) -> None:
        """get_log reads the activity log file."""
        mgr = StallManager(log_dir=self.log_dir)
        log_path = Path(self.log_dir) / ".sdale-edge.log"
        log_path.write_text("line 1\nline 2\nline 3\n")

        result = mgr.get_log("edge", lines=2)
        self.assertIn("line 2", result)
        self.assertIn("line 3", result)

    @patch("clidestable.stall.subprocess.Popen")
    def test_stalls_property(self, mock_popen: MagicMock) -> None:
        """stalls property returns dict of all stalls."""
        mock_popen.return_value = MagicMock(pid=1)

        mgr = StallManager(log_dir=self.log_dir)
        mgr.create("edge")
        mgr.create("edge2")

        stalls = mgr.stalls
        self.assertEqual(len(stalls), 2)
        self.assertIn("edge", stalls)
        self.assertIn("edge2", stalls)


if __name__ == "__main__":
    unittest.main()
