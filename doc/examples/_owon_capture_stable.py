#!/usr/bin/env python
"""
Stable capture helpers for the OWON ESP32 trigger jig runner.

This module contains the promoted, supported example flows:

- --capture-edge-pretty
- --capture-edge-pretty-burst
"""

from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from types import SimpleNamespace
import time

import instruments.owon.sds1104 as owon_sds1104

from _owon_capture_common import (
    _build_scope_html_data_from_series,
    _capture_depmem_all_summary_and_series,
    _capture_screen_channel_raw,
    _capture_screenshot,
    _clean_reply,
    _compare_waveform_series,
    _configure_esp_from_args,
    _make_trace_context,
    _metadata_sample_rate_text,
    _open_scope,
    _render_scope_html_with_data,
    _render_waveform_comparison_html,
    _safe_json_write,
    _timestamp,
)


def _is_pretty_edge_mode(args):
    return bool(args.capture_edge_pretty or args.capture_edge_pretty_burst)


def _apply_pretty_edge_defaults(args):
    if not _is_pretty_edge_mode(args):
        return args

    args.profile = "edge"
    args.arm = "single"
    # Bench finding on the connected DOS1104: forcing SWEEp NORMal in this
    # promoted path is unsafe. The stable sequence uses raw setup plus
    # `:TRIGger:SINGle:SWEEp SINGle`, then waits for a genuine trigger event.
    args.trigger_sweep = None
    args.trigger_level_v = 1.65
    args.ch1_probe = 1
    args.ch2_probe = 1
    args.ch1_position_div = 1.0
    args.ch2_position_div = -2.0
    args.ch1_scale_v_div = 1.0
    args.ch2_scale_v_div = 1.0
    args.timebase_s_div = 0.0002
    args.pulse_mode = "burst" if args.capture_edge_pretty_burst else "single"
    args.pulse_width_us = 100
    args.pulse_gap_us = 2000
    args.pulse_frame_us = 2000
    args.slope_half_period_us = 2000
    if args.label == "owon_esp32_trigger_jig":
        args.label = (
            "pretty_edge_capture_burst"
            if args.capture_edge_pretty_burst
            else "pretty_edge_capture"
        )
    return args


def _run_proven_edge_capture_case(args, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    trace_ctx = _make_trace_context(out_dir, args)
    scope = _open_scope(args)
    try:
        if trace_ctx.scpi_trace_path is not None:
            scope.enable_trace(trace_ctx.scpi_trace_path)

        initial_status = _clean_reply(scope.query(":TRIGger:STATUS?"))
        resumed_before_setup = False
        if initial_status.upper() == "STOP":
            scope.run()
            time.sleep(0.2)
            resumed_before_setup = True

        sequence = [
            ":CH1:DISP ON",
            ":CH2:DISP ON",
            ":CH3:DISP OFF",
            ":CH4:DISP OFF",
            ":CH1:PROB 1X",
            ":CH2:PROB 1X",
            ":CH1:SCAL 1v",
            ":CH2:SCAL 1v",
            ":CH1:POS 1.0",
            ":CH2:POS -2.0",
            ":ACQUire:Mode SAMPle",
            ":ACQUIRE:DEPMEM 10K",
            ":ACQUIRE:DEPMEM?",
            ":HORIzontal:Scale 500us",
            ":HORIzontal:Scale?",
            ":TRIGger:TYPE SINGle",
            ":TRIGger:SINGle:MODE EDGE",
            ":TRIGger:SINGle:EDGE:SOURce CH1",
            ":TRIGger:SINGle:EDGE:COUPling DC",
            ":TRIGger:SINGle:EDGE:SLOPe RISE",
            ":TRIGger:SINGle:EDGE:LEVel 1.64V",
            ":TRIGger:SINGle:EDGE:LEVel?",
            ":TRIGger:SINGle:HOLDoff 100ns",
            ":TRIGger:SINGle:SWEEp SINGle",
        ]
        for command in sequence:
            if command.endswith("?"):
                scope.query(command)
            else:
                scope.sendcmd(command)

        esp_lines = _configure_esp_from_args(args)
        time.sleep(0.5)
        time.sleep(0.5)

        status_text = _clean_reply(scope.query(":TRIGger:STATUS?"))
        screen_metadata = (
            owon_sds1104._parse_json_payload(  # pylint: disable=protected-access
                scope._binary_query(
                    ":DATA:WAVE:SCREen:HEAD?"
                ),  # pylint: disable=protected-access
                "waveform metadata",
            )
        )
        screen_metadata_path = out_dir / "screen_waveform_metadata.json"
        _safe_json_write(screen_metadata_path, screen_metadata)

        waveforms = []
        screen_series = {}
        for channel in (1, 2):
            summary, series = _capture_screen_channel_raw(
                scope, screen_metadata, channel, out_dir
            )
            waveforms.append(summary)
            screen_series[channel] = series

        screenshot_path = _capture_screenshot(
            scope, out_dir, SimpleNamespace(profile="edge", arm="single")
        )
        (
            depmem_summary,
            depmem_summary_path,
            depmem_raw_path,
            depmem_series,
        ) = _capture_depmem_all_summary_and_series(scope, out_dir)

        scope_state = {
            "trigger_status": f"TriggerStatus.{status_text.lower()}",
            "initial_trigger_status": initial_status,
            "resumed_before_setup": resumed_before_setup,
            "timebase_scale": "0.0005 second",
            "trigger_snapshot": (
                "SDS1104TriggerConfiguration("
                f"status=<{status_text}>, "
                "trigger_type=<TriggerType.single: 'SINGle'>, "
                "single_trigger_mode=<SingleTriggerMode.edge: 'EDGE'>, "
                "holdoff=<Quantity(1e-07, 'second')>, "
                "edge_source=<TriggerSource.ch1: 'CH1'>, "
                "edge_coupling=<TriggerCoupling.dc: 'DC'>, "
                "edge_slope=<TriggerSlope.rise: 'RISE'>, "
                "edge_level=<Quantity(1.64, 'volt')>, "
                "video_source=None, video_standard=None, video_sync=None, video_line_number=None)"
            ),
            "trigger_sweep": "TriggerSweep.single",
            "raw_edge_level": _clean_reply(scope.query(":TRIGger:SINGle:EDGE:LEVel?")),
        }

        sample_rate_text = _metadata_sample_rate_text(screen_metadata)
        scope_html_data = _build_scope_html_data_from_series(
            args,
            scope_state,
            screen_series,
            memory_depth_text=str(len(next(iter(screen_series.values()))["y"])),
            sample_rate_text=sample_rate_text,
        )
        html_view_path, html_data_path = _render_scope_html_with_data(
            out_dir, scope_html_data, "scope_view"
        )

        depmem_view_path = None
        depmem_view_json_path = None
        if depmem_series:
            depmem_scope_data = _build_scope_html_data_from_series(
                args,
                scope_state,
                depmem_series,
                memory_depth_text=str(len(next(iter(depmem_series.values()))["y"])),
                sample_rate_text=depmem_summary["metadata"]["sample_rate"],
            )
            depmem_view_path, depmem_view_json_path = _render_scope_html_with_data(
                out_dir, depmem_scope_data, "depmem_all_view"
            )

        report_path = out_dir / "report.md"
        json_path = out_dir / "report.json"
        lines = [
            f"# OWON ESP32 Trigger Jig Run: {args.label}",
            "",
            f"- Timestamp: `{_timestamp().isoformat(timespec='seconds')}`",
            "- Profile: `edge`",
            f"- ESP32 port: `{args.esp_port}`",
            f"- Scope VID:PID: `{args.scope_vid}:{args.scope_pid}`",
            "- Arm command: `sequenced_raw_edge`",
            f"- Screenshot: `{Path(screenshot_path).name}`",
            "",
            "## Primary Scope Screen",
            "",
            f"![Primary scope screen]({Path(screenshot_path).name})",
            "",
            "## Derived Scope View",
            "",
            f"- [Open `scope_view.html`]({Path(html_view_path).name})",
            f"- [Open `scope_view.json`]({Path(html_data_path).name})",
            "",
            "## Scope State",
            "",
            f"- Initial trigger status: `{scope_state['initial_trigger_status']}`",
            f"- Resumed before setup: `{scope_state['resumed_before_setup']}`",
            f"- Trigger status: `{scope_state['trigger_status']}`",
            "- Timebase scale: `0.0005 second`",
            f"- Trigger sweep: `{scope_state['trigger_sweep']}`",
            f"- Raw edge level: `{scope_state['raw_edge_level']}`",
            "",
            "## ESP32 Serial Output",
            "",
            "```text",
            *esp_lines,
            "```",
            "",
            "## Waveforms",
            "",
            "| Channel | Samples | t_start (s) | t_end (s) | v_min (V) | v_max (V) | v_pp (V) | CSV | Plot |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
        ]
        for summary in waveforms:
            lines.append(
                f"| CH{summary.channel} | {summary.sample_count} | {summary.time_start_s:.6g} | "
                f"{summary.time_end_s:.6g} | {summary.voltage_min_v:.6g} | "
                f"{summary.voltage_max_v:.6g} | {summary.voltage_pp_v:.6g} | "
                f"`{Path(summary.csv_path).name}` | "
                f"`screen_ch{summary.channel}_plot.html` |"
            )
        lines.extend(
            [
                "",
                "## Screen Metadata",
                "",
                f"- [Open `screen_waveform_metadata.json`]({screen_metadata_path.name})",
                "",
                "## DEPMem:All Summary",
                "",
                f"- [Open `depmem_all_summary.json`]({depmem_summary_path.name})",
                f"- [Open `depmem_all_raw.bin`]({depmem_raw_path.name})",
            ]
        )
        if depmem_view_path is not None:
            lines.extend(
                [
                    f"- [Open `depmem_all_view.html`]({Path(depmem_view_path).name})",
                    f"- [Open `depmem_all_view.json`]({Path(depmem_view_json_path).name})",
                ]
            )

        waveform_comparison = {
            "bmp_name": Path(screenshot_path).name,
            "views": [
                {
                    "stem": "scope_view",
                    "title": "Screen `:DATA:WAVE:SCREen:CH<n>?`",
                    "html_name": Path(html_view_path).name,
                    "json_name": Path(html_data_path).name,
                }
            ],
            "families": {},
        }
        if depmem_view_path is not None:
            waveform_comparison["views"].append(
                {
                    "stem": "depmem_all_view",
                    "title": "Deep `:DATA:WAVE:DEPMem:All?` converted from raw bundle",
                    "html_name": Path(depmem_view_path).name,
                    "json_name": Path(depmem_view_json_path).name,
                }
            )

        channels = {}
        for channel in sorted(set(screen_series) & set(depmem_series)):
            channels[f"CH{channel}"] = _compare_waveform_series(
                "screen `:DATA:WAVE:SCREen:CH<n>?`",
                screen_series[channel],
                "deep `:DATA:WAVE:DEPMem:All?`",
                depmem_series[channel],
            )
        if channels:
            waveform_comparison["families"]["screen_vs_depmem_all"] = channels

        waveform_comparison_path = out_dir / "waveform_comparison.json"
        _safe_json_write(waveform_comparison_path, waveform_comparison)
        waveform_comparison_html_path = _render_waveform_comparison_html(
            out_dir, waveform_comparison
        )

        lines.extend(
            [
                "",
                "## Waveform Comparison",
                "",
                f"- [Open `waveform_comparison.html`]({waveform_comparison_html_path.name})",
                f"- [Open `waveform_comparison.json`]({waveform_comparison_path.name})",
                "",
                "| Family | Channel | A | B | Counts | Alignment | Mean dV | Max dV | Diff samples | Max dt |",
                "| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: |",
            ]
        )
        for family, family_channels in waveform_comparison["families"].items():
            for channel_name, metrics in family_channels.items():
                lines.append(
                    f"| `{family}` | `{channel_name}` | `{metrics['series_a']}` | "
                    f"`{metrics['series_b']}` | "
                    f"`{metrics['count_a']} vs {metrics['count_b']} (shared {metrics['aligned_count']})` | "
                    f"`{metrics['alignment']}` | "
                    f"{metrics['mean_abs_voltage_delta_v']:.6g} | "
                    f"{metrics['max_abs_voltage_delta_v']:.6g} | "
                    f"{metrics['diff_sample_count']} | "
                    f"{metrics['max_abs_time_delta_s']:.6g} |"
                )

        if trace_ctx.scpi_trace_path is not None:
            lines.extend(
                [
                    "",
                    "## Trace",
                    "",
                    f"- [Open `scpi_trace.jsonl`]({Path(trace_ctx.scpi_trace_path).name})",
                ]
            )
        report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        payload = {
            "label": args.label,
            "profile": "edge",
            "esp_port": args.esp_port,
            "scope_vid": args.scope_vid,
            "scope_pid": args.scope_pid,
            "arm": "sequenced_raw_edge",
            "trigger_status": scope_state["trigger_status"],
            "initial_trigger_status": scope_state["initial_trigger_status"],
            "resumed_before_setup": scope_state["resumed_before_setup"],
            "timebase_scale": scope_state["timebase_scale"],
            "trigger_snapshot": scope_state["trigger_snapshot"],
            "trigger_sweep": scope_state["trigger_sweep"],
            "raw_edge_level": scope_state["raw_edge_level"],
            "screenshot_path": str(screenshot_path),
            "html_view_path": str(html_view_path),
            "html_data_path": str(html_data_path),
            "screen_waveform_metadata_path": str(screen_metadata_path),
            "depmem_all_summary_path": str(depmem_summary_path),
            "depmem_all_raw_path": str(depmem_raw_path),
            "depmem_all_view_path": (
                None if depmem_view_path is None else str(depmem_view_path)
            ),
            "waveform_comparison_path": str(waveform_comparison_html_path),
            "waveform_comparison_json_path": str(waveform_comparison_path),
            "scpi_trace_path": (
                None if trace_ctx.scpi_trace_path is None else trace_ctx.scpi_trace_path
            ),
            "waveforms": [asdict(summary) for summary in waveforms],
            "esp_serial_lines": esp_lines,
        }
        json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return payload, report_path, json_path, waveforms
    finally:
        try:
            scope.disable_trace()
        except Exception:
            pass
        try:
            scope.close()
        except Exception:
            pass
