#!/usr/bin/env python
"""
Debug and validation helpers for the OWON ESP32 trigger jig runner.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import time

import usb.core

import instruments as ik
from instruments.units import ureg as u

from _owon_capture_common import (
    RawWaveformSummary,
    _build_scope_html_data_from_series,
    _capture_screenshot,
    _capture_waveform,
    _clean_reply,
    _compare_waveform_series,
    _format_time_token,
    _format_voltage_token,
    _make_trace_context,
    _metadata_sample_rate_text,
    _open_scope,
    _render_scope_html,
    _render_scope_html_with_data,
    _render_waveform_comparison_html,
    _safe_json_write,
    _timestamp,
    _write_jsonl,
)


def _raw_waveform_summary(scope, channel):
    metadata = scope.read_waveform_metadata()
    point_count = scope._waveform_point_count(metadata)  # pylint: disable=protected-access
    payload = scope._binary_query_exact(  # pylint: disable=protected-access
        f":DATA:WAVE:SCREEN:CH{channel}?",
        4 + 2 * point_count,
    )
    raw_adc = ik.owon.sds1104._parse_waveform_adc(  # pylint: disable=protected-access
        ik.owon.sds1104._strip_packet_prefix(payload, f"screen waveform CH{channel}"),
        f"screen waveform CH{channel}",
    )
    raw_list = [int(value) for value in raw_adc]
    channel_meta = metadata["CHANNEL"][channel - 1]
    return RawWaveformSummary(
        channel=channel,
        sample_count=len(raw_list),
        raw_min=min(raw_list),
        raw_max=max(raw_list),
        raw_first_16=raw_list[:16],
        metadata_scale=str(channel_meta.get("SCALE")),
        metadata_probe=str(channel_meta.get("PROBE")),
        metadata_offset=channel_meta.get("OFFSET"),
    ), metadata


def _summarize_numeric_axis(values):
    values = [float(value) for value in values]
    return {
        "count": len(values),
        "min": min(values),
        "max": max(values),
        "pp": max(values) - min(values),
        "first_16": values[:16],
    }


def _capture_waveform_truth(
    scope, out_dir, args, scope_state, capture_channels, deep_first=False
):
    truth = {
        "screen_bmp_path": None,
        "screen_metadata_path": None,
        "screen_metadata": None,
        "screen_waveforms": {},
        "screen_channel_alias_waveforms": {},
        "deep_memory_metadata_path": None,
        "deep_memory_metadata": None,
        "deep_memory_channels": {},
        "deep_memory_bundle": None,
        "errors": [],
    }
    screen_series = {}
    screen_alias_series = {}
    deep_channel_series = {}
    deep_bundle_series = {}
    screen_metadata = None
    deep_metadata = None
    comparison = {
        "bmp_name": None,
        "views": [],
        "families": {},
    }

    try:
        deep_metadata = scope.read_deep_memory_metadata()
        deep_metadata_path = out_dir / "deep_memory_metadata.json"
        _safe_json_write(deep_metadata_path, deep_metadata)
        truth["deep_memory_metadata_path"] = str(deep_metadata_path)
        truth["deep_memory_metadata"] = deep_metadata
    except Exception as exc:
        truth["errors"].append(f"read_deep_memory_metadata: {exc}")
        deep_metadata = None

    for channel in capture_channels:
        try:
            x_axis, y_axis = scope.read_deep_memory_channel(channel)
            x_values = [float(value) for value in x_axis]
            y_values = [float(value) for value in y_axis]
            truth["deep_memory_channels"][f"CH{channel}"] = {
                "time": _summarize_numeric_axis(x_values),
                "voltage": _summarize_numeric_axis(y_values),
            }
            deep_channel_series[channel] = {"x": x_values, "y": y_values}
        except Exception as exc:
            truth["errors"].append(f"read_deep_memory_channel({channel}): {exc}")

    try:
        bundle = scope.read_deep_memory_all()
        truth["deep_memory_bundle"] = {
            "metadata_keys": sorted(bundle.metadata.keys()),
            "raw_channels": {
                f"CH{channel}": {
                    "count": len(raw_values),
                    "min": int(min(raw_values)),
                    "max": int(max(raw_values)),
                    "first_16": [int(value) for value in list(raw_values)[:16]],
                }
                for channel, raw_values in bundle.raw_channels.items()
            },
        }
        converted_channels = {}
        for channel, raw_values in bundle.raw_channels.items():
            x_axis = scope._waveform_time_axis(bundle.metadata, len(raw_values))  # pylint: disable=protected-access
            y_axis = scope._waveform_voltage_axis(bundle.metadata, channel, raw_values)  # pylint: disable=protected-access
            x_values = [float(value) for value in x_axis]
            y_values = [float(value) for value in y_axis]
            converted_channels[f"CH{channel}"] = {
                "time": _summarize_numeric_axis(x_values),
                "voltage": _summarize_numeric_axis(y_values),
            }
            deep_bundle_series[channel] = {"x": x_values, "y": y_values}
        truth["deep_memory_bundle"]["converted_channels"] = converted_channels
    except Exception as exc:
        truth["errors"].append(f"read_deep_memory_all: {exc}")

    if not deep_first:
        bmp_path = out_dir / "waveform_truth_screen.bmp"
        bmp_path.write_bytes(scope.read_screen_bmp())
        truth["screen_bmp_path"] = str(bmp_path)
        comparison["bmp_name"] = bmp_path.name

        try:
            screen_metadata = scope.read_waveform_metadata()
            screen_metadata_path = out_dir / "screen_waveform_metadata.json"
            _safe_json_write(screen_metadata_path, screen_metadata)
            truth["screen_metadata_path"] = str(screen_metadata_path)
            truth["screen_metadata"] = screen_metadata
        except Exception as exc:
            truth["errors"].append(f"read_waveform_metadata: {exc}")
            screen_metadata = None

        for channel in capture_channels:
            try:
                raw_summary, metadata = _raw_waveform_summary(scope, channel)
                truth["screen_waveforms"][f"CH{channel}"] = {
                    "raw_summary": asdict(raw_summary),
                    "metadata_scale": str(metadata["CHANNEL"][channel - 1].get("SCALE")),
                    "metadata_probe": str(metadata["CHANNEL"][channel - 1].get("PROBE")),
                    "metadata_offset": metadata["CHANNEL"][channel - 1].get("OFFSET"),
                }
            except Exception as exc:
                truth["errors"].append(f"raw screen CH{channel}: {exc}")

            try:
                x_axis, y_axis = scope.read_waveform(channel)
                x_values = [float(value) for value in x_axis]
                y_values = [float(value) for value in y_axis]
                truth["screen_waveforms"].setdefault(f"CH{channel}", {})
                truth["screen_waveforms"][f"CH{channel}"]["converted_summary"] = {
                    "time": _summarize_numeric_axis(x_values),
                    "voltage": _summarize_numeric_axis(y_values),
                }
                screen_series[channel] = {"x": x_values, "y": y_values}
            except Exception as exc:
                truth["errors"].append(f"read_waveform({channel}): {exc}")

            try:
                x_axis, y_axis = scope.channel[channel - 1].read_waveform()
                x_values = [float(value) for value in x_axis]
                y_values = [float(value) for value in y_axis]
                truth["screen_channel_alias_waveforms"][f"CH{channel}"] = {
                    "time": _summarize_numeric_axis(x_values),
                    "voltage": _summarize_numeric_axis(y_values),
                }
                screen_alias_series[channel] = {"x": x_values, "y": y_values}
            except Exception as exc:
                truth["errors"].append(f"channel[{channel - 1}].read_waveform(): {exc}")

    truth_path = out_dir / "waveform_truth.json"
    _safe_json_write(truth_path, truth)

    view_specs = [
        (
            "screen_read_waveform_view",
            "Screen `read_waveform(channel)`",
            screen_series,
            screen_metadata,
        ),
        (
            "screen_channel_alias_view",
            "Screen `channel[n].read_waveform()`",
            screen_alias_series,
            screen_metadata,
        ),
        (
            "deep_memory_channel_view",
            "Deep `read_deep_memory_channel(channel)`",
            deep_channel_series,
            deep_metadata,
        ),
        (
            "deep_memory_bundle_view",
            "Deep `read_deep_memory_all()` converted from raw bundle",
            deep_bundle_series,
            deep_metadata,
        ),
    ]
    for stem, title, waveform_data, metadata in view_specs:
        if not waveform_data:
            continue
        first_channel = next(iter(waveform_data.values()))
        scope_data = _build_scope_html_data_from_series(
            args,
            scope_state,
            waveform_data,
            memory_depth_text=str(len(first_channel["y"])),
            sample_rate_text=_metadata_sample_rate_text(metadata),
        )
        html_path, json_path = _render_scope_html_with_data(out_dir, scope_data, stem)
        comparison["views"].append(
            {
                "stem": stem,
                "title": title,
                "html_name": html_path.name,
                "json_name": json_path.name,
            }
        )

    family_map = {
        "screen": (
            "read_waveform(channel)",
            screen_series,
            "channel[n].read_waveform()",
            screen_alias_series,
        ),
        "deep_memory": (
            "read_deep_memory_channel(channel)",
            deep_channel_series,
            "read_deep_memory_all()",
            deep_bundle_series,
        ),
    }
    for family_name, (name_a, series_a, name_b, series_b) in family_map.items():
        channels = {}
        for channel in sorted(set(series_a) & set(series_b)):
            channels[f"CH{channel}"] = _compare_waveform_series(
                name_a,
                series_a[channel],
                name_b,
                series_b[channel],
            )
        if channels:
            comparison["families"][family_name] = channels

    comparison_path = out_dir / "waveform_comparison.json"
    _safe_json_write(comparison_path, comparison)
    comparison_html_path = _render_waveform_comparison_html(out_dir, comparison)
    comparison["json_path"] = str(comparison_path)
    comparison["html_path"] = str(comparison_html_path)

    return truth, truth_path, comparison


def _classify_error(text):
    lowered = str(text).lower()
    if "timeout" in lowered or "timed out" in lowered:
        return "transport_timeout"
    if "pipe error" in lowered:
        return "transport_pipe_error"
    if "length-prefixed body" in lowered or "length mismatch" in lowered:
        return "malformed_length_prefix"
    if "deep_memory" in lowered or "deep-memory" in lowered or "depmem" in lowered:
        return "deep_memory_error"
    if "waveform" in lowered or lowered.startswith("ch1:") or lowered.startswith("ch2:"):
        return "waveform_read_error"
    return "unknown_error"


def _is_transport_failure(exc):
    if isinstance(exc, (usb.core.USBTimeoutError, usb.core.USBError)):
        return True
    text = str(exc).lower()
    if isinstance(exc, OSError) and (
        "timeout" in text
        or "timed out" in text
        or "pipe" in text
        or "access denied" in text
    ):
        return True
    if isinstance(exc, ValueError) and (
        "length-prefixed" in text
        or "payload is too short" in text
        or "packet prefix" in text
        or "header" in text
    ):
        return True
    return False


def _snapshot_scope_state(scope):
    def capture(fn):
        try:
            value = fn()
            if hasattr(value, "units"):
                return {"value": value.magnitude, "units": str(value.units)}
            return str(value)
        except Exception as exc:
            return f"error: {type(exc).__name__}: {exc}"

    return {
        "trigger_status": capture(lambda: scope.trigger_status),
        "trigger_type": capture(lambda: scope.trigger_type),
        "single_trigger_mode": capture(lambda: scope.single_trigger_mode),
        "trigger_sweep": capture(lambda: scope.trigger_sweep),
        "timebase_scale": capture(lambda: scope.timebase_scale),
        "horizontal_offset": capture(lambda: scope.horizontal_offset),
        "memory_depth": capture(lambda: scope.memory_depth),
        "acquire_mode": capture(lambda: scope.acquire_mode),
        "acquire_averages": capture(lambda: scope.acquire_averages),
        "measurement_display_enabled": capture(
            lambda: scope.measurement_display_enabled
        ),
        "raw_edge_level": capture(
            lambda: _clean_reply(scope.query(":TRIGger:SINGle:EDGE:LEVel?"))
        ),
        "trigger_configuration": capture(lambda: scope.read_trigger_configuration()),
    }


def _snapshot_scope_state_minimal(scope):
    def capture(fn):
        try:
            return str(fn())
        except Exception as exc:
            return f"error: {type(exc).__name__}: {exc}"

    return {
        "trigger_status": capture(lambda: _clean_reply(scope.query(":TRIGger:STATUS?"))),
        "trigger_sweep": capture(
            lambda: _clean_reply(scope.query(":TRIGger:SINGle:SWEEp?"))
        ),
        "raw_edge_level": capture(
            lambda: _clean_reply(scope.query(":TRIGger:SINGle:EDGE:LEVel?"))
        ),
        "timebase_scale": capture(lambda: _clean_reply(scope.query(":HORIzontal:Scale?"))),
        "memory_depth": capture(lambda: _clean_reply(scope.query(":ACQUIRE:DEPMEM?"))),
    }


def _capture_state_for_style(scope, style):
    if style == "off":
        return None
    if style == "minimal":
        return _snapshot_scope_state_minimal(scope)
    return _snapshot_scope_state(scope)


def _record_state_snapshot(trace_ctx, phase, command_label, snapshot, error=None):
    if (
        trace_ctx is None
        or trace_ctx.state_trace_path is None
        or trace_ctx.state_probe_style == "off"
        or snapshot is None
    ):
        return
    trace_ctx.state_seq += 1
    payload = {
        "ts": _timestamp().isoformat(timespec="microseconds"),
        "seq": trace_ctx.state_seq,
        "phase": phase,
        "command_label": command_label,
        "snapshot": snapshot,
    }
    if error is not None:
        payload["error"] = error
    _write_jsonl(trace_ctx.state_trace_path, payload)


def _apply_state_step(scope, label, trace_ctx, callback, settle_s=0.05):
    style = "full" if trace_ctx is None else trace_ctx.state_probe_style
    _record_state_snapshot(
        trace_ctx, "before", label, _capture_state_for_style(scope, style)
    )
    try:
        result = callback()
    except Exception as exc:
        _record_state_snapshot(
            trace_ctx,
            "error",
            label,
            _capture_state_for_style(scope, style),
            error=f"{type(exc).__name__}: {exc}",
        )
        raise
    _record_state_snapshot(
        trace_ctx, "after", label, _capture_state_for_style(scope, style)
    )
    time.sleep(max(float(settle_s), 0.0))
    _record_state_snapshot(
        trace_ctx,
        "after_settle",
        label,
        _capture_state_for_style(scope, style),
    )
    return result


def _apply_channel_setup(scope, args, trace_ctx):
    for channel in range(1, 5):
        _apply_state_step(
            scope,
            f"channel[{channel}].display = {channel in args.capture_channels}",
            trace_ctx,
            lambda channel=channel: setattr(
                scope.channel[channel - 1],
                "display",
                channel in args.capture_channels,
            ),
        )

    _apply_state_step(
        scope,
        f"channel[1].probe_attenuation = {int(args.ch1_probe)}",
        trace_ctx,
        lambda: setattr(scope.channel[0], "probe_attenuation", int(args.ch1_probe)),
    )
    _apply_state_step(
        scope,
        f"channel[2].probe_attenuation = {int(args.ch2_probe)}",
        trace_ctx,
        lambda: setattr(scope.channel[1], "probe_attenuation", int(args.ch2_probe)),
    )
    if 3 in args.capture_channels:
        _apply_state_step(
            scope,
            f"channel[3].probe_attenuation = {int(args.ch3_probe)}",
            trace_ctx,
            lambda: setattr(scope.channel[2], "probe_attenuation", int(args.ch3_probe)),
        )

    if args.ch1_scale_v_div is not None:
        _apply_state_step(
            scope,
            f"channel[1].scale = {args.ch1_scale_v_div} V/div",
            trace_ctx,
            lambda: setattr(scope.channel[0], "scale", args.ch1_scale_v_div * u.volt),
        )
    if args.ch2_scale_v_div is not None:
        _apply_state_step(
            scope,
            f"channel[2].scale = {args.ch2_scale_v_div} V/div",
            trace_ctx,
            lambda: setattr(scope.channel[1], "scale", args.ch2_scale_v_div * u.volt),
        )
    if args.ch3_scale_v_div is not None and 3 in args.capture_channels:
        _apply_state_step(
            scope,
            f"channel[3].scale = {args.ch3_scale_v_div} V/div",
            trace_ctx,
            lambda: setattr(scope.channel[2], "scale", args.ch3_scale_v_div * u.volt),
        )

    _apply_state_step(
        scope,
        f"channel[1].position = {float(args.ch1_position_div)}",
        trace_ctx,
        lambda: setattr(scope.channel[0], "position", float(args.ch1_position_div)),
    )
    _apply_state_step(
        scope,
        f"channel[2].position = {float(args.ch2_position_div)}",
        trace_ctx,
        lambda: setattr(scope.channel[1], "position", float(args.ch2_position_div)),
    )
    if 3 in args.capture_channels:
        _apply_state_step(
            scope,
            f"channel[3].position = {float(args.ch3_position_div)}",
            trace_ctx,
            lambda: setattr(scope.channel[2], "position", float(args.ch3_position_div)),
        )


def _apply_trigger_common(scope, args, trace_ctx):
    sweep_readback = None
    if args.trigger_sweep:
        try:
            _apply_state_step(
                scope,
                f"trigger_sweep = {args.trigger_sweep}",
                trace_ctx,
                lambda: setattr(
                    scope, "trigger_sweep", scope.TriggerSweep(args.trigger_sweep)
                ),
            )
            sweep_readback = str(scope.trigger_sweep)
        except Exception as exc:
            sweep_readback = f"error: {exc}"
    return sweep_readback


def _configure_scope(scope, args, trace_ctx):
    _apply_channel_setup(scope, args, trace_ctx)
    if args.memory_depth is not None:
        _apply_state_step(
            scope,
            f"memory_depth = {int(args.memory_depth)}",
            trace_ctx,
            lambda: setattr(scope, "memory_depth", int(args.memory_depth)),
        )
    if args.horizontal_offset_div is not None:
        _apply_state_step(
            scope,
            f"horizontal_offset = {float(args.horizontal_offset_div)}",
            trace_ctx,
            lambda: setattr(scope, "horizontal_offset", float(args.horizontal_offset_div)),
        )
    if args.measurement_display == "on":
        _apply_state_step(
            scope,
            "measurement_display_enabled = True",
            trace_ctx,
            lambda: setattr(scope, "measurement_display_enabled", True),
        )
    elif args.measurement_display == "off":
        _apply_state_step(
            scope,
            "measurement_display_enabled = False",
            trace_ctx,
            lambda: setattr(scope, "measurement_display_enabled", False),
        )
    _apply_state_step(
        scope,
        f"timebase_scale = {args.timebase_s_div}",
        trace_ctx,
        lambda: setattr(scope, "timebase_scale", args.timebase_s_div * u.second),
    )
    _apply_state_step(
        scope,
        ":TRIGger:TYPE SINGle",
        trace_ctx,
        lambda: scope.sendcmd(":TRIGger:TYPE SINGle"),
    )

    if args.profile == "edge":
        _apply_state_step(
            scope,
            "single_trigger_mode = EDGE",
            trace_ctx,
            lambda: setattr(scope, "single_trigger_mode", scope.SingleTriggerMode.edge),
        )
        _apply_state_step(
            scope,
            f"trigger_source = {args.edge_source}",
            trace_ctx,
            lambda: setattr(
                scope,
                "trigger_source",
                getattr(scope.TriggerSource, args.edge_source.lower()),
            ),
        )
        _apply_state_step(
            scope,
            f"trigger_coupling = {args.edge_coupling}",
            trace_ctx,
            lambda: setattr(
                scope,
                "trigger_coupling",
                getattr(scope.TriggerCoupling, args.edge_coupling.lower()),
            ),
        )
        _apply_state_step(
            scope,
            f"trigger_slope = {args.edge_slope}",
            trace_ctx,
            lambda: setattr(
                scope,
                "trigger_slope",
                getattr(scope.TriggerSlope, args.edge_slope.lower()),
            ),
        )
        if args.trigger_level_v is not None:
            _apply_state_step(
                scope,
                f"trigger_level = {args.trigger_level_v} V",
                trace_ctx,
                lambda: setattr(scope, "trigger_level", args.trigger_level_v * u.volt),
            )
    elif args.profile == "pulse":
        _apply_state_step(
            scope,
            "single_trigger_mode = PULSe",
            trace_ctx,
            lambda: setattr(scope, "single_trigger_mode", scope.SingleTriggerMode.pulse),
        )
        _apply_state_step(
            scope,
            f"PULSe:SOURce {args.pulse_source.upper()}",
            trace_ctx,
            lambda: scope.sendcmd(
                f":TRIGger:SINGle:PULSe:SOURce {args.pulse_source.upper()}"
            ),
        )
        _apply_state_step(
            scope,
            f"PULSe:SIGN {args.pulse_sign}",
            trace_ctx,
            lambda: scope.sendcmd(f":TRIGger:SINGle:PULSe:SIGN {args.pulse_sign}"),
        )
        _apply_state_step(
            scope,
            f"PULSe:TIME {args.pulse_trigger_time_us} us",
            trace_ctx,
            lambda: scope.sendcmd(
                f":TRIGger:SINGle:PULSe:TIME {_format_time_token(args.pulse_trigger_time_us * u.microsecond)}"
            ),
        )
        _apply_state_step(
            scope,
            f"PULSe:DIR {args.pulse_dir.upper()}",
            trace_ctx,
            lambda: scope.sendcmd(f":TRIGger:SINGle:PULSe:DIR {args.pulse_dir.upper()}"),
        )
        _apply_state_step(
            scope,
            f"PULSe:COUPling {args.pulse_coupling.upper()}",
            trace_ctx,
            lambda: scope.sendcmd(
                f":TRIGger:SINGle:PULSe:COUPling {args.pulse_coupling.upper()}"
            ),
        )
    elif args.profile == "slope":
        _apply_state_step(
            scope,
            "single_trigger_mode = SLOPe",
            trace_ctx,
            lambda: setattr(scope, "single_trigger_mode", scope.SingleTriggerMode.slope),
        )
        _apply_state_step(
            scope,
            f"SLOPe:SOURce {args.slope_source.upper()}",
            trace_ctx,
            lambda: scope.sendcmd(
                f":TRIGger:SINGle:SLOPe:SOURce {args.slope_source.upper()}"
            ),
        )
        _apply_state_step(
            scope,
            f"SLOPe:ULevel {args.slope_upper_v} V",
            trace_ctx,
            lambda: scope.sendcmd(
                f":TRIGger:SINGle:SLOPe:ULevel {_format_voltage_token(args.slope_upper_v * u.volt)}"
            ),
        )
        _apply_state_step(
            scope,
            f"SLOPe:LLevel {args.slope_lower_v} V",
            trace_ctx,
            lambda: scope.sendcmd(
                f":TRIGger:SINGle:SLOPe:LLevel {_format_voltage_token(args.slope_lower_v * u.volt)}"
            ),
        )
        _apply_state_step(
            scope,
            f"SLOPe:SIGN {args.slope_sign}",
            trace_ctx,
            lambda: scope.sendcmd(f":TRIGger:SINGle:SLOPe:SIGN {args.slope_sign}"),
        )
        _apply_state_step(
            scope,
            f"SLOPe:TIME {args.slope_trigger_time_us} us",
            trace_ctx,
            lambda: scope.sendcmd(
                f":TRIGger:SINGle:SLOPe:TIME {_format_time_token(args.slope_trigger_time_us * u.microsecond)}"
            ),
        )
        _apply_state_step(
            scope,
            f"SLOPe:SLOPe {args.slope_edge.upper()}",
            trace_ctx,
            lambda: scope.sendcmd(
                f":TRIGger:SINGle:SLOPe:SLOPe {args.slope_edge.upper()}"
            ),
        )
    else:
        raise ValueError(f"Unsupported profile: {args.profile}")

    _apply_state_step(
        scope,
        f"trigger_holdoff = {args.trigger_holdoff_ns} ns",
        trace_ctx,
        lambda: setattr(scope, "trigger_holdoff", args.trigger_holdoff_ns * u.nanosecond),
    )
    sweep_readback = _apply_trigger_common(scope, args, trace_ctx)

    if args.arm == "run":
        _apply_state_step(scope, "run()", trace_ctx, scope.run)
    elif args.arm == "single":
        _apply_state_step(
            scope,
            f"single(stop_first={args.single_stop_first}, arm_method={args.arm_method})",
            trace_ctx,
            lambda: scope.single(
                stop_first=args.single_stop_first,
                arm_method=args.arm_method,
            ),
        )
    elif args.arm == "stop":
        _apply_state_step(scope, "stop()", trace_ctx, scope.stop)
    return {
        "trigger_sweep": sweep_readback,
        "trigger_status": str(scope.trigger_status),
        "trigger_snapshot": str(scope.read_trigger_configuration()),
        "raw_edge_level": _clean_reply(scope.query(":TRIGger:SINGle:EDGE:LEVel?")),
        "trigger_type": str(scope.trigger_type),
    }


def _restore_stable_edge(scope, args):
    try:
        scope.sendcmd(":TRIGger:TYPE SINGle")
        scope.sendcmd(":TRIGger:SINGle:MODE EDGE")
        scope.sendcmd(f":TRIGger:SINGle:EDGE:SOURce {args.edge_source.upper()}")
        scope.sendcmd(f":TRIGger:SINGle:EDGE:COUPling {args.edge_coupling.upper()}")
        scope.sendcmd(f":TRIGger:SINGle:EDGE:SLOPe {args.edge_slope.upper()}")
        if args.trigger_level_v is not None:
            scope.sendcmd(
                f":TRIGger:SINGle:EDGE:LEVel {_format_voltage_token(args.trigger_level_v * u.volt)}"
            )
    except Exception:
        pass


def _collect_scope_state(scope, style="full"):
    if style == "off":
        return {}
    if style == "minimal":
        return _snapshot_scope_state_minimal(scope)
    state = {}
    try:
        state["trigger_status"] = str(scope.trigger_status)
    except Exception as exc:
        state["trigger_status"] = f"error: {exc}"
    try:
        state["trigger_type"] = str(scope.trigger_type)
    except Exception as exc:
        state["trigger_type"] = f"error: {exc}"
    try:
        state["timebase_scale"] = str(scope.timebase_scale)
    except Exception as exc:
        state["timebase_scale"] = f"error: {exc}"
    try:
        state["trigger_sweep"] = str(scope.trigger_sweep)
    except Exception as exc:
        state["trigger_sweep"] = f"error: {exc}"
    try:
        state["raw_edge_level"] = _clean_reply(
            scope.query(":TRIGger:SINGle:EDGE:LEVel?")
        )
    except Exception as exc:
        state["raw_edge_level"] = f"error: {exc}"
    try:
        state["trigger_snapshot"] = str(scope.read_trigger_configuration())
    except Exception as exc:
        state["trigger_snapshot"] = f"error: {exc}"
    return state


def _namespace_with_overrides(args, **updates):
    data = vars(args).copy()
    data.update(updates)
    return argparse.Namespace(**data)


def _write_report(
    out_dir,
    args,
    esp_lines,
    scope_state,
    after_arm_state,
    after_finalize_state,
    screenshot_path,
    html_view_path,
    html_data_path,
    trace_ctx,
    screenshot_error,
    waveforms,
    waveform_errors,
    waveform_truth_path=None,
    waveform_truth=None,
    waveform_comparison=None,
):
    report_path = out_dir / "report.md"
    json_path = out_dir / "report.json"

    waveform_rows = []
    for summary in waveforms:
        waveform_rows.append(
            f"| CH{summary.channel} | {summary.sample_count} | "
            f"{summary.time_start_s:.6g} | {summary.time_end_s:.6g} | "
            f"{summary.voltage_min_v:.6g} | {summary.voltage_max_v:.6g} | "
            f"{summary.voltage_pp_v:.6g} | `{Path(summary.csv_path).name}` |"
        )

    report_lines = [
        f"# OWON ESP32 Trigger Jig Run: {args.label}",
        "",
        f"- Timestamp: `{_timestamp().isoformat(timespec='seconds')}`",
        f"- Profile: `{args.profile}`",
        f"- ESP32 port: `{args.esp_port}`",
        f"- Scope VID:PID: `{args.scope_vid}:{args.scope_pid}`",
        f"- Arm command: `{args.arm}`",
        f"- Screenshot: `{screenshot_path.name if screenshot_path is not None else 'not captured'}`",
        "",
        "## Primary Scope Screen",
        "",
        *(
            [f"![Primary scope screen]({Path(screenshot_path).name})", ""]
            if screenshot_path is not None
            else []
        ),
        "",
        "## Derived Scope View",
        "",
        *(
            [
                f"- [Open `scope_view.html`]({Path(html_view_path).name})",
                f"- [Open `scope_view.json`]({Path(html_data_path).name})",
                "",
                "> VS Code Markdown preview disables local scripts/iframes here.",
                "> Open the HTML file directly to view the rendered scope screen.",
                "",
            ]
            if html_view_path is not None and html_data_path is not None
            else []
        ),
        *(
            [
                "",
                "## Trace Artifacts",
                "",
                f"- [Open `scpi_trace.jsonl`]({Path(trace_ctx.scpi_trace_path).name})",
                f"- [Open `state_trace.jsonl`]({Path(trace_ctx.state_trace_path).name})",
                "",
            ]
            if trace_ctx is not None
            and (
                trace_ctx.scpi_trace_path is not None
                or trace_ctx.state_trace_path is not None
            )
            else []
        ),
        "",
        "## ESP32 Configuration",
        "",
        f"- Pulse mode: `{args.pulse_mode}`",
        f"- Pulse width: `{args.pulse_width_us} us`",
        f"- Pulse gap: `{args.pulse_gap_us} us`",
        f"- Frame gap: `{args.pulse_frame_us} us`",
        f"- Slope half-period: `{args.slope_half_period_us} us`",
        "",
        "## Scope State",
        "",
        f"- Trigger status: `{scope_state['trigger_status']}`",
        f"- Timebase scale: `{scope_state['timebase_scale']}`",
        f"- Trigger snapshot: `{scope_state['trigger_snapshot']}`",
        "",
        "## Arming States",
        "",
        f"- After arm: `{after_arm_state}`",
        f"- After finalize: `{after_finalize_state}`",
        "",
        "## ESP32 Serial Output",
        "",
        "```text",
        *esp_lines,
        "```",
        "",
        "## Waveforms",
        "",
        "| Channel | Samples | t_start (s) | t_end (s) | v_min (V) | v_max (V) | v_pp (V) | CSV |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        *waveform_rows,
        "",
        *(
            [
                "## Waveform Truth",
                "",
                f"- [Open `waveform_truth.json`]({Path(waveform_truth_path).name})",
                "",
                f"- Errors: `{'; '.join(waveform_truth['errors']) if waveform_truth and waveform_truth.get('errors') else 'none'}`",
                "",
            ]
            if waveform_truth_path is not None and waveform_truth is not None
            else []
        ),
        *(
            [
                "## Waveform Comparison",
                "",
                f"- [Open `waveform_comparison.html`]({Path(waveform_comparison['html_path']).name})",
                f"- [Open `waveform_comparison.json`]({Path(waveform_comparison['json_path']).name})",
                "",
                "| Family | Channel | A | B | Counts | Alignment | Mean dV | Max dV | Diff samples | Max dt |",
                "| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: |",
                *[
                    f"| `{family}` | `{channel_name}` | "
                    f"`{metrics['series_a']}` | `{metrics['series_b']}` | "
                    f"`{metrics['count_a']} vs {metrics['count_b']} (shared {metrics['aligned_count']})` | "
                    f"`{metrics['alignment']}` | "
                    f"`{metrics['mean_abs_voltage_delta_v']:.6g}` | "
                    f"`{metrics['max_abs_voltage_delta_v']:.6g}` | "
                    f"`{metrics['diff_sample_count']}` | "
                    f"`{metrics['max_abs_time_delta_s']:.6g}` |"
                    for family, channels in waveform_comparison["families"].items()
                    for channel_name, metrics in channels.items()
                ],
                "",
            ]
            if waveform_comparison is not None
            else []
        ),
        "",
        "## Notes",
        "",
        "- This report is generated by `owon_esp32_trigger_jig_runner.py`.",
        "- The BMP is the primary evidence artifact.",
        "- `scope_view.html` is a derived view built from `scope_view.json`.",
        "- `waveform_comparison.html` groups the screen and deep-memory APIs side by side.",
        "- HTML waveform views keep the discrete front-panel `M:` scale and show a separate derived `Span:` from the returned x-axis.",
        "- It records the exact run inputs and captured artifacts, but it does not yet make a formal pass/fail verdict.",
    ]
    if waveform_errors:
        report_lines.extend(
            [
                "",
                "## Waveform Errors",
                "",
                *[f"- {item}" for item in waveform_errors],
            ]
        )
    if screenshot_error:
        report_lines.extend(
            [
                "",
                "## Screenshot Error",
                "",
                f"- {screenshot_error}",
            ]
        )
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    payload = {
        "label": args.label,
        "profile": args.profile,
        "esp_port": args.esp_port,
        "scope_vid": args.scope_vid,
        "scope_pid": args.scope_pid,
        "arm": args.arm,
        "arm_method": args.arm_method,
        "single_stop_first": args.single_stop_first,
        "finalize_method": args.finalize_method,
        "finalize_delay_s": args.finalize_delay_s,
        "trigger_status": scope_state["trigger_status"],
        "timebase_scale": scope_state["timebase_scale"],
        "trigger_snapshot": scope_state["trigger_snapshot"],
        "after_arm_state": after_arm_state,
        "after_finalize_state": after_finalize_state,
        "screenshot_path": None if screenshot_path is None else str(screenshot_path),
        "html_view_path": None if html_view_path is None else str(html_view_path),
        "html_data_path": None if html_data_path is None else str(html_data_path),
        "scpi_trace_path": None if trace_ctx is None else trace_ctx.scpi_trace_path,
        "state_trace_path": None if trace_ctx is None else trace_ctx.state_trace_path,
        "waveform_truth_path": None if waveform_truth_path is None else str(waveform_truth_path),
        "waveform_comparison_path": (
            None if waveform_comparison is None else str(waveform_comparison["html_path"])
        ),
        "waveform_comparison_json_path": (
            None if waveform_comparison is None else str(waveform_comparison["json_path"])
        ),
        "screenshot_error": screenshot_error,
        "waveforms": [asdict(summary) for summary in waveforms],
        "waveform_errors": waveform_errors,
        "esp_serial_lines": esp_lines,
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    return report_path, json_path


def _run_capture_case(scope, args, out_dir, esp_lines):
    out_dir.mkdir(parents=True, exist_ok=True)
    trace_ctx = _make_trace_context(out_dir, args)
    if trace_ctx.scpi_trace_path is not None:
        scope.enable_trace(trace_ctx.scpi_trace_path)
    extra_state = _configure_scope(scope, args, trace_ctx)
    time.sleep(max(args.capture_delay_s, 0.0))
    after_arm_state = {}
    if not args.immediate_deep_probe:
        after_arm_state = _collect_scope_state(scope, style=args.state_probe_style)
        after_arm_state.update(extra_state)
    if args.finalize_method != "none":
        _apply_state_step(
            scope,
            f"freeze_acquisition(method={args.finalize_method})",
            trace_ctx,
            lambda: scope.freeze_acquisition(
                method=args.finalize_method,
                settle_time=args.finalize_delay_s,
            ),
            settle_s=0.0,
        )
    after_finalize_state = {}
    if not args.immediate_deep_probe:
        after_finalize_state = _collect_scope_state(scope, style=args.state_probe_style)
        scope_state = dict(after_finalize_state)
    else:
        scope_state = dict(extra_state)

    screenshot_path = None
    html_view_path = None
    html_data_path = None
    screenshot_error = None
    waveform_truth = None
    waveform_truth_path = None
    waveform_comparison = None
    waveforms = []
    waveform_errors = []

    if args.validate_waveforms:
        try:
            waveform_truth, waveform_truth_path, waveform_comparison = _capture_waveform_truth(
                scope,
                out_dir,
                args,
                scope_state,
                args.capture_channels,
                deep_first=args.immediate_deep_probe,
            )
        except Exception as exc:
            waveform_errors.append(f"waveform truth capture: {exc}")

    if args.immediate_deep_probe:
        if waveform_truth is not None:
            after_arm_state = _collect_scope_state(scope, style="minimal")
            after_arm_state.update(extra_state)
            after_finalize_state = dict(after_arm_state)
            scope_state = dict(after_arm_state)
    else:
        try:
            screenshot_path = _capture_screenshot(scope, out_dir, args)
        except Exception as exc:
            screenshot_error = str(exc)

        for channel in args.capture_channels:
            try:
                waveforms.append(_capture_waveform(scope, channel, out_dir))
            except Exception as exc:
                waveform_errors.append(f"CH{channel}: {exc}")

        scope_view_sample_rate_text = None
        try:
            scope_view_sample_rate_text = _metadata_sample_rate_text(
                scope.read_waveform_metadata()
            )
        except Exception as exc:
            waveform_errors.append(f"scope_view sample-rate metadata: {exc}")

        try:
            html_view_path, html_data_path = _render_scope_html(
                out_dir,
                args,
                scope_state,
                waveforms,
                sample_rate_text=scope_view_sample_rate_text,
            )
        except Exception as exc:
            waveform_errors.append(f"scope_view.html: {exc}")

    report_path, json_path = _write_report(
        out_dir,
        args,
        esp_lines,
        scope_state,
        after_arm_state,
        after_finalize_state,
        screenshot_path,
        html_view_path,
        html_data_path,
        trace_ctx,
        screenshot_error,
        waveforms,
        waveform_errors,
        waveform_truth_path=waveform_truth_path,
        waveform_truth=waveform_truth,
        waveform_comparison=waveform_comparison,
    )
    primary_error = None
    if screenshot_error:
        primary_error = screenshot_error
    elif waveform_errors:
        primary_error = waveform_errors[0]
    return {
        "label": args.label,
        "profile": args.profile,
        "trigger_status": scope_state.get("trigger_status"),
        "trigger_status_before_reads": after_arm_state.get("trigger_status"),
        "trigger_status_after_finalize": after_finalize_state.get("trigger_status"),
        "trigger_sweep": scope_state.get("trigger_sweep"),
        "arm_method": args.arm_method,
        "single_stop_first": args.single_stop_first,
        "finalize_method": args.finalize_method,
        "screenshot_path": None if screenshot_path is None else str(screenshot_path),
        "screenshot_error": screenshot_error,
        "failure_class": None if primary_error is None else _classify_error(primary_error),
        "deep_metadata_ok": bool(
            waveform_truth is not None and waveform_truth.get("deep_memory_metadata") is not None
        ),
        "deep_ch1_ok": bool(
            waveform_truth is not None and "CH1" in waveform_truth.get("deep_memory_channels", {})
        ),
        "deep_bundle_ok": bool(
            waveform_truth is not None and waveform_truth.get("deep_memory_bundle") is not None
        ),
        "session_error": None,
        "waveform_errors": list(waveform_errors),
        "report_path": str(report_path),
        "json_path": str(json_path),
    }, report_path, json_path, waveforms


def _build_verification_cases(args):
    cases = []
    if args.verify_pulse:
        trigger_time_us = int(args.pulse_trigger_time_us)
        width_map = {
            ">": max(trigger_time_us * 4, trigger_time_us + 100),
            "<": max(10, trigger_time_us // 2),
            "=": trigger_time_us,
        }
        for sign, suffix in ((">", "gt"), ("<", "lt"), ("=", "eq")):
            case_width_us = width_map[sign]
            cases.append(
                _namespace_with_overrides(
                    args,
                    label=(
                        f"{args.label}_pulse_{suffix}_{trigger_time_us}us_"
                        f"src_{case_width_us}us"
                    ),
                    profile="pulse",
                    pulse_mode="single",
                    pulse_width_us=case_width_us,
                    pulse_sign=sign,
                )
            )
    elif args.verify_slope:
        for edge in ("POS", "NEG"):
            for sign, suffix in ((">", "gt"), ("<", "lt"), ("=", "eq")):
                cases.append(
                    _namespace_with_overrides(
                        args,
                        label=(
                            f"{args.label}_slope_{edge.lower()}_{suffix}_"
                            f"{int(args.slope_trigger_time_us)}us"
                        ),
                        profile="slope",
                        slope_edge=edge,
                        slope_sign=sign,
                    )
                )
    return cases


def _build_edge_arming_cases(args):
    base = {
        "profile": "edge",
        "capture_channels": [1, 2],
        "pulse_mode": "single",
        "pulse_width_us": 100,
        "pulse_gap_us": 2000,
        "pulse_frame_us": 2000,
        "slope_half_period_us": 2000,
        "ch1_probe": 1,
        "ch2_probe": 1,
        "ch1_scale_v_div": 1.0,
        "ch2_scale_v_div": 1.0,
        "ch1_position_div": 1.0,
        "ch2_position_div": -2.0,
        "timebase_s_div": 200e-6,
        "trigger_level_v": 1.65,
        "trigger_holdoff_ns": 100,
        "validate_waveforms": True,
        "arm": "single",
    }
    cases = [
        ("edge_auto_legacy_stopfirst", "AUTO", "legacy_single", True, "none"),
        ("edge_normal_legacy_stopfirst", "NORMal", "legacy_single", True, "none"),
        ("edge_normal_legacy_nostopfirst", "NORMal", "legacy_single", False, "none"),
        ("edge_single_legacy_stopfirst", "SINGle", "legacy_single", True, "none"),
        ("edge_auto_running_stopfirst_runningstop", "AUTO", "running_run", True, "running_stop"),
        ("edge_normal_running_stopfirst_runningstop", "NORMal", "running_run", True, "running_stop"),
        ("edge_normal_running_nostopfirst_runningstop", "NORMal", "running_run", False, "running_stop"),
        ("edge_single_running_stopfirst_runningstop", "SINGle", "running_run", True, "running_stop"),
        ("edge_normal_legacy_nostopfirst_runningstop", "NORMal", "legacy_single", False, "running_stop"),
        ("edge_normal_legacy_stopfirst_runningstop", "NORMal", "legacy_single", True, "running_stop"),
    ]
    built = []
    for label, sweep, arm_method, stop_first, finalize_method in cases:
        built.append(
            _namespace_with_overrides(
                args,
                label=label,
                trigger_sweep=sweep,
                arm_method=arm_method,
                single_stop_first=stop_first,
                finalize_method=finalize_method,
                **base,
            )
        )
    return built


def _run_case_with_fresh_scope(args, case_args, out_dir, esp_lines):
    scope = None
    transport_failure = False
    clean_success = False
    try:
        scope = _open_scope(case_args)
        summary, report_path, json_path, waveforms = _run_capture_case(
            scope, case_args, out_dir, esp_lines
        )
        transport_failure = bool(
            summary.get("failure_class")
            in {"transport_timeout", "transport_pipe_error", "malformed_length_prefix"}
            or (
                summary.get("session_error") is not None
                and _is_transport_failure(summary["session_error"])
            )
        )
        clean_success = not transport_failure
        return summary, report_path, json_path, waveforms
    except Exception as exc:
        failure_class = _classify_error(exc)
        transport_failure = _is_transport_failure(exc)
        report_path = out_dir / "case_error.txt"
        report_path.write_text(f"{type(exc).__name__}: {exc}\n", encoding="utf-8")
        summary = {
            "label": case_args.label,
            "profile": case_args.profile,
            "trigger_status": None,
            "trigger_status_before_reads": None,
            "trigger_status_after_finalize": None,
            "trigger_sweep": case_args.trigger_sweep,
            "arm_method": case_args.arm_method,
            "single_stop_first": case_args.single_stop_first,
            "finalize_method": case_args.finalize_method,
            "screenshot_path": None,
            "screenshot_error": None,
            "failure_class": failure_class,
            "deep_metadata_ok": False,
            "deep_ch1_ok": False,
            "deep_bundle_ok": False,
            "waveform_errors": [],
            "session_error": f"{type(exc).__name__}: {exc}",
            "report_path": str(report_path),
            "json_path": None,
        }
        return summary, report_path, None, []
    finally:
        if scope is not None:
            try:
                scope.disable_trace()
            except Exception:
                pass
            try:
                if transport_failure:
                    if case_args.restore_after_failure:
                        try:
                            _restore_stable_edge(scope, case_args)
                        except Exception:
                            pass
                    scope.close(
                        reset_device=case_args.hard_reset_on_failure,
                        settle_time=case_args.reset_settle_s,
                    )
                else:
                    if clean_success and case_args.restore_after_success:
                        try:
                            _restore_stable_edge(scope, case_args)
                        except Exception:
                            pass
                    scope.close()
            except Exception:
                pass


def _write_verification_report(out_dir, args, summaries):
    report_path = out_dir / "verification_report.md"
    json_path = out_dir / "verification_report.json"

    rows = []
    for summary in summaries:
        rows.append(
            f"| `{summary['label']}` | `{summary['profile']}` | "
            f"`{summary['trigger_status']}` | `{summary['trigger_sweep']}` | "
            f"`{Path(summary['screenshot_path']).name if summary['screenshot_path'] else 'none'}` | "
            f"`{Path(summary['report_path']).name}` | "
            f"`{'; '.join(summary['waveform_errors']) if summary['waveform_errors'] else 'none'}` |"
        )

    lines = [
        f"# OWON Trigger Verification: {args.label}",
        "",
        f"- Timestamp: `{_timestamp().isoformat(timespec='seconds')}`",
        f"- ESP32 port: `{args.esp_port}`",
        f"- Scope VID:PID: `{args.scope_vid}:{args.scope_pid}`",
        "",
        "| Case | Profile | Trigger status | Sweep | Screenshot | Report | Waveform errors |",
        "| --- | --- | --- | --- | --- | --- | --- |",
        *rows,
        "",
        "## Case Reports",
        "",
        *[
            f"- [{Path(item['report_path']).name}]({Path(item['label']) / Path(item['report_path']).name})"
            for item in summaries
        ],
    ]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    json_path.write_text(json.dumps(summaries, indent=2), encoding="utf-8")
    return report_path, json_path


def _write_edge_arming_report(out_dir, args, summaries):
    report_path = out_dir / "edge_arming_report.md"
    json_path = out_dir / "edge_arming_report.json"

    rows = []
    for summary in summaries:
        rows.append(
            f"| `{summary['label']}` | `{summary['trigger_sweep']}` | "
            f"`{summary['arm_method']}` | `{summary['single_stop_first']}` | "
            f"`{summary['finalize_method']}` | "
            f"`{summary['trigger_status_before_reads']}` | "
            f"`{summary['trigger_status_after_finalize']}` | "
            f"`{summary['deep_metadata_ok']}` | `{summary['deep_ch1_ok']}` | "
            f"`{summary['deep_bundle_ok']}` | "
            f"`{summary['failure_class'] or 'none'}` | "
            f"`{Path(summary['report_path']).name if summary.get('report_path') else 'none'}` |"
        )

    lines = [
        f"# OWON Edge Arming Matrix: {args.label}",
        "",
        f"- Timestamp: `{_timestamp().isoformat(timespec='seconds')}`",
        f"- ESP32 port: `{args.esp_port}`",
        f"- Scope VID:PID: `{args.scope_vid}:{args.scope_pid}`",
        "",
        "| Case | Sweep | Arm | Stop First | Finalize | Status Before Reads | Status After Finalize | Deep Meta | Deep CH1 | Deep Bundle | Failure Class | Report |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        *rows,
        "",
        "## Case Reports",
        "",
        *[
            f"- [{Path(item['report_path']).name}]({Path(item['label']) / Path(item['report_path']).name})"
            for item in summaries
            if item.get("report_path")
        ],
    ]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    json_path.write_text(json.dumps(summaries, indent=2), encoding="utf-8")
    return report_path, json_path
