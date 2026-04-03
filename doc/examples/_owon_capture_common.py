#!/usr/bin/env python
"""
Shared helpers for OWON DOS1104 example capture scripts.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any
import time

import serial

import instruments as ik
import instruments.owon.sds1104 as owon_sds1104
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


def _format_token(value, base_unit, units):
    quantity = u.Quantity(value, base_unit) if not hasattr(value, "to") else value
    quantity = quantity.to(base_unit)
    for scale, suffix in units:
        scaled = quantity.to(scale).magnitude
        if abs(scaled) >= 1 or suffix == units[-1][1]:
            text = f"{scaled:.12f}".rstrip("0").rstrip(".")
            if text == "-0":
                text = "0"
            return f"{text}{suffix}"
    raise ValueError(f"Could not format token for {value!r}")


def _format_time_token(value):
    return _format_token(
        value,
        u.second,
        [
            (u.microsecond, "us"),
            (u.millisecond, "ms"),
            (u.second, "s"),
        ],
    )


def _format_voltage_token(value):
    return _format_token(
        value,
        u.volt,
        [
            (u.millivolt, "mV"),
            (u.volt, "V"),
        ],
    )


@dataclass
class WaveformSummary:
    channel: int
    sample_count: int
    time_start_s: float
    time_end_s: float
    voltage_min_v: float
    voltage_max_v: float
    voltage_pp_v: float
    csv_path: str


@dataclass
class RawWaveformSummary:
    channel: int
    sample_count: int
    raw_min: int
    raw_max: int
    raw_first_16: list[int]
    metadata_scale: str
    metadata_probe: str
    metadata_offset: Any


@dataclass
class TraceContext:
    scpi_trace_path: str | None
    state_trace_path: str | None
    state_probe_style: str = "full"
    state_seq: int = 0


def _format_sample_rate_text(x_values):
    if len(x_values) < 2:
        return "unknown"
    dt = abs(x_values[1] - x_values[0])
    if dt <= 0:
        return "unknown"
    sample_rate = 1.0 / dt

    def _fmt(value):
        return f"{value:.6f}".rstrip("0").rstrip(".")

    if sample_rate >= 0.9995e9:
        return f"{_fmt(sample_rate / 1e9)}GS/s"
    if sample_rate >= 0.9995e6:
        return f"{_fmt(sample_rate / 1e6)}MS/s"
    if sample_rate >= 0.9995e3:
        return f"{_fmt(sample_rate / 1e3)}kS/s"
    return f"{_fmt(sample_rate)}S/s"


def _write_jsonl(path, payload):
    if path is None:
        return
    with Path(path).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=True) + "\n")


def _make_trace_context(out_dir, args):
    trace_root = Path(args.trace_dir) / out_dir.name if args.trace_dir else out_dir
    trace_root.mkdir(parents=True, exist_ok=True)
    return TraceContext(
        scpi_trace_path=(
            str(trace_root / "scpi_trace.jsonl") if args.trace_scpi else None
        ),
        state_trace_path=(
            str(trace_root / "state_trace.jsonl") if args.trace_state else None
        ),
        state_probe_style=args.state_probe_style,
    )


def _metadata_sample_rate_text(metadata):
    sample = metadata.get("SAMPLE") if isinstance(metadata, dict) else None
    if not isinstance(sample, dict):
        return None
    raw = sample.get("SAMPLERATE")
    if raw in {None, ""}:
        return None
    return _clean_reply(str(raw)).replace("(", "").replace(")", "")


def _open_scope(args):
    deadline = time.monotonic() + args.scope_open_retry_s
    last_exc = None
    while time.monotonic() < deadline:
        try:
            strict_open = bool(getattr(args, "strict_open_scpi", False))
            return ik.owon.OWONSDS1104.open_usb(
                vid=int(args.scope_vid, 0),
                pid=int(args.scope_pid, 0),
                timeout=args.scope_timeout_s * u.second,
                enable_scpi=(args.enable_scpi or strict_open),
                ignore_scpi_failure=not strict_open,
                settle_time=args.scope_settle_s,
            )
        except Exception as exc:  # pragma: no cover - bench retry path
            last_exc = exc
            time.sleep(0.5)
    raise RuntimeError(f"Scope open failed: {last_exc}")


def _open_serial(args):
    return serial.Serial(
        port=args.esp_port,
        baudrate=args.esp_baud,
        timeout=0.2,
        write_timeout=0.2,
    )


def _configure_esp_from_args(args):
    with _open_serial(args) as port:
        return _configure_esp(port, args)


def _serial_write_line(port, line):
    port.write((line + "\n").encode("utf-8"))
    port.flush()


def _serial_drain(port, duration_s):
    deadline = time.monotonic() + max(duration_s, 0.0)
    lines = []
    while time.monotonic() < deadline:
        raw = port.readline()
        if raw:
            lines.append(raw.decode("utf-8", errors="replace").rstrip())
        else:
            time.sleep(0.01)
    return lines


def _configure_esp(port, args):
    _serial_write_line(port, "status")
    if args.pulse_mode == "burst":
        _serial_write_line(port, "burst")
    else:
        _serial_write_line(port, f"single {int(args.pulse_width_us)}")
    _serial_write_line(port, f"gap {int(args.pulse_gap_us)}")
    _serial_write_line(port, f"frame {int(args.pulse_frame_us)}")
    _serial_write_line(port, f"half {int(args.slope_half_period_us)}")
    return _serial_drain(port, 0.5)


def _capture_screenshot(scope, out_dir, args):
    bmp_path = out_dir / f"{args.profile}_{args.arm}_scope_screen.bmp"
    bmp_path.write_bytes(scope.read_screen_bmp())
    return bmp_path


def _capture_waveform(scope, channel, out_dir):
    x_axis, y_axis = scope.read_waveform(channel)
    csv_path = out_dir / f"ch{channel}_waveform.csv"

    x_values = [float(value) for value in x_axis]
    y_values = [float(value) for value in y_axis]

    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["time_s", "voltage_v"])
        writer.writerows(zip(x_values, y_values, strict=True))

    v_min = min(y_values)
    v_max = max(y_values)
    return WaveformSummary(
        channel=channel,
        sample_count=len(y_values),
        time_start_s=x_values[0],
        time_end_s=x_values[-1],
        voltage_min_v=v_min,
        voltage_max_v=v_max,
        voltage_pp_v=v_max - v_min,
        csv_path=str(csv_path),
    )


def _capture_screen_channel_raw(scope, metadata, channel, out_dir):
    point_count = scope._waveform_point_count(metadata)  # pylint: disable=protected-access
    payload = scope._binary_query_exact(  # pylint: disable=protected-access
        f":DATA:WAVE:SCREen:CH{channel}?", 4 + 2 * point_count
    )
    raw_adc = owon_sds1104._parse_waveform_adc(  # pylint: disable=protected-access
        owon_sds1104._strip_packet_prefix(payload, f"screen waveform CH{channel}"),  # pylint: disable=protected-access
        f"screen waveform CH{channel}",
    )
    x_axis = scope._waveform_time_axis(metadata, point_count)  # pylint: disable=protected-access
    y_axis = scope._waveform_voltage_axis(metadata, channel, raw_adc)  # pylint: disable=protected-access
    csv_path = out_dir / f"ch{channel}_waveform.csv"

    x_values = [float(value) for value in x_axis]
    y_values = [float(value) for value in y_axis]

    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["time_s", "voltage_v"])
        writer.writerows(zip(x_values, y_values, strict=True))

    v_min = min(y_values)
    v_max = max(y_values)
    summary = WaveformSummary(
        channel=channel,
        sample_count=len(y_values),
        time_start_s=x_values[0],
        time_end_s=x_values[-1],
        voltage_min_v=v_min,
        voltage_max_v=v_max,
        voltage_pp_v=v_max - v_min,
        csv_path=str(csv_path),
    )
    return summary, {"x": x_values, "y": y_values}


def _capture_depmem_all_summary_and_series(scope, out_dir):
    raw_payload = scope.read_deep_memory_all_raw()
    raw_path = out_dir / "depmem_all_raw.bin"
    raw_path.write_bytes(raw_payload)
    capture = scope._parse_deep_memory_all_payload(raw_payload)  # pylint: disable=protected-access
    summary = {
        "metadata": {
            "timebase_scale": capture.metadata.get("TIMEBASE", {}).get("SCALE"),
            "hoffset": capture.metadata.get("TIMEBASE", {}).get("HOFFSET"),
            "datalen": capture.metadata.get("SAMPLE", {}).get("DATALEN"),
            "sample_rate": capture.metadata.get("SAMPLE", {}).get("SAMPLERATE"),
            "depmem": capture.metadata.get("SAMPLE", {}).get("DEPMEM"),
            "screenoffset": capture.metadata.get("SAMPLE", {}).get("SCREENOFFSET"),
            "runstatus": capture.metadata.get("RUNSTATUS"),
        },
        "channels": {
            f"CH{channel}": {
                "samples": len(raw_values),
                "raw_min": int(min(raw_values)),
                "raw_max": int(max(raw_values)),
                "first_16": [int(value) for value in list(raw_values)[:16]],
            }
            for channel, raw_values in capture.raw_channels.items()
        },
    }
    summary_path = out_dir / "depmem_all_summary.json"
    _safe_json_write(summary_path, summary)

    series = {}
    for channel, raw_values in capture.raw_channels.items():
        x_axis = scope._waveform_time_axis(capture.metadata, len(raw_values))  # pylint: disable=protected-access
        y_axis = scope._waveform_voltage_axis(capture.metadata, channel, raw_values)  # pylint: disable=protected-access
        series[channel] = {
            "x": [float(value) for value in x_axis],
            "y": [float(value) for value in y_axis],
        }
    return summary, summary_path, raw_path, series


def _safe_json_write(path, payload):
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _build_scope_html_data_from_series(
    args,
    scope_state,
    waveform_data,
    memory_depth_text=None,
    sample_rate_text=None,
):
    first_channel = next(iter(waveform_data.values()), {"x": [0.0, 1.0], "y": []})
    time_window_s = None
    if len(first_channel["x"]) >= 2:
        time_window_s = abs(float(first_channel["x"][-1]) - float(first_channel["x"][0]))
    if sample_rate_text is None:
        sample_rate_text = _format_sample_rate_text(first_channel["x"])
    if memory_depth_text is None:
        memory_depth_text = str(len(first_channel["y"])) if first_channel["y"] else "unknown"

    status_text = str(scope_state.get("trigger_status", "STOP"))
    if "." in status_text:
        status_text = status_text.split(".")[-1].upper()

    if args.profile == "edge":
        trigger_source = args.edge_source.upper()
        trigger_coupling = args.edge_coupling.upper()
        trigger_edge = "falling" if args.edge_slope.lower() == "fall" else "rising"
    elif args.profile == "pulse":
        trigger_source = args.pulse_source.upper()
        trigger_coupling = args.pulse_coupling.upper()
        trigger_edge = "falling" if args.pulse_dir.upper() == "NEG" else "rising"
    else:
        trigger_source = args.slope_source.upper()
        trigger_coupling = "DC"
        trigger_edge = "falling" if args.slope_edge.upper() == "NEG" else "rising"

    return {
        "meta": {
            "status": status_text.title() if status_text == "STOP" else status_text,
            "timebase_s_div": args.timebase_s_div,
            "time_window_s": time_window_s,
            "sample_rate_text": sample_rate_text,
            "memory_depth_text": memory_depth_text,
        },
        "trigger": {
            "source": trigger_source,
            "coupling": trigger_coupling,
            "edge": trigger_edge,
            "level_v": args.trigger_level_v,
            "horizontal_pos_s": 0.0,
        },
        "channels": {
            "CH1": {
                "visible": 1 in args.capture_channels,
                "volts_per_div": args.ch1_scale_v_div,
                "position_div": args.ch1_position_div,
                "color": "#ffff00",
                "data": waveform_data.get(1, {}).get("y", []),
                "time_s": waveform_data.get(1, {}).get("x", []),
            },
            "CH2": {
                "visible": 2 in args.capture_channels,
                "volts_per_div": args.ch2_scale_v_div,
                "position_div": args.ch2_position_div,
                "color": "#00ffff",
                "data": waveform_data.get(2, {}).get("y", []),
                "time_s": waveform_data.get(2, {}).get("x", []),
            },
            "CH3": {
                "visible": 3 in args.capture_channels,
                "volts_per_div": args.ch3_scale_v_div,
                "position_div": args.ch3_position_div,
                "color": "#ff8800",
                "data": waveform_data.get(3, {}).get("y", []),
                "time_s": waveform_data.get(3, {}).get("x", []),
            },
        },
    }


def _build_scope_html_data(args, scope_state, waveforms):
    waveform_data = {}
    for summary in waveforms:
        with Path(summary.csv_path).open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        waveform_data[summary.channel] = {
            "x": [float(row["time_s"]) for row in rows],
            "y": [float(row["voltage_v"]) for row in rows],
        }
    return _build_scope_html_data_from_series(args, scope_state, waveform_data)


def _render_scope_html_with_data(out_dir, scope_data, stem):
    template_path = Path(__file__).resolve().parent / "scope.html"
    template = template_path.read_text(encoding="utf-8")
    template = template.replace("scope_view_data.js", f"{stem}_data.js")
    template = template.replace("scope_view.json", f"{stem}.json")
    html_path = out_dir / f"{stem}.html"
    json_path = out_dir / f"{stem}.json"
    js_path = out_dir / f"{stem}_data.js"
    html_path.write_text(template, encoding="utf-8")
    json_path.write_text(json.dumps(scope_data, indent=2), encoding="utf-8")
    js_path.write_text(
        "window.__SCOPE_DATA__ = " + json.dumps(scope_data) + ";\n", encoding="utf-8"
    )
    return html_path, json_path


def _render_scope_html(out_dir, args, scope_state, waveforms, sample_rate_text=None):
    scope_data = _build_scope_html_data(args, scope_state, waveforms)
    if sample_rate_text is not None:
        scope_data["meta"]["sample_rate_text"] = sample_rate_text
    return _render_scope_html_with_data(out_dir, scope_data, "scope_view")


def _max_abs_delta(values_a, values_b):
    if not values_a or not values_b:
        return 0.0
    return max(abs(float(a) - float(b)) for a, b in zip(values_a, values_b, strict=True))


def _mean_abs_delta(values_a, values_b):
    if not values_a or not values_b:
        return 0.0
    deltas = [abs(float(a) - float(b)) for a, b in zip(values_a, values_b, strict=True)]
    return sum(deltas) / len(deltas)


def _align_waveform_series(series_a, series_b):
    x_a = list(series_a["x"])
    y_a = list(series_a["y"])
    x_b = list(series_b["x"])
    y_b = list(series_b["y"])
    if len(y_a) == len(y_b):
        return {
            "alignment": "exact",
            "x_a": x_a,
            "y_a": y_a,
            "x_b": x_b,
            "y_b": y_b,
        }

    if abs(len(y_a) - len(y_b)) == 1:
        if len(y_a) > len(y_b):
            candidates = [
                ("drop_first_a", x_a[1:], y_a[1:], x_b, y_b),
                ("drop_last_a", x_a[:-1], y_a[:-1], x_b, y_b),
            ]
        else:
            candidates = [
                ("drop_first_b", x_a, y_a, x_b[1:], y_b[1:]),
                ("drop_last_b", x_a, y_a, x_b[:-1], y_b[:-1]),
            ]
        best = min(
            candidates,
            key=lambda item: (
                _max_abs_delta(item[2], item[4]),
                _mean_abs_delta(item[2], item[4]),
            ),
        )
        return {
            "alignment": best[0],
            "x_a": list(best[1]),
            "y_a": list(best[2]),
            "x_b": list(best[3]),
            "y_b": list(best[4]),
        }

    shared = min(len(y_a), len(y_b))
    return {
        "alignment": f"prefix_trim_to_{shared}",
        "x_a": x_a[:shared],
        "y_a": y_a[:shared],
        "x_b": x_b[:shared],
        "y_b": y_b[:shared],
    }


def _compare_waveform_series(name_a, series_a, name_b, series_b):
    aligned = _align_waveform_series(series_a, series_b)
    delta_samples = [
        abs(float(a) - float(b))
        for a, b in zip(aligned["y_a"], aligned["y_b"], strict=True)
    ]
    return {
        "series_a": name_a,
        "series_b": name_b,
        "count_a": len(series_a["y"]),
        "count_b": len(series_b["y"]),
        "aligned_count": len(aligned["y_a"]),
        "alignment": aligned["alignment"],
        "max_abs_voltage_delta_v": max(delta_samples) if delta_samples else 0.0,
        "mean_abs_voltage_delta_v": sum(delta_samples) / len(delta_samples)
        if delta_samples
        else 0.0,
        "diff_sample_count": sum(1 for delta in delta_samples if delta > 1e-9),
        "max_abs_time_delta_s": _max_abs_delta(aligned["x_a"], aligned["x_b"]),
        "voltage_pp_a_v": (
            max(series_a["y"]) - min(series_a["y"]) if series_a["y"] else 0.0
        ),
        "voltage_pp_b_v": (
            max(series_b["y"]) - min(series_b["y"]) if series_b["y"] else 0.0
        ),
    }


def _render_waveform_comparison_html(out_dir, comparison):
    html_path = out_dir / "waveform_comparison.html"
    lines = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="UTF-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
        "<title>Waveform Comparison</title>",
        "<style>",
        "body { background: #141414; color: #eee; font-family: Consolas, 'Courier New', monospace; margin: 0; padding: 24px; }",
        "h1, h2 { margin: 0 0 12px; }",
        "h2 { margin-top: 28px; }",
        ".note { color: #bbb; margin-bottom: 20px; }",
        ".image { margin: 16px 0 24px; }",
        "img { max-width: 100%; border: 1px solid #444; }",
        "table { width: 100%; border-collapse: collapse; margin: 12px 0 24px; }",
        "th, td { border: 1px solid #333; padding: 8px 10px; text-align: left; }",
        "th { background: #1e1e1e; }",
        ".views { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }",
        ".card { background: #0c0c0c; border: 1px solid #333; padding: 12px; }",
        "iframe { width: 100%; height: 620px; border: 1px solid #333; background: #000; }",
        "a { color: #7cc7ff; }",
        "</style>",
        "</head>",
        "<body>",
        "<h1>Waveform Comparison</h1>",
        '<p class="note">BMP is the ground-truth screen capture. The HTML views below render the public waveform APIs grouped by acquisition family.</p>',
    ]
    if comparison.get("bmp_name"):
        lines.extend(
            [
                "<h2>Reference BMP</h2>",
                f'<div class="image"><img src="{comparison["bmp_name"]}" alt="Scope BMP"></div>',
            ]
        )

    lines.extend(
        [
            "<h2>Numeric Comparison</h2>",
            "<table>",
            "<thead><tr><th>Family</th><th>Channel</th><th>A</th><th>B</th><th>Counts</th><th>Alignment</th><th>Mean |dV|</th><th>Max |dV|</th><th>Diff samples</th><th>Max |dt|</th></tr></thead>",
            "<tbody>",
        ]
    )
    for family, channels in comparison.get("families", {}).items():
        for channel_name, metrics in channels.items():
            lines.append(
                "<tr>"
                f"<td>{family}</td>"
                f"<td>{channel_name}</td>"
                f"<td>{metrics['series_a']}</td>"
                f"<td>{metrics['series_b']}</td>"
                f"<td>{metrics['count_a']} vs {metrics['count_b']} (shared {metrics['aligned_count']})</td>"
                f"<td>{metrics['alignment']}</td>"
                f"<td>{metrics['mean_abs_voltage_delta_v']:.6g} V</td>"
                f"<td>{metrics['max_abs_voltage_delta_v']:.6g} V</td>"
                f"<td>{metrics['diff_sample_count']}</td>"
                f"<td>{metrics['max_abs_time_delta_s']:.6g} s</td>"
                "</tr>"
            )
    lines.extend(["</tbody>", "</table>"])

    views = comparison.get("views", [])
    if views:
        lines.extend(["<h2>Rendered Views</h2>", '<div class="views">'])
        for view in views:
            lines.extend(
                [
                    '<div class="card">',
                    f"<h3>{view['title']}</h3>",
                    f'<p><a href="{view["html_name"]}">Open HTML</a> | <a href="{view["json_name"]}">Open JSON</a></p>',
                    f'<iframe src="{view["html_name"]}" loading="lazy"></iframe>',
                    "</div>",
                ]
            )
        lines.append("</div>")

    lines.extend(["</body>", "</html>"])
    html_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return html_path
