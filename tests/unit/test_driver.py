import pytest

from sim800_adapter import TinyGSMAdapter
from sim800_driver import Sim800Driver


class FakeTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.writes = []
        self.timeouts = []

    def write(self, data):
        self.writes.append(data)

    def read_until(self, terminator, timeout):
        self.timeouts.append((terminator, timeout))
        return self.responses.pop(0)


class TimeoutTransport(FakeTransport):
    def read_until(self, terminator, timeout):
        self.timeouts.append((terminator, timeout))
        raise TimeoutError("transport read timed out")


def test_command_parses_ok():
    response = Sim800Driver(FakeTransport([b"\r\n+CSQ: 20,0\r\nOK\r\n"])).command("AT+CSQ")
    assert response.ok and response.payload == ("+CSQ: 20,0",)


def test_retry_then_success():
    transport = FakeTransport([b"ERROR\r\n", b"OK\r\n"])
    assert Sim800Driver(transport, retries=1).check_ready()
    assert len(transport.writes) == 2


def test_adapter_signal_quality():
    transport = FakeTransport([b"+CSQ: 17,99\r\nOK\r\n"])
    assert TinyGSMAdapter(Sim800Driver(transport)).get_signal_quality() == 17


def test_adapter_init_raw_and_sms():
    transport = FakeTransport([b"OK\r\n", b"OK\r\n", b"OK\r\n", b"OK\r\n"])
    adapter = TinyGSMAdapter(Sim800Driver(transport))
    assert adapter.init() and adapter.raw("AT")["ok"] and adapter.send_sms("+123", "hello")


def test_driver_rejects_empty_command():
    with pytest.raises(ValueError, match="must not be empty"):
        Sim800Driver(FakeTransport([])).command(" \t")


def test_driver_parses_cme_error():
    response = Sim800Driver(FakeTransport([b"+CME ERROR: 10\r\n"])).command("AT+X", retries=0)
    assert not response.ok and response.error == "+CME ERROR: 10"


def test_driver_parses_cms_error():
    response = Sim800Driver(FakeTransport([b"+CMS ERROR: 305\r\n"])).command("AT+CMGS", retries=0)
    assert not response.ok and response.error == "+CMS ERROR: 305"


def test_timeout_from_transport_is_propagated():
    with pytest.raises(TimeoutError, match="timed out"):
        Sim800Driver(TimeoutTransport([])).command("AT", retries=0, timeout=0.01)


def test_timeout_argument_reaches_transport():
    transport = FakeTransport([b"OK\r\n"])
    assert Sim800Driver(transport).command("AT", timeout=1.25).ok
    assert transport.timeouts == [(b"\r\n", 1.25)]


def test_incomplete_response_is_not_ok():
    response = Sim800Driver(FakeTransport([b"+CSR\r\n"])).command("AT+X", retries=0)
    assert not response.ok and response.lines == ("+CSR",) and response.payload == ("+CSR",)


def test_empty_response_is_not_ok():
    response = Sim800Driver(FakeTransport([b""])).command("AT", retries=0)
    assert not response.ok and response.lines == ()


def test_retry_exhaustion_returns_last_error():
    transport = FakeTransport([b"ERROR\r\n", b"ERROR\r\n", b"ERROR\r\n"])
    response = Sim800Driver(transport, retries=2).command("AT", retries=2)
    assert not response.ok and response.error == "ERROR" and response.attempts == 3


def test_zero_retries_makes_one_attempt():
    transport = FakeTransport([b"ERROR\r\n"])
    response = Sim800Driver(transport, retries=5).command("AT", retries=0)
    assert response.attempts == 1 and len(transport.writes) == 1


def test_command_is_stripped_before_write():
    transport = FakeTransport([b"OK\r\n"])
    Sim800Driver(transport).command("  AT+CSQ  ")
    assert transport.writes == [b"AT+CSQ\r"]


def test_send_sms_rejects_missing_inputs():
    driver = Sim800Driver(FakeTransport([]))
    with pytest.raises(ValueError):
        driver.send_sms("", "body")
    with pytest.raises(ValueError):
        driver.send_sms("+123", "")


def test_send_sms_stops_when_text_mode_fails():
    transport = FakeTransport([b"ERROR\r\n", b"ERROR\r\n", b"ERROR\r\n"])
    response = Sim800Driver(transport).send_sms("+123", "body")
    assert response.error == "ERROR" and len(transport.writes) == 3


def test_adapter_returns_none_for_malformed_signal():
    transport = FakeTransport([b"+CSQ: nope,99\r\nOK\r\n"])
    assert TinyGSMAdapter(Sim800Driver(transport)).get_signal_quality() is None
