"""Reliable SIM800 AT command transport and response handling."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Protocol


class Transport(Protocol):
    """Minimal byte transport required by :class:`Sim800Driver`."""

    def write(self, data: bytes) -> None: ...
    def read_until(self, terminator: bytes, timeout: float) -> bytes: ...


@dataclass(frozen=True)
class ATResponse:
    """Parsed modem response."""

    command: str
    lines: tuple[str, ...]
    ok: bool
    error: str | None = None
    attempts: int = 1

    @property
    def payload(self) -> tuple[str, ...]:
        """Return lines excluding terminal status lines."""
        return tuple(line for line in self.lines if line not in {"OK", "ERROR"} and not line.startswith("+CME ERROR"))


@dataclass
class Sim800Driver:
    """AT command driver independent of pyserial or a concrete board."""

    transport: Transport
    timeout: float = 5.0
    retries: int = 2
    command_terminator: bytes = b"\r\n"
    _last_response: ATResponse | None = field(default=None, init=False)

    def command(self, command: str, *, timeout: float | None = None, retries: int | None = None) -> ATResponse:
        """Send a command, retry transient failures, and parse the modem response."""
        clean = command.strip()
        if not clean:
            raise ValueError("command must not be empty")
        limit = self.retries if retries is None else max(0, retries)
        wait = self.timeout if timeout is None else timeout
        last: ATResponse | None = None
        for attempt in range(1, limit + 2):
            self.transport.write((clean + "\r").encode("ascii"))
            raw = self.transport.read_until(self.command_terminator, wait)
            response = self._parse(clean, raw, attempt)
            last = response
            if response.ok or attempt > limit:
                self._last_response = response
                return response
            time.sleep(min(0.05 * attempt, 0.25))
        assert last is not None
        return last

    @staticmethod
    def _parse(command: str, raw: bytes, attempt: int) -> ATResponse:
        """Parse line-oriented SIM800 output without discarding unknown URCs."""
        text = raw.decode("utf-8", errors="replace")
        lines = tuple(line.strip() for line in text.replace("\r", "\n").split("\n") if line.strip())
        error = next(
            (
                line
                for line in lines
                if line == "ERROR" or line.startswith("+CME ERROR") or line.startswith("+CMS ERROR")
            ),
            None,
        )
        return ATResponse(command, lines, error is None and "OK" in lines, error, attempt)

    def check_ready(self) -> bool:
        """Return whether the modem answers the basic attention command."""
        return self.command("AT").ok

    def signal_quality(self) -> ATResponse:
        """Read RSSI and BER using the standard query command."""
        return self.command("AT+CSQ")

    def send_sms(self, number: str, message: str) -> ATResponse:
        """Validate basic SMS inputs and issue a text-mode SMS sequence."""
        if not number.strip() or not message:
            raise ValueError("number and message are required")
        mode = self.command("AT+CMGF=1")
        if not mode.ok:
            return mode
        return self.command(f'AT+CMGS="{number}"{message}\x1a')
