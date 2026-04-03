#!/usr/bin/env python
"""
Small command-line runner for the OWON ESP32 trigger jig.

Stable promoted flows:

- --capture-edge-pretty
- --capture-edge-pretty-burst

Debug and validation flows are delegated to internal helper modules.
"""

from __future__ import annotations

import argparse

from _owon_capture_common import _artifact_dir, _configure_esp, _open_serial
from _owon_capture_debug import (
    _build_edge_arming_cases,
    _build_verification_cases,
    _restore_stable_edge,
    _run_capture_case,
    _run_case_with_fresh_scope,
    _write_edge_arming_report,
    _write_verification_report,
)
from _owon_capture_stable import (
    _apply_pretty_edge_defaults,
    _is_pretty_edge_mode,
    _run_proven_edge_capture_case,
)


def build_arg_parser():
    parser = argparse.ArgumentParser(description="Run the OWON ESP32 trigger jig.")
    parser.add_argument("--esp-port", required=True)
    parser.add_argument("--esp-baud", type=int, default=115200)
    parser.add_argument("--label", default="owon_esp32_trigger_jig")
    parser.add_argument("--artifact-root", default="doc/examples/artifacts")

    parser.add_argument("--scope-vid", default="0x5345")
    parser.add_argument("--scope-pid", default="0x1234")
    parser.add_argument("--scope-timeout-s", type=float, default=5.0)
    parser.add_argument("--scope-settle-s", type=float, default=0.1)
    parser.add_argument("--scope-open-retry-s", type=float, default=30.0)
    parser.add_argument("--enable-scpi", action="store_true")
    parser.add_argument("--trace-scpi", action="store_true")
    parser.add_argument("--trace-state", action="store_true")
    parser.add_argument("--trace-dir", default=None)
    parser.add_argument("--strict-open-scpi", action="store_true")
    parser.add_argument(
        "--hard-reset-on-failure",
        dest="hard_reset_on_failure",
        action="store_true",
    )
    parser.add_argument(
        "--no-hard-reset-on-failure",
        dest="hard_reset_on_failure",
        action="store_false",
    )
    parser.set_defaults(hard_reset_on_failure=False)
    parser.add_argument("--reset-settle-s", type=float, default=1.5)
    parser.add_argument(
        "--restore-after-success",
        dest="restore_after_success",
        action="store_true",
    )
    parser.add_argument(
        "--no-restore-after-success",
        dest="restore_after_success",
        action="store_false",
    )
    parser.set_defaults(restore_after_success=True)
    parser.add_argument(
        "--restore-after-failure",
        dest="restore_after_failure",
        action="store_true",
    )
    parser.add_argument(
        "--no-restore-after-failure",
        dest="restore_after_failure",
        action="store_false",
    )
    parser.set_defaults(restore_after_failure=True)
    parser.add_argument(
        "--state-probe-style",
        choices=("full", "minimal", "off"),
        default="full",
    )
    parser.add_argument("--immediate-deep-probe", action="store_true")

    parser.add_argument(
        "--profile", choices=("edge", "pulse", "slope"), default="pulse"
    )
    parser.add_argument("--capture-edge-pretty", action="store_true")
    parser.add_argument("--capture-edge-pretty-burst", action="store_true")
    parser.add_argument("--verify-pulse", action="store_true")
    parser.add_argument("--verify-slope", action="store_true")
    parser.add_argument("--verify-edge-arming", action="store_true")
    parser.add_argument("--validate-waveforms", action="store_true")
    parser.add_argument("--arm", choices=("run", "single", "stop"), default="run")
    parser.add_argument(
        "--arm-method",
        choices=("legacy_single", "running_run"),
        default="legacy_single",
    )
    parser.add_argument(
        "--single-stop-first",
        dest="single_stop_first",
        action="store_true",
    )
    parser.add_argument(
        "--no-single-stop-first",
        dest="single_stop_first",
        action="store_false",
    )
    parser.set_defaults(single_stop_first=True)
    parser.add_argument("--capture-delay-s", type=float, default=0.5)
    parser.add_argument(
        "--finalize-method",
        choices=("none", "legacy_stop", "running_stop"),
        default="none",
    )
    parser.add_argument("--finalize-delay-s", type=float, default=0.2)
    parser.add_argument("--capture-channels", default=None)

    parser.add_argument("--ch1-scale-v-div", type=float, default=1.0)
    parser.add_argument("--ch2-scale-v-div", type=float, default=1.0)
    parser.add_argument("--ch3-scale-v-div", type=float, default=1.0)
    parser.add_argument("--ch1-probe", type=int, default=1)
    parser.add_argument("--ch2-probe", type=int, default=1)
    parser.add_argument("--ch3-probe", type=int, default=1)
    parser.add_argument("--ch1-position-div", type=float, default=1.0)
    parser.add_argument("--ch2-position-div", type=float, default=-2.0)
    parser.add_argument("--ch3-position-div", type=float, default=0.0)
    parser.add_argument("--timebase-s-div", type=float, default=50e-6)
    parser.add_argument("--trigger-level-v", type=float, default=1.65)
    parser.add_argument("--trigger-holdoff-ns", type=int, default=100)
    parser.add_argument(
        "--trigger-sweep", choices=("AUTO", "NORMal", "SINGle"), default=None
    )
    parser.add_argument("--edge-source", default="ch1")
    parser.add_argument("--edge-coupling", default="dc")
    parser.add_argument("--edge-slope", default="rise")
    parser.add_argument("--horizontal-offset-div", type=float, default=None)
    parser.add_argument("--memory-depth", type=int, default=None)
    parser.add_argument(
        "--measurement-display",
        choices=("keep", "on", "off"),
        default="keep",
    )

    parser.add_argument("--pulse-mode", choices=("burst", "single"), default="burst")
    parser.add_argument("--pulse-width-us", type=int, default=50)
    parser.add_argument("--pulse-gap-us", type=int, default=2000)
    parser.add_argument("--pulse-frame-us", type=int, default=20000)
    parser.add_argument("--slope-half-period-us", type=int, default=5000)

    parser.add_argument("--pulse-source", default="CH1")
    parser.add_argument("--pulse-sign", default=">")
    parser.add_argument("--pulse-trigger-time-us", type=float, default=50.0)
    parser.add_argument("--pulse-dir", default="POS")
    parser.add_argument("--pulse-coupling", default="DC")

    parser.add_argument("--slope-source", default="CH2")
    parser.add_argument("--slope-upper-v", type=float, default=2.4)
    parser.add_argument("--slope-lower-v", type=float, default=0.8)
    parser.add_argument("--slope-sign", default=">")
    parser.add_argument("--slope-trigger-time-us", type=float, default=50.0)
    parser.add_argument("--slope-edge", default="POS")
    return parser


def _normalize_args(args):
    verify_flags = [args.verify_pulse, args.verify_slope, args.verify_edge_arming]
    if sum(bool(flag) for flag in verify_flags) > 1:
        raise SystemExit(
            "Choose only one of --verify-pulse, --verify-slope, or --verify-edge-arming."
        )
    if _is_pretty_edge_mode(args) and any(verify_flags):
        raise SystemExit(
            "--capture-edge-pretty and --capture-edge-pretty-burst cannot be combined with verification modes."
        )

    if args.verify_edge_arming or args.validate_waveforms:
        args.strict_open_scpi = True
        args.hard_reset_on_failure = True
        args.restore_after_failure = False
        args.trace_scpi = True
        args.trace_state = True
    if _is_pretty_edge_mode(args):
        args.trace_scpi = True
        _apply_pretty_edge_defaults(args)

    if args.capture_channels is None:
        if args.verify_pulse or args.profile == "pulse":
            args.capture_channels = [1]
        elif args.verify_slope or args.profile == "slope":
            args.capture_channels = [2]
        else:
            args.capture_channels = [1, 2]
    else:
        args.capture_channels = [
            int(item.strip())
            for item in str(args.capture_channels).split(",")
            if item.strip()
        ]

    return args


def main():
    args = _normalize_args(build_arg_parser().parse_args())

    out_dir = _artifact_dir(args.artifact_root, args.label)
    out_dir.mkdir(parents=True, exist_ok=True)

    esp_lines = []
    if not _is_pretty_edge_mode(args):
        with _open_serial(args) as esp:
            esp_lines = _configure_esp(esp, args)

    if args.verify_edge_arming:
        summaries = []
        for case_args in _build_edge_arming_cases(args):
            case_dir = out_dir / case_args.label
            summary, _, _, _ = _run_case_with_fresh_scope(
                args, case_args, case_dir, esp_lines
            )
            summaries.append(summary)
        report_path, json_path = _write_edge_arming_report(out_dir, args, summaries)
        waveforms = []
    elif args.verify_pulse or args.verify_slope:
        summaries = []
        for case_args in _build_verification_cases(args):
            case_dir = out_dir / case_args.label
            summary, _, _, _ = _run_case_with_fresh_scope(
                args, case_args, case_dir, esp_lines
            )
            summaries.append(summary)
        report_path, json_path = _write_verification_report(out_dir, args, summaries)
        waveforms = []
    elif _is_pretty_edge_mode(args):
        _, report_path, json_path, waveforms = _run_proven_edge_capture_case(
            args, out_dir
        )
    else:
        from _owon_capture_common import _open_scope

        scope = _open_scope(args)
        summary = None
        try:
            summary, report_path, json_path, waveforms = _run_capture_case(
                scope, args, out_dir, esp_lines
            )
        finally:
            try:
                scope.disable_trace()
            except Exception:
                pass
            transport_failure = bool(
                summary is not None
                and summary.get("failure_class")
                in {
                    "transport_timeout",
                    "transport_pipe_error",
                    "malformed_length_prefix",
                }
            )
            if transport_failure:
                if args.restore_after_failure:
                    try:
                        _restore_stable_edge(scope, args)
                    except Exception:
                        pass
                scope.close(
                    reset_device=args.hard_reset_on_failure,
                    settle_time=args.reset_settle_s,
                )
            else:
                if args.restore_after_success:
                    try:
                        _restore_stable_edge(scope, args)
                    except Exception:
                        pass
                scope.close()

    print(f"Artifacts: {out_dir}")
    print(f"Markdown: {report_path}")
    print(f"JSON: {json_path}")
    for summary in waveforms:
        print(
            f"CH{summary.channel}: {summary.sample_count} samples, "
            f"Vpp={summary.voltage_pp_v:.6g} V, CSV={summary.csv_path}"
        )


if __name__ == "__main__":
    main()
