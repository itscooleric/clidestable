"""Stall manager — spawns and tracks shell sessions with ttyd."""

from __future__ import annotations

import logging
import os
import signal
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger("clidestable.stall")

# ttyd ports start here and increment per stall
_BASE_PORT = 7701


@dataclass
class Stall:
    """A named shell session with a ttyd web terminal."""

    name: str
    port: int
    slot: int = 0  # 1-based slot number for path routing
    pid: Optional[int] = None
    log_path: Optional[Path] = None

    @property
    def alive(self) -> bool:
        """Check if the ttyd process is still running."""
        if self.pid is None:
            return False
        try:
            os.kill(self.pid, 0)
            return True
        except (OSError, ProcessLookupError):
            return False

    @property
    def base_path(self) -> str:
        """URL base path for this stall (e.g. /stall/1/)."""
        return f"/stall/{self.slot}/"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "port": self.port,
            "slot": self.slot,
            "base_path": self.base_path,
            "pid": self.pid,
            "alive": self.alive,
            "log_path": str(self.log_path) if self.log_path else None,
        }


class StallManager:
    """Manages named stalls (shell sessions with ttyd terminals)."""

    def __init__(self, log_dir: str = "/opt/stacks",
                 base_port: int = _BASE_PORT) -> None:
        self._stalls: dict[str, Stall] = {}
        self._log_dir = Path(log_dir)
        self._base_port = base_port
        self._next_port = base_port

    @property
    def stalls(self) -> dict[str, Stall]:
        return dict(self._stalls)

    def _allocate_port(self) -> int:
        """Get the next available port."""
        port = self._next_port
        self._next_port += 1
        return port

    def create(self, name: str) -> Stall:
        """Create a new stall (shell session + ttyd).

        Args:
            name: Unique stall name.

        Returns:
            The created Stall.

        Raises:
            ValueError: If a stall with this name already exists.
        """
        if name in self._stalls:
            existing = self._stalls[name]
            if existing.alive:
                raise ValueError(f"Stall '{name}' already exists and is running")
            # Dead stall — clean up and recreate
            del self._stalls[name]

        port = self._allocate_port()
        slot = port - self._base_port + 1  # port 7701 → slot 1
        log_path = self._log_dir / f".sdale-{name}.log"
        base_path = f"/stall/{slot}/"

        # Ensure log file exists
        log_path.touch(exist_ok=True)

        # Start ttyd tailing the activity log — shows agent commands in real time
        # Uses slot-based base path so Caddy can route via single port
        try:
            proc = subprocess.Popen(
                [
                    "ttyd",
                    "--port", str(port),
                    "--readonly",
                    "--base-path", base_path,
                    "bash", "-c",
                    f"echo '🐴 stall: {name} — watching agent activity'; "
                    f"echo '   log: {log_path}'; echo ''; "
                    f"tail -f {log_path}",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            pid = proc.pid
            logger.info("Started stall '%s' on port %d (slot %d, pid %d)", name, port, slot, pid)
        except FileNotFoundError:
            raise RuntimeError(
                "ttyd not found. Install it: apt install ttyd (or see https://github.com/tsl0922/ttyd)"
            )

        stall = Stall(name=name, port=port, slot=slot, pid=pid, log_path=log_path)
        self._stalls[name] = stall
        return stall

    def destroy(self, name: str) -> bool:
        """Destroy a stall, killing its ttyd process.

        Returns:
            True if the stall was destroyed, False if not found.
        """
        stall = self._stalls.pop(name, None)
        if stall is None:
            return False

        if stall.pid and stall.alive:
            try:
                os.kill(stall.pid, signal.SIGTERM)
                logger.info("Killed stall '%s' (pid %d)", name, stall.pid)
            except (OSError, ProcessLookupError):
                pass
        return True

    def get(self, name: str) -> Optional[Stall]:
        """Get a stall by name."""
        return self._stalls.get(name)

    def get_log(self, name: str, lines: int = 200) -> str:
        """Read the activity log for a stall.

        Returns the last N lines of the log file.
        """
        log_path = self._log_dir / f".sdale-{name}.log"
        if not log_path.exists():
            return ""
        text = log_path.read_text(errors="replace")
        log_lines = text.splitlines()
        return "\n".join(log_lines[-lines:])

    def destroy_all(self) -> None:
        """Destroy all stalls. Called on server shutdown."""
        for name in list(self._stalls):
            self.destroy(name)
