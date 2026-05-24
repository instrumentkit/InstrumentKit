#!/usr/bin/env python
"""
Run a conservative OWON / HANMATEK DOS1104 "safe commands" smoke.

This helper intentionally avoids known-toxic sweep mutations and trigger arming
experiments. It focuses on:

- read-only state queries
- screen capture / screen waveform reads
- deep-memory reads only when the effective sweep is AUTO

Artifacts:
- safe_scope_smoke.json
- safe_scope_smoke.md
- scpi_trace.jsonl
- scope_screen.bmp
- screen_waveform_metadata.json
- depmem_all_raw.bin (when read succeeds)
- deep_memory_metadata.json only when explicitly requested
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

import instruments as ik
from instruments.units import ureg as u


def _timestamp():
    return datetime.now(timezone.utc)


def _artifact_dir(root, label, timestamp=None):
    timestamp = _timestamp() if timestamp is None else timestamp
    date_dir = Path(root) / timestamp.strftime("%Y%m%d")
    return date_dir / f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{label}"


def _clean_reply(text):
    cleaned = str(text).strip()
    if cleaned.endswith("->"):
        cleaned = cleaned[:-2].rstrip()
    return cleaned


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
        return {"label": label, "ok": True, "value": _jsonable(fn())}
    except Exception as exc:  # pragma: no cover - bench-only path
        return {"label": label, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def _waveform_summary(x_axis, y_axis):
    return {
        "samples": len(x_axis),
        "t_start": float(x_axis[0]) if len(x_axis) else None,
        "t_end": float(x_axis[-1]) if len(x_axis) else None,
        "v_min": float(min(y_axis)) if len(y_axis) else None,
        "v_max": float(max(y_axis)) if len(y_axis) else None,
        "v_pp": (float(max(y_axis) - min(y_axis)) if len(y_axis) else None),
    }


def _deep_bundle_summary(bundle):
    raw_channels = getattr(bundle, "raw_channels", {})
    return {
        "channel_count": len(raw_channels),
        "channels": {
            f"CH{index}": {
                "samples": len(samples),
                "raw_min": int(min(samples)) if len(samples) else None,
                "raw_max": int(max(samples)) if len(samples) else None,
            }
            for index, samples in raw_channels.items()
        },
        "metadata_keys": sorted(getattr(bundle, "metadata", {}).keys()),
    }


def _capture_deepmem_all(scope, out_dir):
    raw_payload = scope.read_deep_memory_all_raw()
    raw_path = out_dir / "depmem_all_raw.bin"
    raw_path.write_bytes(raw_payload)
    capture = scope._parse_deep_memory_all_payload(
        raw_payload
    )  # pylint: disable=protected-access
    return {
        "raw_path": str(raw_path),
        "summary": _deep_bundle_summary(capture),
    }


def _channel_probe(scope, channel_index, property_name):
    channel = scope.channel[channel_index - 1]
    return getattr(channel, property_name)


def _add_result(results, label, fn):
    result = _capture(label, fn)
    results.append(result)
    return result


def _add_skip(results, label, reason):
    results.append({"label": label, "ok": False, "skipped": True, "reason": reason})


def _compact_baseline_snapshot(scope):
    return {
        "trigger_status": _jsonable(scope.trigger_status),
        "raw_sweep": _clean_reply(scope.query(":TRIGger:SINGle:SWEEp?")),
        "raw_edge_level": _clean_reply(scope.query(":TRIGger:SINGle:EDGE:LEVel?")),
        "timebase": _clean_reply(scope.query(":HORIzontal:Scale?")),
        "memory_depth": _clean_reply(scope.query(":ACQUIRE:DEPMEM?")),
    }


def normalize_auto_sweep_if_needed(scope):
    """
    Ensures the effective trigger sweep is AUTO.

    :return: Tuple ``(changed, original_sweep, effective_sweep)``.
    """
    original = scope.trigger_sweep
    changed = False
    if original != scope.TriggerSweep.auto:
        scope.trigger_sweep = scope.TriggerSweep.auto
        changed = True
    return changed, _jsonable(original), _jsonable(scope.trigger_sweep)


def normalize_safe_auto_baseline(scope):
    """
    Normalizes to the conservative AUTO baseline and returns a compact snapshot.
    """
    changed, original_sweep, effective_sweep = normalize_auto_sweep_if_needed(scope)
    return {
        "changed_sweep": changed,
        "original_sweep": original_sweep,
        "effective_sweep": effective_sweep,
        "snapshot": _compact_baseline_snapshot(scope),
    }


def _build_parser():
    parser = argparse.ArgumentParser(description="Run a conservative DOS1104 smoke.")
    parser.add_argument("--scope-vid", default="0x5345")
    parser.add_argument("--scope-pid", default="0x1234")
    parser.add_argument("--timeout-s", type=float, default=2.0)
    parser.add_argument("--settle-s", type=float, default=0.1)
    parser.add_argument("--artifact-root", default="doc/examples/artifacts")
    parser.add_argument("--label", default="safe_scope_smoke")
    parser.add_argument("--normalize-auto-sweep", action="store_true")
    parser.add_argument("--trace", action="store_true", default=True)
    parser.add_argument(
        "--include-experimental-deep-path",
        action="store_true",
        help="Also probe undocumented deep-memory HEAD/CH commands.",
    )
    return parser


def main():
    args = _build_parser().parse_args()
    out_dir = _artifact_dir(args.artifact_root, args.label)
    out_dir.mkdir(parents=True, exist_ok=True)
    trace_path = out_dir / "scpi_trace.jsonl"

    scope = ik.owon.OWONSDS1104.open_usb(
        vid=int(args.scope_vid, 0),
        pid=int(args.scope_pid, 0),
        timeout=args.timeout_s * u.second,
        enable_scpi=False,
        ignore_scpi_failure=True,
        settle_time=args.settle_s,
    )
    results = []
    original_sweep = None
    effective_sweep = None
    try:
        if args.trace:
            scope.enable_trace(trace_path)

        name_result = _add_result(results, "name", lambda: scope.name)
        _add_result(results, "trigger_status", lambda: scope.trigger_status)
        _add_result(results, "trigger_type", lambda: scope.trigger_type)
        _add_result(results, "single_trigger_mode", lambda: scope.single_trigger_mode)
        sweep_result = _add_result(
            results, "trigger_sweep", lambda: scope.trigger_sweep
        )
        if sweep_result.get("ok"):
            original_sweep = sweep_result["value"]
            effective_sweep = original_sweep

        if (
            args.normalize_auto_sweep
            and sweep_result.get("ok")
            and sweep_result["value"]["value"] != "AUTO"
        ):
            try:
                baseline = normalize_safe_auto_baseline(scope)
                effective_sweep = baseline["effective_sweep"]
                results.append(
                    {
                        "label": "set trigger_sweep = AUTO",
                        "ok": True,
                        "value": effective_sweep,
                    }
                )
            except Exception as exc:  # pragma: no cover - bench-only path
                results.append(
                    {
                        "label": "set trigger_sweep = AUTO",
                        "ok": False,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )

        _add_result(results, "trigger_holdoff", lambda: scope.trigger_holdoff)
        _add_result(results, "timebase_scale", lambda: scope.timebase_scale)
        _add_result(results, "horizontal_offset", lambda: scope.horizontal_offset)
        _add_result(results, "memory_depth", lambda: scope.memory_depth)
        _add_result(results, "acquire_mode", lambda: scope.acquire_mode)
        _add_result(results, "acquire_averages", lambda: scope.acquire_averages)
        _add_result(
            results,
            "measurement_display_enabled",
            lambda: scope.measurement_display_enabled,
        )
        _add_result(
            results,
            "read_trigger_configuration",
            lambda: scope.read_trigger_configuration(),
        )

        for channel in range(1, 5):
            for property_name in (
                "display",
                "coupling",
                "probe_attenuation",
                "scale",
                "offset",
                "position",
                "invert",
            ):
                _add_result(
                    results,
                    f"CH{channel}.{property_name}",
                    lambda channel=channel, property_name=property_name: _channel_probe(
                        scope,
                        channel,
                        property_name,
                    ),
                )

        def _read_bmp():
            payload = scope.read_screen_bmp()
            bmp_path = out_dir / "scope_screen.bmp"
            bmp_path.write_bytes(payload)
            return {"bytes": len(payload), "path": str(bmp_path)}

        _add_result(results, "read_screen_bmp", _read_bmp)

        def _read_screen_metadata():
            metadata = scope.read_waveform_metadata()
            metadata_path = out_dir / "screen_waveform_metadata.json"
            metadata_path.write_text(
                json.dumps(_jsonable(metadata), indent=2), encoding="utf-8"
            )
            return metadata

        _add_result(results, "read_waveform_metadata", _read_screen_metadata)

        _add_result(
            results,
            "read_waveform(1)",
            lambda: _waveform_summary(*scope.read_waveform(1)),
        )
        _add_result(
            results,
            "channel[0].read_waveform()",
            lambda: _waveform_summary(*scope.channel[0].read_waveform()),
        )
        _add_result(
            results,
            "read_waveform(2)",
            lambda: _waveform_summary(*scope.read_waveform(2)),
        )
        _add_result(
            results,
            "channel[1].read_waveform()",
            lambda: _waveform_summary(*scope.channel[1].read_waveform()),
        )

        effective_value = None
        if isinstance(effective_sweep, dict):
            effective_value = effective_sweep.get("value")

        if effective_value == "AUTO":
            _add_result(
                results,
                "read_deep_memory_all",
                lambda: _capture_deepmem_all(scope, out_dir),
            )
            if args.include_experimental_deep_path:

                def _read_deep_metadata():
                    metadata = scope.read_deep_memory_metadata()
                    metadata_path = out_dir / "deep_memory_metadata.json"
                    metadata_path.write_text(
                        json.dumps(_jsonable(metadata), indent=2), encoding="utf-8"
                    )
                    return metadata

                _add_result(results, "read_deep_memory_metadata", _read_deep_metadata)
                _add_result(
                    results,
                    "read_deep_memory_channel(1)",
                    lambda: _waveform_summary(*scope.read_deep_memory_channel(1)),
                )
        else:
            skip_reason = (
                "deep-memory reads are only classified safe when the effective "
                "trigger sweep is AUTO"
            )
            _add_skip(results, "read_deep_memory_all", skip_reason)
            if args.include_experimental_deep_path:
                _add_skip(results, "read_deep_memory_metadata", skip_reason)
                _add_skip(results, "read_deep_memory_channel(1)", skip_reason)

        _add_result(results, "final_name", lambda: scope.name)
        _add_result(results, "final_trigger_status", lambda: scope.trigger_status)
        _add_result(results, "final_trigger_sweep", lambda: scope.trigger_sweep)
    finally:
        scope.close()

    json_path = out_dir / "safe_scope_smoke.json"
    md_path = out_dir / "safe_scope_smoke.md"
    payload = {
        "timestamp": _timestamp().isoformat(timespec="seconds"),
        "scope_vid": args.scope_vid,
        "scope_pid": args.scope_pid,
        "trace_path": str(trace_path) if args.trace else None,
        "original_trigger_sweep": original_sweep,
        "effective_trigger_sweep": effective_sweep,
        "results": results,
        "not_run": [
            {
                "label": "trigger_sweep = NORMal",
                "reason": "known bench-toxic for deep-memory follow-up reads",
            },
            {
                "label": "trigger_sweep = SINGle",
                "reason": "known bench-toxic for deep-memory follow-up reads",
            },
            {
                "label": "single() / arm_single() / freeze_acquisition()",
                "reason": "state-changing trigger experiments are intentionally excluded from the safe smoke",
            },
        ],
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# DOS1104 Safe Scope Smoke",
        "",
        f"- Timestamp: `{payload['timestamp']}`",
        f"- Original sweep: `{original_sweep}`",
        f"- Effective sweep: `{effective_sweep}`",
    ]
    if args.trace:
        lines.append(f"- Trace: `{trace_path.name}`")
    lines.extend(
        [
            "",
            "| Probe | OK | Result |",
            "| --- | --- | --- |",
        ]
    )
    for result in results:
        outcome = "`True`" if result.get("ok") else "`False`"
        if result.get("skipped"):
            rendered = json.dumps({"skipped": True, "reason": result["reason"]})
        elif result.get("ok"):
            rendered = json.dumps(result.get("value"), default=str)
        else:
            rendered = json.dumps({"error": result.get("error")})
        lines.append(f"| `{result['label']}` | {outcome} | `{rendered}` |")

    lines.extend(
        [
            "",
            "## Not Run",
            "",
        ]
    )
    for item in payload["not_run"]:
        lines.append(f"- `{item['label']}`: {item['reason']}")

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(md_path)


if __name__ == "__main__":
    main()
