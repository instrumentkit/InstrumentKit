#!/usr/bin/env python
"""
Provides support for the OWON SDS1104 oscilloscope family.
"""

# pylint: disable=too-many-lines

# IMPORTS #####################################################################


from dataclasses import dataclass
from enum import Enum
import json
import re
import struct
import time
from typing import Any

import usb.core
import usb.util

try:
    import libusb_package
except ImportError:  # pragma: no cover - optional runtime helper
    libusb_package = None

from instruments.abstract_instruments import Oscilloscope
from instruments.abstract_instruments.comm import USBCommunicator
from instruments.generic_scpi import SCPIInstrument
from instruments.optional_dep_finder import numpy
from instruments.units import ureg as u
from instruments.util_fns import ProxyList, assume_units

# HELPERS #####################################################################


_TIME_UNITS = {
    "ns": 1e-9,
    "us": 1e-6,
    "ms": 1e-3,
    "s": 1.0,
}

_VERTICAL_UNITS = {
    "mv": 1e-3,
    "v": 1.0,
    "kv": 1e3,
}

_MEASUREMENT_UNITS = {
    "uv": 1e-6,
    "mv": 1e-3,
    "v": 1.0,
    "kv": 1e3,
    "uvs": 1e-6,
    "mvs": 1e-3,
    "vs": 1.0,
    "ns": 1e-9,
    "us": 1e-6,
    "ms": 1e-3,
    "s": 1.0,
    "hz": 1.0,
    "khz": 1e3,
    "mhz": 1e6,
    "ghz": 1e9,
    "%": 1.0,
}

_TIMEBASE_TOKENS = {
    1.0e-9: "1.0ns",
    2.0e-9: "2.0ns",
    5.0e-9: "5.0ns",
    10e-9: "10ns",
    20e-9: "20ns",
    50e-9: "50ns",
    100e-9: "100ns",
    200e-9: "200ns",
    500e-9: "500ns",
    1e-6: "1us",
    2e-6: "2us",
    5e-6: "5us",
    10e-6: "10us",
    20e-6: "20us",
    50e-6: "50us",
    100e-6: "100us",
    200e-6: "200us",
    500e-6: "500us",
    1e-3: "1.0ms",
    2e-3: "2.0ms",
    5e-3: "5.0ms",
    10e-3: "10ms",
    20e-3: "20ms",
    50e-3: "50ms",
    100e-3: "100ms",
    200e-3: "200ms",
    500e-3: "500ms",
    1.0: "1.0s",
    2.0: "2.0s",
    5.0: "5.0s",
    10.0: "10s",
    20.0: "20s",
    50.0: "50s",
    100.0: "100s",
}

_VERTICAL_SCALE_TOKENS = {
    2e-3: "2mv",
    5e-3: "5mv",
    10e-3: "10mv",
    20e-3: "20mv",
    50e-3: "50mv",
    100e-3: "100mv",
    200e-3: "200mv",
    500e-3: "500mv",
    1.0: "1v",
    2.0: "2v",
    5.0: "5v",
    10.0: "10v",
}

_MEMORY_DEPTH_TOKENS = {
    1_000: "1K",
    5_000: "5K",
    10_000: "10K",
    100_000: "100K",
    1_000_000: "1M",
    10_000_000: "10M",
}

_MEASUREMENT_VALUE_RE = re.compile(
    r"(?P<value>[-+]?\d+(?:\.\d*)?(?:[eE][-+]?\d+)?)\s*(?P<unit>[A-Za-z%*]+)?\s*$"
)
_MEASUREMENT_KV_RE = re.compile(r'"(?P<key>[A-Za-z0-9]+)"\s*:\s*"(?P<value>[^"\r\n]*)"')
_MEASUREMENT_CHANNEL_BLOCK_RE = re.compile(
    r'"CH(?P<channel>\d+)"\s*:\s*\{(?P<body>.*?)\}(?=,\s*"CH\d+"\s*:|\s*\}\s*$)',
    re.DOTALL,
)


def _clean_reply(reply):
    """
    Normalizes a DOS1104 text reply.
    """
    text = reply.strip()
    if text.endswith("->"):
        text = text[:-2].rstrip()
    return text


def _strip_packet_prefix(payload, field_name):
    """
    Strips the four-byte SDS1104 binary packet prefix.
    """
    if len(payload) < 4:
        raise ValueError(f"{field_name} payload is too short.")
    return payload[4:]


def _parse_bool(reply, field_name):
    """
    Parses a boolean-like reply.
    """
    cleaned = _clean_reply(reply).upper()
    if cleaned in {"ON", "1"}:
        return True
    if cleaned in {"OFF", "0"}:
        return False
    raise ValueError(f"Invalid {field_name} reply: {reply!r}")


def _parse_float(reply, field_name):
    """
    Parses a float reply.
    """
    cleaned = _clean_reply(reply)
    try:
        return float(cleaned)
    except ValueError as exc:
        raise ValueError(f"Invalid {field_name} reply: {reply!r}") from exc


def _parse_quantity_token(token, units_map, field_name):
    """
    Parses a quantity token like ``100mV`` or ``1ms``.
    """
    cleaned = _clean_reply(token).strip().lower()
    for suffix, scale in units_map.items():
        if cleaned.endswith(suffix):
            magnitude = cleaned[: -len(suffix)]
            try:
                return float(magnitude) * scale
            except ValueError as exc:
                raise ValueError(f"Invalid {field_name} reply: {token!r}") from exc
    raise ValueError(f"Invalid {field_name} reply: {token!r}")


def _parse_timebase_token(token):
    """
    Parses a timebase token to seconds per division.
    """
    return _parse_quantity_token(token, _TIME_UNITS, "timebase")


def _parse_vertical_scale_token(token):
    """
    Parses a vertical scale token to volts per division.
    """
    return _parse_quantity_token(token, _VERTICAL_UNITS, "vertical scale")


def _parse_probe_token(token):
    """
    Parses a probe token such as ``10X`` or ``X10``.
    """
    cleaned = _clean_reply(token).upper()
    if cleaned.startswith("X"):
        cleaned = cleaned[1:]
    elif cleaned.endswith("X"):
        cleaned = cleaned[:-1]
    try:
        value = int(cleaned)
    except ValueError as exc:
        raise ValueError(f"Invalid probe reply: {token!r}") from exc
    if value not in {1, 10, 100, 1000}:
        raise ValueError(f"Invalid probe reply: {token!r}")
    return value


def _format_probe_token(value):
    """
    Formats a probe attenuation token.
    """
    if isinstance(value, str):
        value = _parse_probe_token(value)
    if value not in {1, 10, 100, 1000}:
        raise ValueError("Probe attenuation must be one of 1, 10, 100, or 1000.")
    return f"{value}X"


def _parse_memory_depth_token(token):
    """
    Parses a memory depth token.
    """
    cleaned = _clean_reply(token).upper()
    if cleaned.endswith("K"):
        return int(float(cleaned[:-1]) * 1000)
    if cleaned.endswith("M"):
        return int(float(cleaned[:-1]) * 1_000_000)
    return int(cleaned)


def _parse_measurement_token(token, field_name):
    """
    Parses a scalar measurement token.
    """
    cleaned = _clean_reply(token).strip()
    if not cleaned or cleaned == "?":
        raise ValueError(f"Invalid {field_name} reply: {token!r}")

    match = _MEASUREMENT_VALUE_RE.search(cleaned)
    if match is None:
        raise ValueError(f"Invalid {field_name} reply: {token!r}")

    value = float(match.group("value"))
    unit = (match.group("unit") or "").replace("*", "").lower()
    if not unit:
        return value
    if unit not in _MEASUREMENT_UNITS:
        raise ValueError(f"Invalid {field_name} reply: {token!r}")
    return value * _MEASUREMENT_UNITS[unit]


def _parse_measurement_count(token, field_name):
    """
    Parses a count-like measurement reply.
    """
    return int(round(_parse_measurement_token(token, field_name)))


def _parse_json_payload(payload, field_name):
    """
    Parses an SDS1104 binary JSON payload.
    """
    text = _strip_packet_prefix(payload, field_name).decode("utf-8", errors="replace")
    try:
        parsed = json.loads(text.strip())
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid {field_name} payload: {text!r}") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"Invalid {field_name} payload: {text!r}")
    return parsed


def _sanitize_json_text(text):
    """
    Replaces control characters with spaces before JSON parsing.
    """
    return "".join(character if ord(character) >= 0x20 else " " for character in text)


def _parse_json_array_payload(payload, field_name):
    """
    Parses a length-prefixed JSON array payload.
    """
    text = _strip_packet_prefix(payload, field_name).decode("utf-8", errors="replace")
    text = _sanitize_json_text(text).strip()
    if text == "[?]":
        return []
    text = re.sub(r",\s*}", "}", text)
    text = re.sub(r",\s*]", "]", text)
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid {field_name} payload: {text!r}") from exc
    if not isinstance(parsed, list):
        raise ValueError(f"Invalid {field_name} payload: {text!r}")
    for item in parsed:
        if not isinstance(item, dict):
            raise ValueError(f"Invalid {field_name} entry: {item!r}")
    return parsed


def _parse_measurement_payload(payload, channel):
    """
    Parses a single-channel measurement blob payload.
    """
    text = _strip_packet_prefix(payload, "measurement data").decode(
        "utf-8", errors="replace"
    )
    text = _sanitize_json_text(text).strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        pairs = {
            match.group("key"): match.group("value")
            for match in _MEASUREMENT_KV_RE.finditer(text)
            if match.group("key") != f"CH{channel}"
        }
        if not pairs:
            raise ValueError(
                f"Invalid CH{channel} measurement data payload: {text!r}"
            ) from exc
        return pairs

    nested = parsed.get(f"CH{channel}")
    if isinstance(nested, dict):
        return {
            str(key): "" if value is None else str(value)
            for key, value in nested.items()
        }
    if not isinstance(parsed, dict):
        raise ValueError(f"Invalid CH{channel} measurement data payload: {text!r}")
    return {
        str(key): "" if value is None else str(value) for key, value in parsed.items()
    }


def _parse_measurement_map_payload(payload):
    """
    Parses an all-channel measurement blob payload.
    """
    text = _strip_packet_prefix(payload, "all-channel measurement data").decode(
        "utf-8", errors="replace"
    )
    text = _sanitize_json_text(text).strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        channel_map = {}
        for match in _MEASUREMENT_CHANNEL_BLOCK_RE.finditer(text):
            channel = int(match.group("channel"))
            channel_map[channel] = {
                kv_match.group("key"): kv_match.group("value")
                for kv_match in _MEASUREMENT_KV_RE.finditer(match.group("body"))
            }
        if not channel_map:
            raise ValueError(
                f"Invalid all-channel measurement payload: {text!r}"
            ) from exc
        return channel_map

    channel_map = {}
    if not isinstance(parsed, dict):
        raise ValueError(f"Invalid all-channel measurement payload: {text!r}")
    for key, value in parsed.items():
        if (
            not isinstance(key, str)
            or not key.startswith("CH")
            or not isinstance(value, dict)
        ):
            continue
        try:
            channel = int(key[2:])
        except ValueError:
            continue
        channel_map[channel] = {
            str(item_key): "" if item_value is None else str(item_value)
            for item_key, item_value in value.items()
        }
    if not channel_map:
        raise ValueError(f"Invalid all-channel measurement payload: {text!r}")
    return channel_map


def _parse_sample_rate(token):
    """
    Parses a sample rate token such as ``1MS/s``.
    """
    cleaned = _clean_reply(token).strip().lower()
    units = {
        "ks/s": 1e3,
        "ms/s": 1e6,
        "gs/s": 1e9,
    }
    for suffix, scale in units.items():
        if cleaned.endswith(suffix):
            magnitude = cleaned[: -len(suffix)]
            try:
                return float(magnitude) * scale
            except ValueError as exc:
                raise ValueError(f"Invalid sample rate reply: {token!r}") from exc
    raise ValueError(f"Invalid sample rate reply: {token!r}")


def _parse_waveform_adc(raw_bytes, field_name):
    """
    Parses little-endian signed 16-bit ADC samples.
    """
    if len(raw_bytes) % 2 != 0:
        raise ValueError(
            f"{field_name} payload length is not 16-bit aligned: {len(raw_bytes)}"
        )
    if numpy is not None:
        return numpy.frombuffer(raw_bytes, dtype="<i2").copy()
    return struct.unpack(f"<{len(raw_bytes) // 2}h", raw_bytes)


def _format_discrete_quantity(value, units, token_map, field_name):
    """
    Formats a discrete quantity token for a command.
    """
    if isinstance(value, str):
        value = assume_units(value, units)
    value = assume_units(value, units).to(units).magnitude
    for magnitude, token in token_map.items():
        if abs(value - magnitude) <= max(abs(magnitude) * 1e-9, 1e-15):
            return token
    raise ValueError(
        f"Unsupported {field_name}. Must be one of the documented discrete values."
    )


class _OWONPromptUSBCommunicator(USBCommunicator):  # pylint: disable=abstract-method
    """
    USB communicator for OWON-family prompt-style raw USB replies.

    The SDS1104 USB path does not use newline-terminated SCPI replies.
    Commands are written as raw ASCII without an appended terminator, and text
    replies are packet-delimited with a trailing ``->`` prompt.
    """

    def __init__(self, dev):
        super().__init__(dev)
        self._terminator = ""

    def _sendcmd(self, msg):
        self.write(msg, encoding="ascii")

    def _query(self, msg, size=-1):
        self._sendcmd(msg)
        return self.read(size, encoding="utf-8")

    def close(self):
        """
        Close the communicator without forcing a USB device reset.

        Resetting the OWON scope on every close can trigger a full device
        re-enumeration on Windows and is unnecessarily disruptive during probe
        attempts that fail partway through initialization.
        """
        usb.util.dispose_resources(self._dev)


@dataclass(frozen=True)
class SDS1104DeepMemoryCapture:
    """
    Parsed deep-memory bundle returned by ``:DATA:WAVE:DEPMem:All?``.
    """

    metadata: dict[str, Any]
    raw_channels: dict[int, Any]


@dataclass(frozen=True)
class SDS1104SavedWaveformEntry:
    """
    Saved-waveform index entry returned by ``:SAVE:READ:HEAD?``.
    """

    index: str
    raw: dict[str, Any]


class OWONSDS1104(
    SCPIInstrument, Oscilloscope
):  # pylint: disable=too-many-public-methods
    """
    Conservative driver for the OWON SDS1104 oscilloscope family.

    This driver targets the text-based raw-USB control surface shared by the
    OWON SDS1104 and compatible HANMATEK DOS1104 units. The public API covers
    stable control, scalar measurements, measurement blobs, screen-waveform
    retrieval, BMP capture, deep-memory capture, and saved-waveform access.

    Example usage:

    >>> import instruments as ik
    >>> scope = ik.owon.OWONSDS1104.open_usb()
    >>> scope.name
    'OWON,SDS1104,...'
    >>> scope.channel[0].display
    True
    """

    DEFAULT_USB_VID = 0x5345
    DEFAULT_USB_PID = 0x1234

    class AcquisitionMode(Enum):
        """
        Acquisition modes supported by the SDS1104 family.
        """

        # pylint: disable=invalid-name

        sample = "SAMPle"
        average = "AVERage"
        peak_detect = "PEAK"

    class Coupling(Enum):
        """
        Input coupling modes for SDS1104 channels.
        """

        # pylint: disable=invalid-name

        ac = "AC"
        dc = "DC"
        ground = "GND"

    class TriggerStatus(Enum):
        """
        Acquisition / trigger status values reported by ``:TRIGger:STATUS?``.
        """

        # pylint: disable=invalid-name

        auto = "AUTO"
        ready = "READY"
        trig = "TRIG"
        scan = "SCAN"
        stop = "STOP"

    class TriggerMode(Enum):
        """
        General trigger modes supported by the verified SDS1104 API surface.
        """

        # pylint: disable=invalid-name

        edge = "EDGE"
        video = "VIDEO"

    class TriggerSource(Enum):
        """
        Edge-trigger sources.
        """

        # pylint: disable=invalid-name

        ch1 = "CH1"
        ch2 = "CH2"
        ch3 = "CH3"
        ch4 = "CH4"

    class TriggerCoupling(Enum):
        """
        Edge-trigger coupling modes verified on hardware.
        """

        # pylint: disable=invalid-name

        ac = "AC"
        dc = "DC"

    class TriggerSlope(Enum):
        """
        Edge-trigger slope modes verified on hardware.
        """

        # pylint: disable=invalid-name

        rise = "RISE"
        fall = "FALL"

    class DataSource(Oscilloscope.DataSource):
        """
        Represents a non-waveform SDS1104 data source.

        Only physical channels support waveform transfer in the initial
        driver.
        """

        @property
        def name(self):
            return self._name

        def read_waveform(self, bin_format=True):  # pylint: disable=unused-argument
            raise NotImplementedError(
                "Waveform transfer is only supported for physical SDS1104 channels."
            )

    class Channel(DataSource, Oscilloscope.Channel):
        """
        Class representing a physical channel on the SDS1104.
        """

        def __init__(self, parent, idx):
            self._parent = parent
            self._idx = idx + 1
            super().__init__(parent, f"CH{self._idx}")

        def sendcmd(self, cmd):
            """
            Sends a channel-scoped command.
            """
            self._parent.sendcmd(f":CH{self._idx}:{cmd}")

        def query(self, cmd):
            """
            Queries a channel-scoped command.
            """
            return self._parent.query(f":CH{self._idx}:{cmd}")

        @property
        def display(self):
            """
            Gets/sets whether the channel is displayed.

            :type: `bool`
            """
            return _parse_bool(self.query("DISP?"), "channel display state")

        @display.setter
        def display(self, newval):
            if not isinstance(newval, bool):
                raise TypeError("Display state must be specified with a boolean value.")
            self.sendcmd(f"DISP {'ON' if newval else 'OFF'}")

        @property
        def coupling(self):
            """
            Gets/sets the channel coupling mode.

            :type: `OWONSDS1104.Coupling`
            """
            return OWONSDS1104.Coupling(_clean_reply(self.query("COUP?")).upper())

        @coupling.setter
        def coupling(self, newval):
            if not isinstance(newval, OWONSDS1104.Coupling):
                raise TypeError(
                    "Coupling setting must be a `OWONSDS1104.Coupling` value."
                )
            self.sendcmd(f"COUP {newval.value}")

        @property
        def probe_attenuation(self):
            """
            Gets/sets the configured probe attenuation.

            :type: `int`
            """
            return _parse_probe_token(self.query("PROB?"))

        @probe_attenuation.setter
        def probe_attenuation(self, newval):
            self.sendcmd(f"PROB {_format_probe_token(newval)}")

        @property
        def scale(self):
            """
            Gets/sets the vertical scale in volts per division.

            :type: `~pint.Quantity`
            """
            return u.Quantity(_parse_vertical_scale_token(self.query("SCAL?")), u.volt)

        @scale.setter
        def scale(self, newval):
            token = _format_discrete_quantity(
                newval, u.volt, _VERTICAL_SCALE_TOKENS, "vertical scale"
            )
            self.sendcmd(f"SCAL {token}")

        @property
        def offset(self):
            """
            Gets/sets the vertical offset in volts.

            :type: `~pint.Quantity`
            """
            return u.Quantity(_parse_float(self.query("OFFS?"), "offset"), u.volt)

        @offset.setter
        def offset(self, newval):
            newval = assume_units(newval, u.volt).to(u.volt)
            self.sendcmd(f"OFFS {newval.magnitude}")

        @property
        def position(self):
            """
            Gets/sets the vertical channel position in divisions.

            :type: `float`
            """
            return _parse_float(self.query("POS?"), "position")

        @position.setter
        def position(self, newval):
            self.sendcmd(f"POS {float(newval)}")

        @property
        def invert(self):
            """
            Gets/sets whether the channel waveform is inverted.

            :type: `bool`
            """
            return _parse_bool(self.query("INVErse?"), "channel invert state")

        @invert.setter
        def invert(self, newval):
            if not isinstance(newval, bool):
                raise TypeError("Invert state must be specified with a boolean value.")
            self.sendcmd(f"INVErse {'ON' if newval else 'OFF'}")

        def measure_frequency(self):
            """
            Measures the channel frequency.

            :rtype: `~pint.Quantity`
            """
            return self._parent.measure_frequency(self._idx)

        def measure_period(self):
            """
            Measures the channel period.

            :rtype: `~pint.Quantity`
            """
            return self._parent.measure_period(self._idx)

        def measure_peak_to_peak(self):
            """
            Measures the channel peak-to-peak voltage.

            :rtype: `~pint.Quantity`
            """
            return self._parent.measure_peak_to_peak(self._idx)

        def measure_rms(self):
            """
            Measures the channel cycle RMS voltage.

            :rtype: `~pint.Quantity`
            """
            return self._parent.measure_rms(self._idx)

        def measure_average(self):
            """
            Measures the channel average voltage.
            """
            return self._parent.measure_average(self._idx)

        def measure_maximum(self):
            """
            Measures the channel maximum voltage.
            """
            return self._parent.measure_maximum(self._idx)

        def measure_minimum(self):
            """
            Measures the channel minimum voltage.
            """
            return self._parent.measure_minimum(self._idx)

        def read_measurement_data(self, long_form=False):
            """
            Reads the measurement blob for this channel.
            """
            return self._parent.read_measurement_data(self._idx, long_form=long_form)

        def read_waveform(self, bin_format=True):
            """
            Reads the current screen waveform for this channel.
            """
            if not bin_format:
                raise NotImplementedError(
                    "The OWON SDS1104 driver currently supports binary "
                    "waveform transfer only."
                )
            return self._parent.read_waveform(self._idx)

        def read_deep_memory(self):
            """
            Reads the deep-memory waveform for this channel.
            """
            return self._parent.read_deep_memory_channel(self._idx)

    def __init__(self, filelike):
        super().__init__(filelike)
        self._file.timeout = 1 * u.second

    def close(self):
        """
        Closes the underlying transport if it exposes a close method.
        """
        close_method = getattr(self._file, "close", None)
        if callable(close_method):
            close_method()

    @classmethod
    def open_usb(
        cls,
        vid=DEFAULT_USB_VID,
        pid=DEFAULT_USB_PID,
        timeout=1 * u.second,
        enable_scpi=True,
        ignore_scpi_failure=True,
        settle_time=0.25,
    ):
        """
        Opens an SDS1104-family scope using the default raw USB VID/PID.

        A best-effort OWON-family SCPI enable handshake is attempted after the
        communicator is opened.
        """
        backend = None
        if libusb_package is not None:
            try:
                backend = libusb_package.get_libusb1_backend()
            except Exception:
                backend = None

        dev = usb.core.find(idVendor=vid, idProduct=pid, backend=backend)
        if dev is None:
            raise OSError("No such device found.")

        inst = cls(_OWONPromptUSBCommunicator(dev))
        inst.timeout = assume_units(timeout, u.second)
        inst._file.flush_input()
        time.sleep(0.1)
        if enable_scpi:
            ok = inst.ensure_scpi_mode(
                strict=not ignore_scpi_failure, settle_time=settle_time
            )
            if not ok and not ignore_scpi_failure:
                inst.close()
                raise OSError("OWON SDS1104 SCPI enable handshake failed.")
        return inst

    def ensure_scpi_mode(self, strict=False, settle_time=0.25):
        """
        Best-effort OWON-family SCPI enable handshake.
        """
        original_timeout = self.timeout
        try:
            self._file.flush_input()
            self._file.write_raw(b":SDSLSCPI#")
            time.sleep(max(float(settle_time), 0.0))
            self.timeout = 0.5 * u.second
            reply = self._file.read()
            self._file.flush_input()
            return ":SCPION" in _clean_reply(reply)
        except (usb.core.USBTimeoutError, usb.core.USBError, OSError):
            if strict:
                raise
            return False
        finally:
            self.timeout = original_timeout

    def _enable_scpi_mode(self, settle_time=0.25):
        """
        Backward-compatible alias for the public SCPI-mode helper.
        """
        return self.ensure_scpi_mode(strict=False, settle_time=settle_time)

    def _binary_query(self, command):
        """
        Sends a raw USB command and reads a binary reply.
        """
        self._file.write_raw(command.encode("ascii"))
        if not hasattr(self._file, "read_binary"):
            raise NotImplementedError(
                "Binary waveform support requires a communicator that "
                "implements read_binary()."
            )
        return self._file.read_binary()

    def _binary_query_exact(self, command, size):
        """
        Sends a raw USB command and reads an exact-size binary reply.
        """
        self._file.write_raw(command.encode("ascii"))
        if not hasattr(self._file, "read_exact"):
            raise NotImplementedError(
                "Binary waveform support requires a communicator that "
                "implements read_exact()."
            )
        return self._file.read_exact(size)

    def _query_length_prefixed_binary(self, command, max_body_size=20_000_000):
        """
        Sends a raw USB command and reads a little-endian length-prefixed body.
        """
        self._file.write_raw(command.encode("ascii"))
        if not hasattr(self._file, "read_exact"):
            raise NotImplementedError(
                "Length-prefixed binary support requires a communicator that "
                "implements read_exact()."
            )

        header = self._file.read_exact(4)
        if len(header) < 4:
            raise ValueError(f"Length-prefixed reply too short for {command!r}.")

        body_size = int.from_bytes(header, byteorder="little", signed=False)
        if body_size <= 0:
            raise ValueError(
                f"Invalid length-prefixed body size for {command!r}: {body_size}"
            )
        if body_size > max_body_size:
            raise ValueError(
                f"Length-prefixed body for {command!r} exceeds safety limit: "
                f"{body_size}"
            )
        return header + self._file.read_exact(body_size)

    def _waveform_metadata(self):
        """
        Reads the screen-waveform metadata block.
        """
        return _parse_json_payload(
            self._binary_query(":DATA:WAVE:SCREen:HEAD?"), "waveform metadata"
        )

    def read_waveform_metadata(self):
        """
        Reads the screen-waveform metadata JSON.

        :rtype: `dict`
        """
        return self._waveform_metadata()

    def _extract_channel_metadata(self, metadata, channel):
        channels = metadata.get("CHANNEL")
        if not isinstance(channels, list) or channel - 1 >= len(channels):
            raise ValueError(
                f"Metadata does not contain channel {channel}: {metadata!r}"
            )
        channel_metadata = channels[channel - 1]
        if not isinstance(channel_metadata, dict):
            raise ValueError(
                f"Invalid channel metadata for CH{channel}: {channel_metadata!r}"
            )
        return channel_metadata

    def _sample_rate_hz(self, metadata):
        sample = metadata.get("SAMPLE")
        if not isinstance(sample, dict):
            raise ValueError(f"Metadata missing SAMPLE block: {metadata!r}")
        return _parse_sample_rate(str(sample["SAMPLERATE"]))

    def _waveform_point_count(self, metadata):
        sample = metadata.get("SAMPLE")
        if not isinstance(sample, dict):
            raise ValueError(f"Metadata missing SAMPLE block: {metadata!r}")
        return int(sample["DATALEN"])

    def _horizontal_offset_pixels(self, metadata):
        timebase = metadata.get("TIMEBASE")
        if not isinstance(timebase, dict):
            raise ValueError(f"Metadata missing TIMEBASE block: {metadata!r}")
        return int(timebase["HOFFSET"])

    def _vertical_scale_v_div(self, metadata, channel):
        channel_metadata = self._extract_channel_metadata(metadata, channel)
        return _parse_vertical_scale_token(str(channel_metadata["SCALE"]))

    def _vertical_offset_pixels(self, metadata, channel):
        channel_metadata = self._extract_channel_metadata(metadata, channel)
        return int(channel_metadata["OFFSET"])

    def _probe_attenuation(self, metadata, channel):
        channel_metadata = self._extract_channel_metadata(metadata, channel)
        return _parse_probe_token(str(channel_metadata["PROBE"]))

    def _waveform_time_axis(self, metadata, point_count):
        sample_rate = self._sample_rate_hz(metadata)
        sample_time = 5.0 / sample_rate
        horizontal_offset = self._horizontal_offset_pixels(metadata)
        time_offset = -1.0 * horizontal_offset * 2.0 * sample_time
        if numpy is not None:
            indices = numpy.arange(point_count, dtype=float)
            return (indices - point_count / 2.0) * sample_time - time_offset
        return tuple(
            (index - point_count / 2.0) * sample_time - time_offset
            for index in range(point_count)
        )

    def _waveform_voltage_axis(self, metadata, channel, raw_adc):
        vertical_offset = self._vertical_offset_pixels(metadata, channel)
        volts_per_div = self._vertical_scale_v_div(metadata, channel)
        probe = self._probe_attenuation(metadata, channel)
        if numpy is not None and isinstance(raw_adc, numpy.ndarray):
            return (
                volts_per_div
                * probe
                * (raw_adc.astype(float) - vertical_offset * 8.25)
                / 410.0
            )
        return tuple(
            volts_per_div * probe * (sample - vertical_offset * 8.25) / 410.0
            for sample in raw_adc
        )

    @property
    def name(self):
        """
        The cleaned instrument identity string reported by ``*IDN?``.
        """
        return _clean_reply(super().name)

    @property
    def channel(self):
        """
        Gets the SDS1104 channel proxy list.
        """
        return ProxyList(self, self.Channel, range(4))

    @property
    def ref(self):
        """
        Gets reference data-source objects.
        """
        return ProxyList(
            self, lambda scope, idx: self.DataSource(scope, f"REF{idx + 1}"), range(4)
        )

    @property
    def math(self):
        """
        Gets the math data-source object.
        """
        return self.DataSource(self, "MATH")

    @property
    def acquire_mode(self):
        """
        Gets/sets the acquisition mode.

        :type: `OWONSDS1104.AcquisitionMode`
        """
        reply = _clean_reply(self.query(":ACQUire:Mode?")).upper()
        if reply.startswith("SAMP"):
            return self.AcquisitionMode.sample
        if reply.startswith("AVER"):
            return self.AcquisitionMode.average
        if reply.startswith("PEAK"):
            return self.AcquisitionMode.peak_detect
        raise ValueError(f"Invalid acquisition mode reply: {reply!r}")

    @acquire_mode.setter
    def acquire_mode(self, newval):
        if not isinstance(newval, self.AcquisitionMode):
            raise TypeError(
                'Acquisition mode must be one of "SAMPle", "AVERage", or "PEAK".'
            )
        self.sendcmd(f":ACQUire:Mode {newval.value}")

    @property
    def acquire_averages(self):
        """
        Gets/sets the acquisition average count.

        :type: `int`
        """
        return int(_clean_reply(self.query(":ACQUire:average:num?")))

    @acquire_averages.setter
    def acquire_averages(self, newval):
        if newval not in {4, 16, 64, 128}:
            raise ValueError(
                "Average count not supported by instrument; must be one of "
                "{4, 16, 64, 128}."
            )
        self.sendcmd(f":ACQUire:average:num {int(newval)}")

    @property
    def memory_depth(self):
        """
        Gets/sets the acquisition memory depth.

        :type: `int`
        """
        return _parse_memory_depth_token(self.query(":ACQUIRE:DEPMEM?"))

    @memory_depth.setter
    def memory_depth(self, newval):
        if newval not in _MEMORY_DEPTH_TOKENS:
            raise ValueError(
                "Memory depth must be one of 1K, 5K, 10K, 100K, 1M, or 10M. "
                "20M and 40M are documented, but are not yet verified in this driver."
            )
        self.sendcmd(f":ACQUIRE:DEPMEM {_MEMORY_DEPTH_TOKENS[int(newval)]}")

    @property
    def timebase_scale(self):
        """
        Gets/sets the horizontal scale in seconds per division.

        :type: `~pint.Quantity`
        """
        seconds = _parse_timebase_token(self.query(":HORIzontal:Scale?"))
        return u.Quantity(seconds, u.second)

    @timebase_scale.setter
    def timebase_scale(self, newval):
        token = _format_discrete_quantity(
            newval, u.second, _TIMEBASE_TOKENS, "timebase scale"
        )
        self.sendcmd(f":HORIzontal:Scale {token}")

    @property
    def trigger_status(self):
        """
        Gets the current trigger / acquisition status.

        :type: `OWONSDS1104.TriggerStatus`
        """
        reply = _clean_reply(self.query(":TRIGger:STATUS?")).upper()
        try:
            return self.TriggerStatus(reply)
        except ValueError as exc:
            raise ValueError(f"Invalid trigger status reply: {reply!r}") from exc

    @property
    def trigger_mode(self):
        """
        Gets/sets the current trigger mode.

        :type: `OWONSDS1104.TriggerMode`
        """
        reply = _clean_reply(self.query(":TRIGger:SINGle:MODE?")).upper()
        try:
            return self.TriggerMode(reply)
        except ValueError as exc:
            raise ValueError(f"Invalid trigger mode reply: {reply!r}") from exc

    @trigger_mode.setter
    def trigger_mode(self, newval):
        if not isinstance(newval, self.TriggerMode):
            raise TypeError(
                "Trigger mode must be specified with a "
                "`OWONSDS1104.TriggerMode` value."
            )
        self.sendcmd(f":TRIGger:SINGle:MODE {newval.value}")

    def _require_edge_trigger_mode(self):
        mode = self.trigger_mode
        if mode != self.TriggerMode.edge:
            raise NotImplementedError(
                "Trigger source, coupling, slope, and level are only exposed "
                "for EDGE trigger mode in this driver."
            )

    @property
    def trigger_source(self):
        """
        Gets/sets the edge-trigger source.

        This property is only available when ``trigger_mode`` is ``EDGE``.

        :type: `OWONSDS1104.TriggerSource`
        """
        self._require_edge_trigger_mode()
        reply = _clean_reply(self.query(":TRIGger:SINGle:EDGE:SOURce?")).upper()
        try:
            return self.TriggerSource(reply)
        except ValueError as exc:
            raise ValueError(f"Invalid trigger source reply: {reply!r}") from exc

    @trigger_source.setter
    def trigger_source(self, newval):
        self._require_edge_trigger_mode()
        if not isinstance(newval, self.TriggerSource):
            raise TypeError(
                "Trigger source must be specified with a "
                "`OWONSDS1104.TriggerSource` value."
            )
        self.sendcmd(f":TRIGger:SINGle:EDGE:SOURce {newval.value}")

    @property
    def trigger_coupling(self):
        """
        Gets/sets the edge-trigger coupling.

        This property is only available when ``trigger_mode`` is ``EDGE``.

        :type: `OWONSDS1104.TriggerCoupling`
        """
        self._require_edge_trigger_mode()
        reply = _clean_reply(self.query(":TRIGger:SINGle:EDGE:COUPling?")).upper()
        try:
            return self.TriggerCoupling(reply)
        except ValueError as exc:
            raise ValueError(f"Invalid trigger coupling reply: {reply!r}") from exc

    @trigger_coupling.setter
    def trigger_coupling(self, newval):
        self._require_edge_trigger_mode()
        if not isinstance(newval, self.TriggerCoupling):
            raise TypeError(
                "Trigger coupling must be specified with a "
                "`OWONSDS1104.TriggerCoupling` value."
            )
        self.sendcmd(f":TRIGger:SINGle:EDGE:COUPling {newval.value}")

    @property
    def trigger_slope(self):
        """
        Gets/sets the edge-trigger slope.

        This property is only available when ``trigger_mode`` is ``EDGE``.

        :type: `OWONSDS1104.TriggerSlope`
        """
        self._require_edge_trigger_mode()
        reply = _clean_reply(self.query(":TRIGger:SINGle:EDGE:SLOPe?")).upper()
        try:
            return self.TriggerSlope(reply)
        except ValueError as exc:
            raise ValueError(f"Invalid trigger slope reply: {reply!r}") from exc

    @trigger_slope.setter
    def trigger_slope(self, newval):
        self._require_edge_trigger_mode()
        if not isinstance(newval, self.TriggerSlope):
            raise TypeError(
                "Trigger slope must be specified with a "
                "`OWONSDS1104.TriggerSlope` value."
            )
        self.sendcmd(f":TRIGger:SINGle:EDGE:SLOPe {newval.value}")

    @property
    def trigger_level(self):
        """
        Gets/sets the edge-trigger level.

        This property is only available when ``trigger_mode`` is ``EDGE``.

        :type: `~pint.Quantity`
        """
        self._require_edge_trigger_mode()
        value = _parse_measurement_token(
            self.query(":TRIGger:SINGle:EDGE:LEVel?"), "trigger level"
        )
        return u.Quantity(value, u.volt)

    @trigger_level.setter
    def trigger_level(self, newval):
        self._require_edge_trigger_mode()
        newval = assume_units(newval, u.volt).to(u.volt)
        self.sendcmd(f":TRIGger:SINGle:EDGE:LEVel {newval.magnitude}V")

    @property
    def horizontal_offset(self):
        """
        Gets/sets the horizontal offset in the instrument's division units.

        :type: `float`
        """
        return _parse_float(self.query(":HORIzontal:OFFSET?"), "horizontal offset")

    @horizontal_offset.setter
    def horizontal_offset(self, newval):
        self.sendcmd(f":HORIzontal:OFFSET {float(newval)}")

    @property
    def measurement_display_enabled(self):
        """
        Gets/sets whether the on-screen measurement table is displayed.

        :type: `bool`
        """
        return _parse_bool(
            self.query(":MEASUrement:DISPlay?"), "measurement display state"
        )

    @measurement_display_enabled.setter
    def measurement_display_enabled(self, newval):
        if not isinstance(newval, bool):
            raise TypeError(
                "Measurement display state must be specified with a boolean value."
            )
        self.sendcmd(f":MEASUrement:DISPlay {'ON' if newval else 'OFF'}")

    def run(self):
        """
        Starts acquisition.
        """
        self.sendcmd(":RUN")

    def stop(self):
        """
        Stops acquisition.
        """
        self.sendcmd(":STOP")

    def autoscale(self):
        """
        Executes the scope autoscale action.

        This is an action-like command, not a persistent boolean setting. It
        may reconfigure acquisition, timebase, and channel settings.
        """
        self.sendcmd(":AUTOscale ON")

    def read_waveform(self, channel):
        """
        Reads the current screen waveform for a channel.

        :param int channel: One-based channel number from 1 to 4.
        :rtype: `tuple`
        :return: Pair ``(x, y)`` of time and voltage samples.
        """
        self._validate_channel(channel)
        metadata = self._waveform_metadata()
        point_count = self._waveform_point_count(metadata)
        payload = self._binary_query_exact(
            f":DATA:WAVE:SCREEN:CH{channel}?", 4 + 2 * point_count
        )
        raw_adc = _parse_waveform_adc(
            _strip_packet_prefix(payload, f"screen waveform CH{channel}"),
            f"screen waveform CH{channel}",
        )
        if len(raw_adc) != point_count:
            raise ValueError(
                f"Screen waveform point count mismatch for CH{channel}: "
                f"metadata={point_count}, payload={len(raw_adc)}"
            )
        return (
            self._waveform_time_axis(metadata, point_count),
            self._waveform_voltage_axis(metadata, channel, raw_adc),
        )

    def force_trigger(self):
        raise NotImplementedError(
            "The initial OWON SDS1104 driver does not expose trigger control."
        )

    def _validate_channel(self, channel):
        if channel not in {1, 2, 3, 4}:
            raise ValueError("Channel index must be between 1 and 4.")

    def _measure(self, channel, item, field_name, units):
        self._validate_channel(channel)
        token = self.query(f":MEASUrement:CH{channel}:{item}?")
        value = _parse_measurement_token(token, field_name)
        return u.Quantity(value, units)

    def _measure_short(self, channel, item, field_name, units):
        self._validate_channel(channel)
        token = self.query(f":MEAS:CH{channel}:{item}?")
        value = _parse_measurement_token(token, field_name)
        return u.Quantity(value, units)

    def _measure_short_count(self, channel, item, field_name):
        self._validate_channel(channel)
        token = self.query(f":MEAS:CH{channel}:{item}?")
        return _parse_measurement_count(token, field_name)

    def read_measurement_data(self, channel, long_form=False):
        """
        Reads the wrapper-style measurement blob for a single channel.

        :param int channel: One-based channel number from 1 to 4.
        :param bool long_form: Use ``:MEASUrement:CH<n>?`` instead of
            ``:MEAS:CH<n>?``.
        :rtype: `dict`
        """
        self._validate_channel(channel)
        command = f":MEASUrement:CH{channel}?" if long_form else f":MEAS:CH{channel}?"
        return _parse_measurement_payload(self._binary_query(command), channel)

    def read_all_measurement_data(self, long_form=False):
        """
        Reads the wrapper-style all-channel measurement blob.

        :param bool long_form: Use ``:MEASUrement:ALL?`` instead of ``:MEAS?``.
        :rtype: `dict`
        """
        command = ":MEASUrement:ALL?" if long_form else ":MEAS?"
        return _parse_measurement_map_payload(self._binary_query(command))

    def measure_frequency(self, channel):
        """
        Measures the frequency of a channel.

        :param int channel: One-based channel number from 1 to 4.
        :rtype: `~pint.Quantity`
        """
        return self._measure(channel, "FREQuency", "frequency", u.hertz)

    def measure_period(self, channel):
        """
        Measures the period of a channel.

        :param int channel: One-based channel number from 1 to 4.
        :rtype: `~pint.Quantity`
        """
        return self._measure(channel, "PERiod", "period", u.second)

    def measure_peak_to_peak(self, channel):
        """
        Measures the peak-to-peak voltage of a channel.

        :param int channel: One-based channel number from 1 to 4.
        :rtype: `~pint.Quantity`
        """
        return self._measure(channel, "PKPK", "peak-to-peak voltage", u.volt)

    def measure_rms(self, channel):
        """
        Measures the cycle RMS voltage of a channel.

        :param int channel: One-based channel number from 1 to 4.
        :rtype: `~pint.Quantity`
        """
        return self._measure(channel, "CYCRms", "RMS voltage", u.volt)

    def measure_average(self, channel):
        """
        Measures the average voltage of a channel.

        :param int channel: One-based channel number from 1 to 4.
        :rtype: `~pint.Quantity`
        """
        return self._measure(channel, "AVERage", "average voltage", u.volt)

    def measure_maximum(self, channel):
        """
        Measures the maximum voltage of a channel.

        :param int channel: One-based channel number from 1 to 4.
        :rtype: `~pint.Quantity`
        """
        return self._measure(channel, "MAX", "maximum voltage", u.volt)

    def measure_minimum(self, channel):
        """
        Measures the minimum voltage of a channel.

        :param int channel: One-based channel number from 1 to 4.
        :rtype: `~pint.Quantity`
        """
        return self._measure(channel, "MIN", "minimum voltage", u.volt)

    def measure_top(self, channel):
        """
        Measures the top voltage of a channel.

        :param int channel: One-based channel number from 1 to 4.
        :rtype: `~pint.Quantity`
        """
        return self._measure(channel, "VTOP", "top voltage", u.volt)

    def measure_base(self, channel):
        """
        Measures the base voltage of a channel.

        :param int channel: One-based channel number from 1 to 4.
        :rtype: `~pint.Quantity`
        """
        return self._measure(channel, "VBASe", "base voltage", u.volt)

    def measure_amplitude(self, channel):
        """
        Measures the amplitude voltage of a channel.

        :param int channel: One-based channel number from 1 to 4.
        :rtype: `~pint.Quantity`
        """
        return self._measure(channel, "VAMP", "amplitude voltage", u.volt)

    def measure_rise_time(self, channel):
        """
        Measures the rise time of a channel.

        :param int channel: One-based channel number from 1 to 4.
        :rtype: `~pint.Quantity`
        """
        return self._measure(channel, "RTime", "rise time", u.second)

    def measure_fall_time(self, channel):
        """
        Measures the fall time of a channel.

        :param int channel: One-based channel number from 1 to 4.
        :rtype: `~pint.Quantity`
        """
        return self._measure(channel, "FTime", "fall time", u.second)

    def measure_positive_width(self, channel):
        """
        Measures the positive pulse width of a channel.

        :param int channel: One-based channel number from 1 to 4.
        :rtype: `~pint.Quantity`
        """
        return self._measure(channel, "PWIDth", "positive pulse width", u.second)

    def measure_negative_width(self, channel):
        """
        Measures the negative pulse width of a channel.

        :param int channel: One-based channel number from 1 to 4.
        :rtype: `~pint.Quantity`
        """
        return self._measure(channel, "NWIDth", "negative pulse width", u.second)

    def measure_positive_duty(self, channel):
        """
        Measures the positive duty cycle of a channel.

        :param int channel: One-based channel number from 1 to 4.
        :rtype: `~pint.Quantity`
        """
        return self._measure(channel, "PDUTy", "positive duty cycle", u.percent)

    def measure_negative_duty(self, channel):
        """
        Measures the negative duty cycle of a channel.

        :param int channel: One-based channel number from 1 to 4.
        :rtype: `~pint.Quantity`
        """
        return self._measure(channel, "NDUTy", "negative duty cycle", u.percent)

    def measure_overshoot(self, channel):
        """
        Measures the overshoot percentage of a channel.

        :param int channel: One-based channel number from 1 to 4.
        :rtype: `~pint.Quantity`
        """
        return self._measure(channel, "OVERshoot", "overshoot", u.percent)

    def measure_preshoot(self, channel):
        """
        Measures the preshoot percentage of a channel.

        :param int channel: One-based channel number from 1 to 4.
        :rtype: `~pint.Quantity`
        """
        return self._measure(channel, "PREShoot", "preshoot", u.percent)

    def measure_square_sum(self, channel):
        """
        Measures the short-form ``SQUAresum`` quantity for a channel.

        :param int channel: One-based channel number from 1 to 4.
        :rtype: `~pint.Quantity`
        """
        return self._measure_short(channel, "SQUARESUM", "square sum", u.volt)

    def measure_cursor_rms(self, channel):
        """
        Measures the cursor RMS voltage of a channel.

        :param int channel: One-based channel number from 1 to 4.
        :rtype: `~pint.Quantity`
        """
        return self._measure_short(channel, "CURSorrms", "cursor RMS voltage", u.volt)

    def measure_screen_duty(self, channel):
        """
        Measures the screen duty percentage of a channel.

        :param int channel: One-based channel number from 1 to 4.
        :rtype: `~pint.Quantity`
        """
        return self._measure_short(channel, "SCREenduty", "screen duty", u.percent)

    def measure_positive_pulse_count(self, channel):
        """
        Measures the positive pulse count of a channel.

        :param int channel: One-based channel number from 1 to 4.
        :rtype: `int`
        """
        return self._measure_short_count(channel, "PPULSENUM", "positive pulse count")

    def measure_negative_pulse_count(self, channel):
        """
        Measures the negative pulse count of a channel.

        :param int channel: One-based channel number from 1 to 4.
        :rtype: `int`
        """
        return self._measure_short_count(channel, "NPULSENUM", "negative pulse count")

    def measure_rise_edge_count(self, channel):
        """
        Measures the rising-edge count of a channel.

        :param int channel: One-based channel number from 1 to 4.
        :rtype: `int`
        """
        self._validate_channel(channel)
        return _parse_measurement_count(
            self.query(f":MEASUrement:CH{channel}:RISEedgenum?"), "rising-edge count"
        )

    def measure_fall_edge_count(self, channel):
        """
        Measures the falling-edge count of a channel.

        :param int channel: One-based channel number from 1 to 4.
        :rtype: `int`
        """
        self._validate_channel(channel)
        return _parse_measurement_count(
            self.query(f":MEASUrement:CH{channel}:FALLedgenum?"), "falling-edge count"
        )

    def measure_area(self, channel):
        """
        Measures the area of a channel.

        :param int channel: One-based channel number from 1 to 4.
        :rtype: `~pint.Quantity`
        """
        return self._measure_short(channel, "AREA", "area", u.volt * u.second)

    def measure_cycle_area(self, channel):
        """
        Measures the cycle area of a channel.

        :param int channel: One-based channel number from 1 to 4.
        :rtype: `~pint.Quantity`
        """
        return self._measure_short(
            channel, "CYCLEAREA", "cycle area", u.volt * u.second
        )

    def measure_hard_frequency(self, channel):
        """
        Measures the hard frequency of a channel.

        :param int channel: One-based channel number from 1 to 4.
        :rtype: `~pint.Quantity`
        """
        return self._measure(channel, "HARDfrequency", "hard frequency", u.hertz)

    def _validate_waveform_point_count(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        metadata,
        point_count,
        channel,
        field_name,
        allow_metadata_short_by_one=False,
    ):
        expected = self._waveform_point_count(metadata)
        if point_count == expected:
            return
        if allow_metadata_short_by_one and point_count + 1 == expected:
            return
        raise ValueError(
            f"{field_name} point count mismatch for CH{channel}: "
            f"metadata={expected}, payload={point_count}"
        )

    def _build_waveform_axes(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self, metadata, channel, raw_adc, field_name, allow_metadata_short_by_one=False
    ):
        self._validate_waveform_point_count(
            metadata,
            len(raw_adc),
            channel,
            field_name,
            allow_metadata_short_by_one=allow_metadata_short_by_one,
        )
        point_count = len(raw_adc)
        return (
            self._waveform_time_axis(metadata, point_count),
            self._waveform_voltage_axis(metadata, channel, raw_adc),
        )

    def read_screen_bmp(self):
        """
        Reads the current screen image as BMP bytes.

        :rtype: `bytes`
        """
        payload = self._query_length_prefixed_binary(":DATA:WAVE:SCREen:BMP?")
        bmp_data = payload[4:]
        if len(bmp_data) < 14 or not bmp_data.startswith(b"BM"):
            raise ValueError(
                "SDS1104 screen BMP payload does not contain a valid BMP header."
            )
        bmp_size = int.from_bytes(bmp_data[2:6], byteorder="little", signed=False)
        if bmp_size != len(bmp_data):
            raise ValueError(
                f"SDS1104 BMP length mismatch: header says {bmp_size} bytes, "
                f"received {len(bmp_data)}."
            )
        return bmp_data

    def read_deep_memory_metadata(self):
        """
        Reads the deep-memory metadata JSON.

        :rtype: `dict`
        """
        return _parse_json_payload(
            self._query_length_prefixed_binary(":DATA:WAVE:DEPMEM:HEAD?"),
            "deep-memory metadata",
        )

    def read_deep_memory_channel(self, channel):
        """
        Reads the deep-memory waveform for a channel.

        :param int channel: One-based channel number from 1 to 4.
        :rtype: `tuple`
        """
        self._validate_channel(channel)
        metadata = self.read_deep_memory_metadata()
        payload = self._query_length_prefixed_binary(f":DATA:WAVE:DEPMEM:CH{channel}?")
        raw_adc = _parse_waveform_adc(
            _strip_packet_prefix(payload, f"deep-memory waveform CH{channel}"),
            f"deep-memory waveform CH{channel}",
        )
        return self._build_waveform_axes(
            metadata,
            channel,
            raw_adc,
            "Deep-memory waveform",
            allow_metadata_short_by_one=True,
        )

    def read_deep_memory_all(self):  # pylint: disable=too-many-locals,too-many-branches
        """
        Reads the bundled deep-memory capture as metadata plus raw channel data.

        :rtype: `SDS1104DeepMemoryCapture`
        """
        payload = self._query_length_prefixed_binary(
            ":DATA:WAVE:DEPMem:All?", max_body_size=100_000_000
        )
        body = payload[4:]
        if len(body) < 4:
            raise ValueError(
                "Deep-memory bundle payload is too short for metadata length."
            )

        metadata_size = int.from_bytes(body[:4], byteorder="little", signed=False)
        if metadata_size <= 0:
            raise ValueError(
                f"Invalid deep-memory bundle metadata length: {metadata_size}"
            )
        if 4 + metadata_size > len(body):
            raise ValueError(
                "Deep-memory bundle metadata length exceeds the received payload size."
            )

        metadata_text = body[4 : 4 + metadata_size].decode("utf-8", errors="replace")
        metadata = json.loads(metadata_text.strip())
        if not isinstance(metadata, dict):
            raise ValueError(f"Invalid deep-memory bundle metadata: {metadata_text!r}")

        offset = 4 + metadata_size
        raw_blocks = []
        block_channel = 1
        while offset < len(body):
            if offset + 4 > len(body):
                raise ValueError(
                    "Deep-memory bundle is truncated before a channel block length."
                )
            block_size = int.from_bytes(
                body[offset : offset + 4], byteorder="little", signed=False
            )
            offset += 4
            if offset + block_size > len(body):
                raise ValueError(
                    f"Deep-memory bundle CH{block_channel} block exceeds the "
                    "received payload size."
                )
            raw_adc = _parse_waveform_adc(
                body[offset : offset + block_size],
                f"deep-memory bundle CH{block_channel}",
            )
            self._validate_waveform_point_count(
                metadata,
                len(raw_adc),
                block_channel,
                "Deep-memory bundle waveform",
                allow_metadata_short_by_one=True,
            )
            raw_blocks.append(raw_adc)
            offset += block_size
            block_channel += 1

        if not raw_blocks:
            raise ValueError("Deep-memory bundle did not contain any channel blocks.")

        raw_channels = {}
        metadata_channels = metadata.get("CHANNEL")
        displayed_channel_ids = []
        if isinstance(metadata_channels, list):
            for index, channel_metadata in enumerate(metadata_channels, start=1):
                if (
                    isinstance(channel_metadata, dict)
                    and str(channel_metadata.get("DISPLAY", "")).upper() == "ON"
                ):
                    displayed_channel_ids.append(index)

        if displayed_channel_ids and len(displayed_channel_ids) == len(raw_blocks):
            channel_ids = displayed_channel_ids
        else:
            channel_ids = list(range(1, len(raw_blocks) + 1))

        for channel_id, raw_adc in zip(channel_ids, raw_blocks, strict=True):
            raw_channels[channel_id] = raw_adc

        return SDS1104DeepMemoryCapture(
            metadata=metadata,
            raw_channels=raw_channels,
        )

    def list_saved_waveforms(self):
        """
        Lists saved-waveform entries exposed by ``:SAVE:READ:HEAD?``.

        :rtype: `list`
        """
        payload = self._query_length_prefixed_binary(":SAVE:READ:HEAD?")
        return [
            SDS1104SavedWaveformEntry(index=str(item["Index"]), raw=dict(item))
            for item in _parse_json_array_payload(payload, "saved waveform head")
        ]

    def read_saved_waveform_data(self, index):
        """
        Reads the raw ADC payload for a saved-waveform entry.

        :param index: Saved-waveform index token.
        :rtype: `numpy.ndarray` or `tuple`
        """
        cleaned_index = str(index).strip()
        if not cleaned_index:
            raise ValueError("Saved waveform index must not be empty.")
        payload = self._query_length_prefixed_binary(f":SAVE:READ:DATA {cleaned_index}")
        return _parse_waveform_adc(
            _strip_packet_prefix(
                payload, f"saved waveform data for index {cleaned_index}"
            ),
            f"saved waveform data for index {cleaned_index}",
        )
