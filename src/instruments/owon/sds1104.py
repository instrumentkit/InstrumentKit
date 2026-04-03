#!/usr/bin/env python
"""
Provides support for the OWON SDS1104 oscilloscope family.
"""

# pylint: disable=too-many-lines

# IMPORTS #####################################################################


from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime, timezone
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
    "uv": 1e-6,
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
    1e-6: "1.0us",
    2e-6: "2.0us",
    5e-6: "5.0us",
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


def _normalize_enum_token(token):
    """
    Normalizes a reply or user token for enum matching.
    """
    return _clean_reply(str(token)).strip().upper()


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


def _trace_hex_preview(data, max_bytes=8):
    """
    Renders a compact hexadecimal preview for trace logs.
    """
    if not data:
        return ""
    return bytes(data[:max_bytes]).hex()


def _extract_trace_bytes(exc):
    """
    Best-effort extraction of partial bytes from an exception object.
    """
    for attribute in ("bytes_received", "partial", "received", "data", "payload"):
        value = getattr(exc, attribute, None)
        if isinstance(value, (bytes, bytearray)):
            return bytes(value)
    if exc.args:
        first = exc.args[0]
        if isinstance(first, (bytes, bytearray)):
            return bytes(first)
    return b""


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
    for suffix, scale in sorted(
        units_map.items(), key=lambda item: len(item[0]), reverse=True
    ):
        if cleaned.endswith(suffix):
            magnitude = cleaned[: -len(suffix)]
            try:
                return float(magnitude) * scale
            except ValueError as exc:
                raise ValueError(f"Invalid {field_name} reply: {token!r}") from exc
    raise ValueError(f"Invalid {field_name} reply: {token!r}")


def _parse_enum_token(token, enum_cls, field_name):
    """
    Parses a mixed-case reply into an enum member.
    """
    normalized = _normalize_enum_token(token)
    for member in enum_cls:
        if normalized in {
            _normalize_enum_token(member.name),
            _normalize_enum_token(member.value),
        }:
            return member
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


def _decimal_from_magnitude(value):
    """
    Converts a numeric magnitude into a finite decimal representation.
    """
    return Decimal(format(float(value), ".15g"))


def _format_decimal_string(value):
    """
    Formats a decimal without scientific notation.
    """
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    if text in {"-0", ""}:
        return "0"
    return text


def _format_scaled_token(base_magnitude, unit_scales, allowed_units, field_name):
    """
    Formats a base-unit magnitude using engineering-style unit tokens.
    """
    base = _decimal_from_magnitude(base_magnitude)
    scale_map = {
        unit: _decimal_from_magnitude(scale)
        for unit, scale in unit_scales.items()
        if unit in allowed_units
    }
    if len(scale_map) != len(tuple(allowed_units)):
        missing = [unit for unit in allowed_units if unit not in scale_map]
        raise ValueError(f"Unsupported {field_name} units: {missing!r}")

    candidates = []
    for unit in allowed_units:
        scaled = base / scale_map[unit]
        magnitude = abs(scaled)
        candidates.append(
            {
                "unit": unit,
                "scaled": scaled,
                "in_window": Decimal("1") <= magnitude < Decimal("1000"),
            }
        )

    if base == 0:
        chosen = candidates[-1]
    else:
        in_window = [candidate for candidate in candidates if candidate["in_window"]]
        if in_window:
            chosen = in_window[0]
        elif abs(candidates[0]["scaled"]) < Decimal("1"):
            chosen = candidates[0]
        else:
            chosen = candidates[-1]

    return f"{_format_decimal_string(chosen['scaled'])}{chosen['unit']}"


def _format_quantity_token(
    value, allowed_units=("uv", "mv", "v"), prefer_smallest_exact=True
):
    """
    Formats a voltage-like quantity token without scientific notation.
    """
    if not prefer_smallest_exact:
        allowed_units = tuple(reversed(tuple(allowed_units)))
    return _format_scaled_token(
        assume_units(value, u.volt).to(u.volt).magnitude,
        _VERTICAL_UNITS,
        tuple(allowed_units),
        "quantity",
    )


def _format_time_token(
    value, allowed_units=("ns", "us", "ms", "s"), prefer_smallest_exact=True
):
    """
    Formats a time quantity token without scientific notation.
    """
    if not prefer_smallest_exact:
        allowed_units = tuple(reversed(tuple(allowed_units)))
    return _format_scaled_token(
        assume_units(value, u.second).to(u.second).magnitude,
        _TIME_UNITS,
        tuple(allowed_units),
        "time",
    )


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
    cleaned = cleaned.replace("(", "").replace(")", "")
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

    ``raw_channels`` contains the raw ADC samples exactly as returned by the
    instrument. Use ``read_deep_memory_channel()`` when you want converted
    time/voltage axes.
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


@dataclass(frozen=True)
class SDS1104TriggerConfiguration:
    """
    Snapshot of the current SDS1104 trigger configuration.
    """

    status: Any
    trigger_type: Any
    single_trigger_mode: Any
    holdoff: Any
    trigger_sweep: Any = None
    edge_source: Any = None
    edge_coupling: Any = None
    edge_slope: Any = None
    edge_level: Any = None
    video_source: Any = None
    video_standard: Any = None
    video_sync: Any = None
    video_line_number: int | None = None


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

    class TriggerType(Enum):
        """
        Top-level trigger types reported by ``:TRIGger:TYPE?``.
        """

        # pylint: disable=invalid-name

        single = "SINGle"
        alt = "ALT"
        logic = "LOGic"
        bus = "BUS"

    class SingleTriggerMode(Enum):
        """
        Single-trigger modes supported by the verified SDS1104 API surface.
        """

        # pylint: disable=invalid-name

        edge = "EDGE"
        video = "VIDEO"
        pulse = "PULSe"
        slope = "SLOPe"

    TriggerMode = SingleTriggerMode

    class TriggerSource(Enum):
        """
        Edge-trigger sources.
        """

        # pylint: disable=invalid-name

        ch1 = "CH1"
        ch2 = "CH2"
        ch3 = "CH3"
        ch4 = "CH4"
        ext = "EXT"
        ext_div5 = "EXT/5"
        ac_line = "ACLine"

    class TriggerCoupling(Enum):
        """
        Edge-trigger coupling modes verified on hardware.
        """

        # pylint: disable=invalid-name

        ac = "AC"
        dc = "DC"
        hf = "HF"

    class TriggerSlope(Enum):
        """
        Edge-trigger slope modes verified on hardware.
        """

        # pylint: disable=invalid-name

        rise = "RISE"
        fall = "FALL"

    class TriggerSweep(Enum):
        """
        Single-trigger sweep modes.
        """

        # pylint: disable=invalid-name

        auto = "AUTO"
        normal = "NORMal"
        single = "SINGle"

    class RunningState(Enum):
        """
        Front-panel-equivalent running states.
        """

        # pylint: disable=invalid-name

        run = "RUN"
        stop = "STOP"

    class VideoStandard(Enum):
        """
        Video trigger standards verified on the SDS1104 family.
        """

        # pylint: disable=invalid-name

        pal = "PAL"
        secam = "SECam"
        ntsc = "NTSC"

    class VideoSync(Enum):
        """
        Video trigger synchronization modes verified on the SDS1104 family.
        """

        # pylint: disable=invalid-name

        line = "LINE"
        field = "FIELD"
        odd = "ODD"
        even = "EVEN"
        lnum = "LNUM"

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
            Experimental / undocumented deep-memory waveform query for this channel.
            """
            return self._parent.read_deep_memory_channel(self._idx)

    def __init__(self, filelike):
        super().__init__(filelike)
        self._file.timeout = 1 * u.second
        self._trace_path = None
        self._trace_seq = 0

    def enable_trace(self, trace_path):
        """
        Enables best-effort SCPI trace logging to a JSONL file.
        """
        self._trace_path = str(trace_path)
        self._trace_seq = 0

    def disable_trace(self):
        """
        Disables SCPI trace logging.
        """
        self._trace_path = None

    def _trace_timestamp(self):
        return datetime.now(timezone.utc).isoformat(timespec="microseconds")

    def _trace_event(self, event):
        if not self._trace_path:
            return
        try:
            self._trace_seq += 1
            payload = {"ts": self._trace_timestamp(), "seq": self._trace_seq}
            payload.update(event)
            with open(self._trace_path, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, ensure_ascii=True) + "\n")
        except Exception:
            pass

    def sendcmd(self, cmd):
        start = time.monotonic()
        command = str(cmd)
        try:
            super().sendcmd(command)
            self._trace_event(
                {
                    "direction": "sendcmd",
                    "command": command,
                    "ok": True,
                    "duration_ms": (time.monotonic() - start) * 1000.0,
                }
            )
        except Exception as exc:
            self._trace_event(
                {
                    "direction": "sendcmd",
                    "command": command,
                    "ok": False,
                    "error_type": type(exc).__name__,
                    "error_text": str(exc),
                    "duration_ms": (time.monotonic() - start) * 1000.0,
                }
            )
            raise

    def query(self, cmd, size=-1):
        start = time.monotonic()
        command = str(cmd)
        try:
            reply = super().query(command, size=size)
            self._trace_event(
                {
                    "direction": "query",
                    "command": command,
                    "reply_kind": "text",
                    "reply_text": str(reply),
                    "ok": True,
                    "duration_ms": (time.monotonic() - start) * 1000.0,
                }
            )
            return reply
        except Exception as exc:
            self._trace_event(
                {
                    "direction": "query",
                    "command": command,
                    "ok": False,
                    "error_type": type(exc).__name__,
                    "error_text": str(exc),
                    "duration_ms": (time.monotonic() - start) * 1000.0,
                }
            )
            raise

    def _close_transport_best_effort(self):
        """
        Closes the underlying transport without raising cleanup errors.
        """
        close_method = getattr(self._file, "close", None)
        if callable(close_method):
            try:
                close_method()
            except Exception:
                pass

    def reset_usb_device(self, settle_time=1.0):
        """
        Best-effort hard USB device reset for contaminated sessions.
        """
        dev = getattr(self._file, "_dev", None)

        flush_method = getattr(self._file, "flush_input", None)
        if callable(flush_method):
            try:
                flush_method()
            except Exception:
                pass

        self._close_transport_best_effort()

        if dev is not None and hasattr(dev, "reset"):
            try:
                dev.reset()
            except Exception:
                pass

        if dev is not None:
            try:
                usb.util.dispose_resources(dev)
            except Exception:
                pass

        time.sleep(max(float(settle_time), 0.0))

    def close(self, reset_device=False, settle_time=0.0):
        """
        Closes the underlying transport.

        :param bool reset_device: When ``True``, attempt a hard USB reset.
        :param float settle_time: Delay after a hard reset.
        """
        if reset_device:
            self.reset_usb_device(settle_time=settle_time)
            return
        self._close_transport_best_effort()

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

    def _flush_input_best_effort(self, suppress_errors=True):
        """
        Flushes any stale USB input bytes before a binary transfer.

        Text setters on the OWON family can leave a trailing prompt token in
        the input buffer. If a binary read starts with that stale prompt, the
        next binary parser sees garbage such as ``b'>\\n'`` instead of the
        expected payload header.
        """
        flush_method = getattr(self._file, "flush_input", None)
        if callable(flush_method):
            try:
                time.sleep(0.05)
                flush_method()
                time.sleep(0.02)
                flush_method()
            except Exception:
                if suppress_errors:
                    pass
                else:
                    raise

    def _binary_query(self, command):
        """
        Sends a raw USB command and reads a binary reply.
        """
        start = time.monotonic()
        if not hasattr(self._file, "read_binary"):
            raise NotImplementedError(
                "Binary waveform support requires a communicator that "
                "implements read_binary()."
            )
        try:
            self._flush_input_best_effort(suppress_errors=False)
            self._file.write_raw(command.encode("ascii"))
        except Exception as exc:
            self._trace_event(
                {
                    "direction": "binary_query",
                    "command": command,
                    "phase": "write",
                    "ok": False,
                    "error_type": type(exc).__name__,
                    "error_text": str(exc),
                    "duration_ms": (time.monotonic() - start) * 1000.0,
                }
            )
            raise
        try:
            payload = self._file.read_binary()
            self._trace_event(
                {
                    "direction": "binary_query",
                    "command": command,
                    "reply_kind": "binary",
                    "phase": "read",
                    "payload_length": len(payload),
                    "ok": True,
                    "duration_ms": (time.monotonic() - start) * 1000.0,
                }
            )
            return payload
        except Exception as exc:
            partial = _extract_trace_bytes(exc)
            self._trace_event(
                {
                    "direction": "binary_query",
                    "command": command,
                    "phase": "read",
                    "ok": False,
                    "error_type": type(exc).__name__,
                    "error_text": str(exc),
                    "bytes_received": len(partial),
                    "header_preview_hex": _trace_hex_preview(partial),
                    "duration_ms": (time.monotonic() - start) * 1000.0,
                }
            )
            raise

    def _binary_query_exact(self, command, size):
        """
        Sends a raw USB command and reads an exact-size binary reply.
        """
        start = time.monotonic()
        if not hasattr(self._file, "read_exact"):
            raise NotImplementedError(
                "Binary waveform support requires a communicator that "
                "implements read_exact()."
            )
        try:
            self._flush_input_best_effort(suppress_errors=False)
            self._file.write_raw(command.encode("ascii"))
        except Exception as exc:
            self._trace_event(
                {
                    "direction": "binary_query_exact",
                    "command": command,
                    "phase": "write",
                    "expected_length": size,
                    "ok": False,
                    "error_type": type(exc).__name__,
                    "error_text": str(exc),
                    "duration_ms": (time.monotonic() - start) * 1000.0,
                }
            )
            raise
        try:
            payload = self._file.read_exact(size)
            self._trace_event(
                {
                    "direction": "binary_query_exact",
                    "command": command,
                    "reply_kind": "binary",
                    "phase": "read",
                    "expected_length": size,
                    "payload_length": len(payload),
                    "ok": True,
                    "duration_ms": (time.monotonic() - start) * 1000.0,
                }
            )
            return payload
        except Exception as exc:
            partial = _extract_trace_bytes(exc)
            self._trace_event(
                {
                    "direction": "binary_query_exact",
                    "command": command,
                    "phase": "read",
                    "expected_length": size,
                    "ok": False,
                    "error_type": type(exc).__name__,
                    "error_text": str(exc),
                    "bytes_received": len(partial),
                    "header_preview_hex": _trace_hex_preview(partial),
                    "duration_ms": (time.monotonic() - start) * 1000.0,
                }
            )
            raise

    def _query_length_prefixed_binary(self, command, max_body_size=20_000_000):
        """
        Sends a raw USB command and reads a little-endian length-prefixed body.
        """
        start = time.monotonic()
        if not hasattr(self._file, "read_exact"):
            raise NotImplementedError(
                "Length-prefixed binary support requires a communicator that "
                "implements read_exact()."
            )
        try:
            self._flush_input_best_effort(suppress_errors=False)
        except Exception as exc:
            self._trace_event(
                {
                    "direction": "binary_length_prefixed_query",
                    "command": command,
                    "phase": "flush",
                    "ok": False,
                    "error_type": type(exc).__name__,
                    "error_text": str(exc),
                    "duration_ms": (time.monotonic() - start) * 1000.0,
                }
            )
            raise

        try:
            self._file.write_raw(command.encode("ascii"))
        except Exception as exc:
            self._trace_event(
                {
                    "direction": "binary_length_prefixed_query",
                    "command": command,
                    "phase": "write",
                    "ok": False,
                    "error_type": type(exc).__name__,
                    "error_text": str(exc),
                    "duration_ms": (time.monotonic() - start) * 1000.0,
                }
            )
            raise

        try:
            header = self._file.read_exact(4)
        except Exception as exc:
            partial = _extract_trace_bytes(exc)
            self._trace_event(
                {
                    "direction": "binary_length_prefixed_query",
                    "command": command,
                    "phase": "header",
                    "ok": False,
                    "error_type": type(exc).__name__,
                    "error_text": str(exc),
                    "header_bytes_received": len(partial),
                    "header_preview_hex": _trace_hex_preview(partial),
                    "duration_ms": (time.monotonic() - start) * 1000.0,
                }
            )
            raise

        if len(header) < 4:
            exc = ValueError(f"Length-prefixed reply too short for {command!r}.")
            self._trace_event(
                {
                    "direction": "binary_length_prefixed_query",
                    "command": command,
                    "phase": "header",
                    "ok": False,
                    "error_type": type(exc).__name__,
                    "error_text": str(exc),
                    "header_bytes_received": len(header),
                    "header_preview_hex": _trace_hex_preview(header),
                    "duration_ms": (time.monotonic() - start) * 1000.0,
                }
            )
            raise exc

        try:
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
        except Exception as exc:
            self._trace_event(
                {
                    "direction": "binary_length_prefixed_query",
                    "command": command,
                    "phase": "header_parse",
                    "ok": False,
                    "error_type": type(exc).__name__,
                    "error_text": str(exc),
                    "header_bytes_received": len(header),
                    "header_preview_hex": _trace_hex_preview(header),
                    "duration_ms": (time.monotonic() - start) * 1000.0,
                }
            )
            raise
        try:
            body = self._file.read_exact(body_size)
            payload = header + body
            self._trace_event(
                {
                    "direction": "binary_length_prefixed_query",
                    "command": command,
                    "reply_kind": "binary",
                    "phase": "complete",
                    "header_length": body_size,
                    "payload_length": len(body),
                    "ok": True,
                    "duration_ms": (time.monotonic() - start) * 1000.0,
                }
            )
            return payload
        except Exception as exc:
            partial = _extract_trace_bytes(exc)
            self._trace_event(
                {
                    "direction": "binary_length_prefixed_query",
                    "command": command,
                    "phase": "body",
                    "ok": False,
                    "error_type": type(exc).__name__,
                    "error_text": str(exc),
                    "header_bytes_received": len(header),
                    "header_preview_hex": _trace_hex_preview(header),
                    "body_length_expected": body_size,
                    "body_bytes_received": len(partial),
                    "duration_ms": (time.monotonic() - start) * 1000.0,
                }
            )
            raise

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

    def _waveform_counts_per_div(self, metadata, channel):
        channel_metadata = self._extract_channel_metadata(metadata, channel)
        current_rate = channel_metadata.get("Current_Rate")
        current_ratio = channel_metadata.get("Current_Ratio")
        if current_rate is None or current_ratio in {None, 0, 0.0}:
            return None
        return float(current_rate) / float(current_ratio)

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
        counts_per_div = self._waveform_counts_per_div(metadata, channel)
        if counts_per_div is not None:
            # Empirical DOS1104 screen/deep-memory scaling:
            # OFFSET steps are 1/50 div and the zero-volt raw baseline is
            # approximately ``OFFSET * 128 - 256`` counts.
            raw_zero = vertical_offset * 128.0 - 256.0
            if numpy is not None and isinstance(raw_adc, numpy.ndarray):
                return (
                    volts_per_div
                    * probe
                    * (raw_adc.astype(float) - raw_zero)
                    / counts_per_div
                )
            return tuple(
                volts_per_div * probe * (sample - raw_zero) / counts_per_div
                for sample in raw_adc
            )
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
        return _parse_enum_token(
            self.query(":TRIGger:STATUS?"), self.TriggerStatus, "trigger status"
        )

    @property
    def trigger_type(self):
        """
        Gets the current top-level trigger type.

        This is query-only because the alternative write paths are not yet
        reproducible enough to promote in this driver.

        :type: `OWONSDS1104.TriggerType`
        """
        return _parse_enum_token(
            self.query(":TRIGger:TYPE?"), self.TriggerType, "trigger type"
        )

    @property
    def single_trigger_mode(self):
        """
        Gets/sets the current single-trigger mode.

        :type: `OWONSDS1104.SingleTriggerMode`
        """
        return _parse_enum_token(
            self.query(":TRIGger:SINGle:MODE?"),
            self.SingleTriggerMode,
            "single trigger mode",
        )

    @single_trigger_mode.setter
    def single_trigger_mode(self, newval):
        if not isinstance(newval, self.SingleTriggerMode):
            raise TypeError(
                "Trigger mode must be specified with a "
                "`OWONSDS1104.SingleTriggerMode` value."
            )
        self.sendcmd(f":TRIGger:SINGle:MODE {newval.value}")

    @property
    def trigger_mode(self):
        """
        Backward-compatible alias for :attr:`single_trigger_mode`.
        """
        return self.single_trigger_mode

    @trigger_mode.setter
    def trigger_mode(self, newval):
        self.single_trigger_mode = newval

    def _require_edge_trigger_mode(self):
        mode = self.single_trigger_mode
        if mode != self.SingleTriggerMode.edge:
            raise NotImplementedError(
                "Edge trigger source, coupling, slope, and level are only "
                "exposed when single_trigger_mode is EDGE in this driver."
            )

    def _require_video_trigger_mode(self):
        mode = self.single_trigger_mode
        if mode != self.SingleTriggerMode.video:
            raise NotImplementedError(
                "Video trigger source, standard, sync, and line number are only "
                "exposed when single_trigger_mode is VIDEO in this driver."
            )

    @property
    def trigger_source(self):
        """
        Gets/sets the edge-trigger source.

        This property is only available when ``single_trigger_mode`` is
        ``EDGE``.

        :type: `OWONSDS1104.TriggerSource`
        """
        self._require_edge_trigger_mode()
        return _parse_enum_token(
            self.query(":TRIGger:SINGle:EDGE:SOURce?"),
            self.TriggerSource,
            "trigger source",
        )

    @trigger_source.setter
    def trigger_source(self, newval):
        self._require_edge_trigger_mode()
        if not isinstance(newval, self.TriggerSource):
            raise TypeError(
                "Trigger source must be specified with a "
                "`OWONSDS1104.TriggerSource` value."
            )
        if newval not in {
            self.TriggerSource.ch1,
            self.TriggerSource.ch2,
            self.TriggerSource.ch3,
            self.TriggerSource.ch4,
            self.TriggerSource.ac_line,
        }:
            raise ValueError(
                "Edge trigger source write support is currently verified only "
                "for CH1-CH4 and ACLine."
            )
        self.sendcmd(f":TRIGger:SINGle:EDGE:SOURce {newval.value}")

    @property
    def trigger_coupling(self):
        """
        Gets/sets the edge-trigger coupling.

        This property is only available when ``single_trigger_mode`` is
        ``EDGE``.

        :type: `OWONSDS1104.TriggerCoupling`
        """
        self._require_edge_trigger_mode()
        return _parse_enum_token(
            self.query(":TRIGger:SINGle:EDGE:COUPling?"),
            self.TriggerCoupling,
            "trigger coupling",
        )

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

        This property is only available when ``single_trigger_mode`` is
        ``EDGE``.

        :type: `OWONSDS1104.TriggerSlope`
        """
        self._require_edge_trigger_mode()
        return _parse_enum_token(
            self.query(":TRIGger:SINGle:EDGE:SLOPe?"),
            self.TriggerSlope,
            "trigger slope",
        )

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

        This property is only available when ``single_trigger_mode`` is
        ``EDGE``.

        :type: `~pint.Quantity`
        """
        self._require_edge_trigger_mode()
        value = _parse_quantity_token(
            self.query(":TRIGger:SINGle:EDGE:LEVel?"),
            {"uv": 1e-6, "mv": 1e-3, "v": 1.0},
            "trigger level",
        )
        return u.Quantity(value, u.volt)

    @trigger_level.setter
    def trigger_level(self, newval):
        self._require_edge_trigger_mode()
        self.sendcmd(f":TRIGger:SINGle:EDGE:LEVel {_format_quantity_token(newval)}")

    @property
    def edge_trigger_source(self):
        """
        Preferred alias for :attr:`trigger_source`.
        """
        return self.trigger_source

    @edge_trigger_source.setter
    def edge_trigger_source(self, newval):
        self.trigger_source = newval

    @property
    def edge_trigger_coupling(self):
        """
        Preferred alias for :attr:`trigger_coupling`.
        """
        return self.trigger_coupling

    @edge_trigger_coupling.setter
    def edge_trigger_coupling(self, newval):
        self.trigger_coupling = newval

    @property
    def edge_trigger_slope(self):
        """
        Preferred alias for :attr:`trigger_slope`.
        """
        return self.trigger_slope

    @edge_trigger_slope.setter
    def edge_trigger_slope(self, newval):
        self.trigger_slope = newval

    @property
    def edge_trigger_level(self):
        """
        Preferred alias for :attr:`trigger_level`.
        """
        return self.trigger_level

    @edge_trigger_level.setter
    def edge_trigger_level(self, newval):
        self.trigger_level = newval

    @property
    def trigger_holdoff(self):
        """
        Gets/sets the single-trigger holdoff time.

        :type: `~pint.Quantity`
        """
        return u.Quantity(
            _parse_quantity_token(
                self.query(":TRIGger:SINGle:HOLDoff?"), _TIME_UNITS, "trigger holdoff"
            ),
            u.second,
        )

    @trigger_holdoff.setter
    def trigger_holdoff(self, newval):
        holdoff = assume_units(newval, u.second).to(u.second)
        if holdoff < 100 * u.nanosecond or holdoff > 10 * u.second:
            raise ValueError("Trigger holdoff must be between 100 ns and 10 s.")
        self.sendcmd(f":TRIGger:SINGle:HOLDoff {_format_time_token(holdoff)}")

    @property
    def trigger_sweep(self):
        """
        Gets/sets the single-trigger sweep mode.

        :type: `OWONSDS1104.TriggerSweep`
        """
        return _parse_enum_token(
            self.query(":TRIGger:SINGle:SWEEp?"),
            self.TriggerSweep,
            "trigger sweep",
        )

    @trigger_sweep.setter
    def trigger_sweep(self, newval):
        if not isinstance(newval, self.TriggerSweep):
            raise TypeError(
                "Trigger sweep must be specified with a `OWONSDS1104.TriggerSweep` value."
            )
        self.sendcmd(f":TRIGger:SINGle:SWEEp {newval.value}")

    @property
    def video_trigger_source(self):
        """
        Gets/sets the video-trigger source.

        :type: `OWONSDS1104.TriggerSource`
        """
        self._require_video_trigger_mode()
        return _parse_enum_token(
            self.query(":TRIGger:SINGle:VIDeo:SOURce?"),
            self.TriggerSource,
            "video trigger source",
        )

    @video_trigger_source.setter
    def video_trigger_source(self, newval):
        self._require_video_trigger_mode()
        if not isinstance(newval, self.TriggerSource):
            raise TypeError(
                "Video trigger source must be specified with a "
                "`OWONSDS1104.TriggerSource` value."
            )
        if newval not in {self.TriggerSource.ch1, self.TriggerSource.ch2}:
            raise ValueError(
                "Video trigger source write support is currently verified only "
                "for CH1 and CH2."
            )
        self.sendcmd(f":TRIGger:SINGle:VIDeo:SOURce {newval.value}")

    @property
    def video_trigger_standard(self):
        """
        Gets/sets the video-trigger standard.

        Query uses ``:TRIGger:SINGle:VIDeo:MODU?`` while writes use the
        verified ``:TRIGger:SINGle:System`` command path.

        :type: `OWONSDS1104.VideoStandard`
        """
        self._require_video_trigger_mode()
        return _parse_enum_token(
            self.query(":TRIGger:SINGle:VIDeo:MODU?"),
            self.VideoStandard,
            "video trigger standard",
        )

    @video_trigger_standard.setter
    def video_trigger_standard(self, newval):
        self._require_video_trigger_mode()
        if not isinstance(newval, self.VideoStandard):
            raise TypeError(
                "Video trigger standard must be specified with a "
                "`OWONSDS1104.VideoStandard` value."
            )
        self.sendcmd(f":TRIGger:SINGle:System {newval.value}")

    @property
    def video_trigger_sync(self):
        """
        Gets/sets the video-trigger synchronization mode.

        Query uses ``:TRIGger:SINGle:VIDeo:SYNC?`` while writes use the
        verified ``:TRIGger:SINGle:Sync`` command path.

        :type: `OWONSDS1104.VideoSync`
        """
        self._require_video_trigger_mode()
        return _parse_enum_token(
            self.query(":TRIGger:SINGle:VIDeo:SYNC?"),
            self.VideoSync,
            "video trigger sync",
        )

    @video_trigger_sync.setter
    def video_trigger_sync(self, newval):
        self._require_video_trigger_mode()
        if not isinstance(newval, self.VideoSync):
            raise TypeError(
                "Video trigger sync must be specified with a "
                "`OWONSDS1104.VideoSync` value."
            )
        self.sendcmd(f":TRIGger:SINGle:Sync {newval.value}")

    @property
    def video_trigger_line_number(self):
        """
        Gets/sets the video-trigger line number.

        The line number is only meaningful when ``video_trigger_sync`` is
        ``LNUM``.

        :type: `int`
        """
        self._require_video_trigger_mode()
        return int(_clean_reply(self.query(":TRIGger:SINGle:VIDeo:LNUM?")))

    @video_trigger_line_number.setter
    def video_trigger_line_number(self, newval):
        self._require_video_trigger_mode()
        if self.video_trigger_sync != self.VideoSync.lnum:
            raise ValueError(
                "Video trigger line number can only be set when "
                "video_trigger_sync is LNUM."
            )
        self.sendcmd(f":TRIGger:SINGle:LineNum {int(newval)}")

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

    def set_running_state(self, newval):
        """
        Sets the front-panel-equivalent running state.
        """
        if not isinstance(newval, self.RunningState):
            raise TypeError(
                "Running state must be specified with a `OWONSDS1104.RunningState` value."
            )
        self.sendcmd(f":RUNning {newval.value}")

    def run_front_panel(self):
        """
        Starts acquisition via the documented ``:RUNning RUN`` path.
        """
        self.set_running_state(self.RunningState.run)

    def stop_front_panel(self):
        """
        Stops acquisition via the documented ``:RUNning STOP`` path.
        """
        self.set_running_state(self.RunningState.stop)

    def arm_single(self, stop_first=True, settle_time=0.05, arm_method="legacy_single"):
        """
        Arms a single acquisition using either the legacy ``:SINGle`` command
        or the documented ``:RUNning RUN`` path.
        """
        if arm_method not in {"legacy_single", "running_run"}:
            raise ValueError(
                "arm_method must be one of {'legacy_single', 'running_run'}."
            )

        if stop_first:
            if arm_method == "legacy_single":
                self.stop()
            else:
                self.stop_front_panel()
            time.sleep(max(float(settle_time), 0.0))

        if arm_method == "legacy_single":
            self.sendcmd(":SINGle")
        else:
            self.run_front_panel()

    def single(self, stop_first=True, settle_time=0.05, arm_method="legacy_single"):
        """
        Arms a single acquisition.

        On the DOS1104/SDS1104 family, issuing ``:SINGle`` directly after a
        prior run state can be unreliable. A short best-effort ``:STOP`` first
        makes the single-acquisition arm behavior more deterministic on the
        units we have on the bench.

        Example

        >>> import instruments as ik
        >>> from instruments.units import ureg as u
        >>> scope = ik.owon.OWONSDS1104.open_usb()
        >>> scope.stop()
        >>> scope.single_trigger_mode = scope.SingleTriggerMode.edge
        >>> scope.trigger_source = scope.TriggerSource.ch1
        >>> scope.trigger_coupling = scope.TriggerCoupling.dc
        >>> scope.trigger_slope = scope.TriggerSlope.rise
        >>> scope.trigger_level = 25 * u.millivolt
        >>> scope.trigger_holdoff = 100 * u.nanosecond
        >>> scope.single()
        >>> scope.wait_for_trigger_status(scope.TriggerStatus.trig, timeout=2 * u.second)
        """
        self.arm_single(
            stop_first=stop_first,
            settle_time=settle_time,
            arm_method=arm_method,
        )

    def stop(self):
        """
        Stops acquisition.
        """
        self.sendcmd(":STOP")

    def freeze_acquisition(self, method="legacy_stop", settle_time=0.05):
        """
        Freezes acquisition using either the legacy ``:STOP`` command or the
        documented ``:RUNning STOP`` path.
        """
        if method not in {"legacy_stop", "running_stop"}:
            raise ValueError("method must be one of {'legacy_stop', 'running_stop'}.")

        if method == "legacy_stop":
            self.stop()
        else:
            self.stop_front_panel()

        time.sleep(max(float(settle_time), 0.0))

    def autoscale(self):
        """
        Executes the scope autoscale action.

        This is an action-like command, not a persistent boolean setting. It
        may reconfigure acquisition, timebase, and channel settings.
        """
        self.sendcmd(":AUTOscale ON")

    def read_trigger_configuration(self):
        """
        Reads a coherent snapshot of the current trigger configuration.

        :rtype: `SDS1104TriggerConfiguration`
        """
        config = SDS1104TriggerConfiguration(
            status=self.trigger_status,
            trigger_type=self.trigger_type,
            single_trigger_mode=self.single_trigger_mode,
            holdoff=self.trigger_holdoff,
            trigger_sweep=self.trigger_sweep,
        )

        if config.single_trigger_mode == self.SingleTriggerMode.edge:
            return SDS1104TriggerConfiguration(
                status=config.status,
                trigger_type=config.trigger_type,
                single_trigger_mode=config.single_trigger_mode,
                holdoff=config.holdoff,
                trigger_sweep=config.trigger_sweep,
                edge_source=self.trigger_source,
                edge_coupling=self.trigger_coupling,
                edge_slope=self.trigger_slope,
                edge_level=self.trigger_level,
            )

        if config.single_trigger_mode == self.SingleTriggerMode.video:
            return SDS1104TriggerConfiguration(
                status=config.status,
                trigger_type=config.trigger_type,
                single_trigger_mode=config.single_trigger_mode,
                holdoff=config.holdoff,
                trigger_sweep=config.trigger_sweep,
                video_source=self.video_trigger_source,
                video_standard=self.video_trigger_standard,
                video_sync=self.video_trigger_sync,
                video_line_number=self.video_trigger_line_number,
            )

        return config

    def wait_for_trigger_status(
        self, target, timeout=1 * u.second, poll_interval=50 * u.millisecond
    ):
        """
        Polls until the trigger status reaches ``target`` or times out.

        :param target: Target trigger status enum member or case-insensitive
            status string.
        :param timeout: Maximum time to wait.
        :param poll_interval: Delay between polls.
        :rtype: `OWONSDS1104.TriggerStatus`
        """
        if isinstance(target, str):
            target = _parse_enum_token(
                target, self.TriggerStatus, "target trigger status"
            )
        if not isinstance(target, self.TriggerStatus):
            raise TypeError(
                "Trigger status target must be a `OWONSDS1104.TriggerStatus` "
                "value or a case-insensitive status string."
            )

        timeout_s = assume_units(timeout, u.second).to(u.second).magnitude
        poll_interval_s = assume_units(poll_interval, u.second).to(u.second).magnitude
        deadline = time.monotonic() + max(timeout_s, 0.0)

        while True:
            status = self.trigger_status
            if status == target:
                return status
            if time.monotonic() >= deadline:
                raise TimeoutError(
                    f"Timed out waiting for trigger status {target.value!r}; "
                    f"last status was {status.value!r}."
                )
            time.sleep(max(poll_interval_s, 0.0))

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
            "No verified force-trigger command is currently promoted for the "
            "OWON SDS1104 / HANMATEK DOS1104 family."
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
        Experimental / undocumented deep-memory metadata query.

        This command family is not listed in the official SDS1000 SCPI PDF.
        Prefer ``read_deep_memory_all()`` for the documented deep-memory path.

        :rtype: `dict`
        """
        return _parse_json_payload(
            self._query_length_prefixed_binary(":DATA:WAVE:DEPMEM:HEAD?"),
            "deep-memory metadata",
        )

    def read_deep_memory_channel(self, channel):
        """
        Experimental / undocumented deep-memory channel query.

        This command family is not listed in the official SDS1000 SCPI PDF.
        Prefer ``read_deep_memory_all()`` for the documented deep-memory path.

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

    def read_deep_memory_all_raw(self):
        """
        Reads the raw bundled deep-memory payload bytes.

        The returned payload includes the outer 4-byte little-endian body
        length header exactly as received from the instrument.

        :rtype: `bytes`
        """
        return self._query_length_prefixed_binary(
            ":DATA:WAVE:DEPMem:All?", max_body_size=100_000_000
        )

    def _parse_deep_memory_all_payload(
        self, payload
    ):  # pylint: disable=too-many-locals,too-many-branches
        """
        Parses a raw ``:DATA:WAVE:DEPMem:All?`` payload into metadata plus raw channels.
        """
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

        return SDS1104DeepMemoryCapture(metadata=metadata, raw_channels=raw_channels)

    def read_deep_memory_all(self):  # pylint: disable=too-many-locals,too-many-branches
        """
        Reads the bundled deep-memory capture as metadata plus raw channel data.

        This method preserves the raw ADC payloads. For converted deep-memory
        time/voltage axes, use ``read_deep_memory_channel()``.

        :rtype: `SDS1104DeepMemoryCapture`
        """
        payload = self.read_deep_memory_all_raw()
        return self._parse_deep_memory_all_payload(payload)

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
