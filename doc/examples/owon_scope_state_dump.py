#!/usr/bin/env python
"""
Capture a broad, mostly safe OWON/HANMATEK DOS1104 state snapshot.

This is intended for bench debugging when scope state appears persistent across
reboots or when a specific front-panel/SCPI combination needs to be preserved
for later analysis.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

import instruments as ik
from instruments.units import ureg as u


def _timestamp():
    return datetime.now(timezone.utc)


def _artifact_dir(root, label, timestamp=None):
    timestamp = _timestamp() if timestamp is None else timestamp
    date_dir = Path(root) / timestamp.strftime("%Y%m%d")
    return date_dir / f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{label}"


def _progress(message):
    print(f"[state-dump] {message}", flush=True)


def _jsonable(value):
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if hasattr(value, "units"):
        return {"value": value.magnitude, "units": str(value.units)}
    if hasattr(value, "name") and hasattr(value, "value"):
        return {"name": value.name, "value": value.value}
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def _capture(label, fn):
    try:
        return {"ok": True, "value": _jsonable(fn())}
    except Exception as exc:  # pragma: no cover - bench-only error path
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def _channel_state(scope, index):
    channel = scope.channel[index - 1]
    return {
        "display": _capture("display", lambda: channel.display),
        "coupling": _capture("coupling", lambda: channel.coupling),
        "probe_attenuation": _capture(
            "probe_attenuation", lambda: channel.probe_attenuation
        ),
        "scale": _capture("scale", lambda: channel.scale),
        "offset": _capture("offset", lambda: channel.offset),
        "position": _capture("position", lambda: channel.position),
        "invert": _capture("invert", lambda: channel.invert),
    }


def _trigger_state(scope):
    state = {
        "trigger_status": _capture("trigger_status", lambda: scope.trigger_status),
        "trigger_type": _capture("trigger_type", lambda: scope.trigger_type),
        "single_trigger_mode": _capture(
            "single_trigger_mode", lambda: scope.single_trigger_mode
        ),
        "trigger_holdoff": _capture("trigger_holdoff", lambda: scope.trigger_holdoff),
        "trigger_configuration": _capture(
            "trigger_configuration", lambda: scope.read_trigger_configuration()
        ),
        "raw_queries": {
            "trigger_status": _capture(
                "raw trigger status", lambda: scope.query(":TRIGger:STATUS?")
            ),
            "trigger_type": _capture(
                "raw trigger type", lambda: scope.query(":TRIGger:TYPE?")
            ),
            "single_mode": _capture(
                "raw single mode", lambda: scope.query(":TRIGger:SINGle:MODE?")
            ),
            "sweep": _capture(
                "raw trigger sweep", lambda: scope.query(":TRIGger:SINGle:SWEEp?")
            ),
        },
    }
    mode = state["single_trigger_mode"]
    mode_name = (
        mode["value"]["name"] if mode.get("ok") and isinstance(mode.get("value"), dict) else None
    )
    if mode_name == "edge":
        state["edge"] = {
            "source": _capture("trigger_source", lambda: scope.trigger_source),
            "coupling": _capture("trigger_coupling", lambda: scope.trigger_coupling),
            "slope": _capture("trigger_slope", lambda: scope.trigger_slope),
            "level": _capture("trigger_level", lambda: scope.trigger_level),
            "raw_source": _capture(
                "raw edge source", lambda: scope.query(":TRIGger:SINGle:EDGE:SOURce?")
            ),
            "raw_coupling": _capture(
                "raw edge coupling",
                lambda: scope.query(":TRIGger:SINGle:EDGE:COUPling?"),
            ),
            "raw_slope": _capture(
                "raw edge slope", lambda: scope.query(":TRIGger:SINGle:EDGE:SLOPe?")
            ),
            "raw_level": _capture(
                "raw edge level", lambda: scope.query(":TRIGger:SINGle:EDGE:LEVel?")
            ),
        }
    if mode_name == "video":
        state["video"] = {
            "source": _capture(
                "video_trigger_source", lambda: scope.video_trigger_source
            ),
            "standard": _capture(
                "video_trigger_standard", lambda: scope.video_trigger_standard
            ),
            "sync": _capture("video_trigger_sync", lambda: scope.video_trigger_sync),
            "line_number": _capture(
                "video_trigger_line_number", lambda: scope.video_trigger_line_number
            ),
        }
    return state


def build_arg_parser():
    parser = argparse.ArgumentParser(description="Dump OWON DOS1104 scope state.")
    parser.add_argument("--scope-vid", default="0x5345")
    parser.add_argument("--scope-pid", default="0x1234")
    parser.add_argument("--timeout-s", type=float, default=2.0)
    parser.add_argument("--settle-s", type=float, default=0.1)
    parser.add_argument("--artifact-root", default="doc/examples/artifacts")
    parser.add_argument("--label", default="owon_scope_state_dump")
    parser.add_argument("--include-screen-metadata", action="store_true")
    parser.add_argument("--include-bmp", action="store_true")
    parser.add_argument(
        "--include-deep-memory-metadata",
        action="store_true",
        help="Probe undocumented experimental deep-memory metadata command family.",
    )
    return parser


def main():
    args = build_arg_parser().parse_args()
    out_dir = _artifact_dir(args.artifact_root, args.label)
    out_dir.mkdir(parents=True, exist_ok=True)

    _progress(f"opening scope on {args.scope_vid}:{args.scope_pid}")
    scope = ik.owon.OWONSDS1104.open_usb(
        vid=int(args.scope_vid, 0),
        pid=int(args.scope_pid, 0),
        timeout=args.timeout_s * u.second,
        enable_scpi=False,
        ignore_scpi_failure=True,
        settle_time=args.settle_s,
    )
    try:
        _progress("capturing identity, acquisition, trigger, and channel state")
        payload = {
            "timestamp": _timestamp().isoformat(timespec="seconds"),
            "scope_vid": args.scope_vid,
            "scope_pid": args.scope_pid,
            "identity": _capture("name", lambda: scope.name),
            "acquisition": {
                "timebase_scale": _capture("timebase_scale", lambda: scope.timebase_scale),
                "horizontal_offset": _capture(
                    "horizontal_offset", lambda: scope.horizontal_offset
                ),
                "memory_depth": _capture("memory_depth", lambda: scope.memory_depth),
                "acquire_mode": _capture("acquire_mode", lambda: scope.acquire_mode),
                "acquire_averages": _capture(
                    "acquire_averages", lambda: scope.acquire_averages
                ),
                "measurement_display_enabled": _capture(
                    "measurement_display_enabled",
                    lambda: scope.measurement_display_enabled,
                ),
            },
            "trigger": _trigger_state(scope),
            "channels": {f"CH{index}": _channel_state(scope, index) for index in range(1, 5)},
        }

        if args.include_screen_metadata:
            _progress("capturing screen waveform metadata")
            payload["screen_waveform_metadata"] = _capture(
                "screen_waveform_metadata", lambda: scope.read_waveform_metadata()
            )

        if args.include_deep_memory_metadata:
            _progress("capturing deep-memory metadata")
            payload["deep_memory_metadata"] = _capture(
                "deep_memory_metadata", lambda: scope.read_deep_memory_metadata()
            )

        if args.include_bmp:
            _progress("capturing BMP screenshot")
            try:
                bmp_path = out_dir / "scope_screen.bmp"
                bmp_path.write_bytes(scope.read_screen_bmp())
                payload["bmp_path"] = str(bmp_path)
            except Exception as exc:  # pragma: no cover - bench-only path
                payload["bmp_path"] = {"error": f"{type(exc).__name__}: {exc}"}
    finally:
        _progress("closing scope")
        scope.close()

    json_path = out_dir / "scope_state.json"
    _progress(f"writing {json_path}")
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json_path)


if __name__ == "__main__":
    main()
