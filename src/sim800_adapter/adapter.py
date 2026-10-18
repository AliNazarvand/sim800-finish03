"""Compatibility adapter for TinyGSM-like modem operations."""

from __future__ import annotations

from typing import Any

from sim800_driver import Sim800Driver


class TinyGSMAdapter:
    """Small, Pythonic facade over the low-level driver."""

    def __init__(self, driver: Sim800Driver) -> None:
        self.driver = driver

    def init(self) -> bool:
        """Initialize modem and return readiness."""
        return self.driver.check_ready()

    def get_signal_quality(self) -> int | None:
        """Return RSSI from ``+CSQ`` or ``None`` if unavailable."""
        response = self.driver.signal_quality()
        for line in response.payload:
            if line.startswith("+CSQ:"):
                try:
                    return int(line.split(":", 1)[1].split(",", 1)[0].strip())
                except (ValueError, IndexError):
                    return None
        return None

    def send_sms(self, number: str, message: str) -> bool:
        """Send an SMS through the driver."""
        return self.driver.send_sms(number, message).ok

    def raw(self, command: str) -> dict[str, Any]:
        """Expose structured raw command output for diagnostics."""
        response = self.driver.command(command)
        return {"command": response.command, "ok": response.ok, "lines": list(response.lines), "error": response.error}
