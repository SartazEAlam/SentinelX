"""Process context enricher — looks up process info via psutil."""

import logging
from functools import lru_cache
from typing import Any

import psutil

logger = logging.getLogger(__name__)


class ProcessContextEnricher:
    """Provides process metadata for enriching events.

    Uses psutil to look up process name, command line, and username.
    Results are LRU-cached to avoid repeated system calls.
    """

    @staticmethod
    @lru_cache(maxsize=512)
    def get_process_info(pid: int) -> dict[str, Any]:
        """Get process metadata by PID.

        Returns a dict with keys: name, cmdline, username, create_time.
        Returns an empty dict if the process no longer exists.
        """
        try:
            proc = psutil.Process(pid)
            info: dict[str, Any] = {
                "name": proc.name(),
                "username": "",
                "create_time": proc.create_time(),
            }
            try:
                info["username"] = proc.username()
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass
            try:
                cmdline = proc.cmdline()
                info["cmdline"] = " ".join(cmdline[:5])  # Truncate for safety
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                info["cmdline"] = ""
            return info
        except (psutil.NoSuchProcess, psutil.AccessDenied) as exc:
            logger.debug("Cannot get process info for pid=%d: %s", pid, exc)
            return {}

    @staticmethod
    def get_current_pid_info() -> dict[str, Any]:
        """Get info about the current process."""
        import os

        return ProcessContextEnricher.get_process_info(os.getpid())
