#!/usr/bin/env python
"""
Hardware integration tests for the OWON SDS1104 trigger API.

These tests are intentionally opt-in. Set ``IK_OWON_HARDWARE=1`` to run them
with a connected OWON SDS1104 / HANMATEK DOS1104 scope.
"""

# IMPORTS ####################################################################


import json
import os
import time

import pytest
import usb.core

import instruments as ik
from instruments.units import ureg as u
from tests import unit_eq

# CONSTANTS ##################################################################


pytestmark = pytest.mark.hardware


def _env_flag(name):
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name, default):
    return int(os.getenv(name, str(default)), 0)


def _scope_open_kwargs():
    return {
        "vid": _env_int("IK_OWON_USB_VID", ik.owon.OWONSDS1104.DEFAULT_USB_VID),
        "pid": _env_int("IK_OWON_USB_PID", ik.owon.OWONSDS1104.DEFAULT_USB_PID),
        "timeout": 2 * u.second,
        "enable_scpi": _env_flag("IK_OWON_ENABLE_SCPI"),
        "ignore_scpi_failure": True,
        "settle_time": float(os.getenv("IK_OWON_USB_SETTLE_TIME", "0.1")),
    }


def _health_check(scope):
    return {
        "trigger_status": scope.trigger_status,
        "timebase_scale": scope.timebase_scale,
    }


def _classify_hardware_failure(text):
    lowered = str(text).lower()
    if "timeout" in lowered or "timed out" in lowered:
        return "transport_timeout"
    if "pipe error" in lowered:
        return "transport_pipe_error"
    if "length-prefixed body" in lowered or "length mismatch" in lowered:
        return "malformed_length_prefix"
    if "deep_memory" in lowered or "deep-memory" in lowered or "depmem" in lowered:
        return "deep_memory_error"
    if "waveform" in lowered or "bmp" in lowered or "screen" in lowered:
        return "waveform_read_error"
    return "unknown_error"


def _clean_text_reply(reply):
    cleaned = reply.strip()
    if cleaned.endswith("->"):
        cleaned = cleaned[:-2].rstrip()
    return cleaned


def _assert_quantity_close(scope, label, actual, expected, rel=1e-6, abs_=1e-12):
    actual_converted = actual.to(expected.units)
    assert actual_converted.magnitude == pytest.approx(
        expected.magnitude, rel=rel, abs=abs_
    ), f"{label}: expected {expected!r}, got {actual!r}; health={_health_check(scope)!r}"


def _assert_readback(scope, label, actual, expected):
    if hasattr(actual, "units") and hasattr(expected, "units"):
        _assert_quantity_close(scope, label, actual, expected)
        return
    assert (
        actual == expected
    ), f"{label}: expected {expected!r}, got {actual!r}; health={_health_check(scope)!r}"


def _set_and_verify(scope, attr, value, expected=None):
    setattr(scope, attr, value)
    readback = getattr(scope, attr)
    _assert_readback(scope, attr, readback, value if expected is None else expected)
    _health_check(scope)
    return readback


def _restore_trigger_configuration(scope, config):
    scope.single_trigger_mode = config.single_trigger_mode
    scope.trigger_holdoff = config.holdoff
    if config.trigger_sweep is not None:
        scope.trigger_sweep = config.trigger_sweep

    if config.single_trigger_mode == scope.SingleTriggerMode.edge:
        if config.edge_source is not None:
            scope.trigger_source = config.edge_source
        if config.edge_coupling is not None:
            scope.trigger_coupling = config.edge_coupling
        if config.edge_slope is not None:
            scope.trigger_slope = config.edge_slope
        if config.edge_level is not None:
            scope.trigger_level = config.edge_level
        return

    if config.single_trigger_mode == scope.SingleTriggerMode.video:
        if config.video_standard is not None:
            scope.video_trigger_standard = config.video_standard
        if config.video_sync is not None:
            scope.video_trigger_sync = config.video_sync
        if (
            config.video_sync == scope.VideoSync.lnum
            and config.video_line_number is not None
        ):
            scope.video_trigger_line_number = config.video_line_number


@pytest.fixture
def hardware_scope():
    if not _env_flag("IK_OWON_HARDWARE"):
        pytest.skip("Set IK_OWON_HARDWARE=1 to run OWON hardware tests.")

    last_exc = None
    scope = None
    deadline = time.monotonic() + float(os.getenv("IK_OWON_OPEN_RETRY_S", "30"))
    while time.monotonic() < deadline:
        try:
            scope = ik.owon.OWONSDS1104.open_usb(**_scope_open_kwargs())
            break
        except (OSError, usb.core.USBError) as exc:
            last_exc = exc
            time.sleep(0.5)

    if scope is None:
        raise last_exc if last_exc is not None else OSError("No such device found.")

    try:
        yield scope
    finally:
        scope.close()


@pytest.fixture
def single_trigger_scope(hardware_scope):
    if hardware_scope.trigger_type != hardware_scope.TriggerType.single:
        pytest.skip(
            "These tests require trigger_type == SINGle so the original top-level "
            "trigger selection remains recoverable."
        )

    original = hardware_scope.read_trigger_configuration()
    try:
        yield hardware_scope
    finally:
        _restore_trigger_configuration(hardware_scope, original)
        _health_check(hardware_scope)


def _open_hardware_scope_once():
    return ik.owon.OWONSDS1104.open_usb(**_scope_open_kwargs())


def _open_hardware_scope_strict_once():
    kwargs = _scope_open_kwargs()
    kwargs["enable_scpi"] = True
    kwargs["ignore_scpi_failure"] = False
    return ik.owon.OWONSDS1104.open_usb(**kwargs)


def test_trigger_query_smoke(hardware_scope):
    status = hardware_scope.trigger_status
    trigger_type = hardware_scope.trigger_type
    mode = hardware_scope.single_trigger_mode
    holdoff = hardware_scope.trigger_holdoff
    health = _health_check(hardware_scope)

    assert isinstance(status, hardware_scope.TriggerStatus), health
    assert isinstance(trigger_type, hardware_scope.TriggerType), health
    assert isinstance(mode, hardware_scope.SingleTriggerMode), health
    assert holdoff.check("[time]"), health

    if mode == hardware_scope.SingleTriggerMode.edge:
        assert isinstance(hardware_scope.trigger_source, hardware_scope.TriggerSource)
        assert isinstance(
            hardware_scope.trigger_coupling, hardware_scope.TriggerCoupling
        )
        assert isinstance(hardware_scope.trigger_slope, hardware_scope.TriggerSlope)
        assert hardware_scope.trigger_level.units == u.volt

    if mode == hardware_scope.SingleTriggerMode.video:
        assert isinstance(
            hardware_scope.video_trigger_source, hardware_scope.TriggerSource
        )
        assert isinstance(
            hardware_scope.video_trigger_standard, hardware_scope.VideoStandard
        )
        assert isinstance(hardware_scope.video_trigger_sync, hardware_scope.VideoSync)
        assert isinstance(hardware_scope.video_trigger_line_number, int)


def test_edge_trigger_write_readback(single_trigger_scope):
    scope = single_trigger_scope
    scope.single_trigger_mode = scope.SingleTriggerMode.edge
    _health_check(scope)

    _set_and_verify(scope, "trigger_source", scope.TriggerSource.ch1)
    _set_and_verify(scope, "trigger_coupling", scope.TriggerCoupling.dc)
    _set_and_verify(scope, "trigger_coupling", scope.TriggerCoupling.ac)
    _set_and_verify(scope, "trigger_slope", scope.TriggerSlope.rise)
    _set_and_verify(scope, "trigger_slope", scope.TriggerSlope.fall)
    _set_and_verify(scope, "trigger_level", 480 * u.millivolt)

    for holdoff in (100 * u.nanosecond, 1 * u.microsecond, 1 * u.millisecond):
        _set_and_verify(scope, "trigger_holdoff", holdoff)


def test_video_trigger_write_readback(single_trigger_scope):
    scope = single_trigger_scope
    scope.single_trigger_mode = scope.SingleTriggerMode.video
    _health_check(scope)

    for standard in (
        scope.VideoStandard.pal,
        scope.VideoStandard.ntsc,
        scope.VideoStandard.secam,
    ):
        _set_and_verify(scope, "video_trigger_standard", standard)

    for sync in (scope.VideoSync.field, scope.VideoSync.line, scope.VideoSync.lnum):
        _set_and_verify(scope, "video_trigger_sync", sync)

    _set_and_verify(scope, "video_trigger_line_number", 2)


def test_video_trigger_source_write_readback(single_trigger_scope):
    scope = single_trigger_scope
    scope.single_trigger_mode = scope.SingleTriggerMode.video
    _health_check(scope)

    for source in (scope.TriggerSource.ch1, scope.TriggerSource.ch2):
        _set_and_verify(scope, "video_trigger_source", source)


def test_trigger_mode_switch_soak(single_trigger_scope):
    scope = single_trigger_scope
    for _ in range(20):
        scope.single_trigger_mode = scope.SingleTriggerMode.edge
        assert scope.single_trigger_mode == scope.SingleTriggerMode.edge, _health_check(scope)
        scope.single_trigger_mode = scope.SingleTriggerMode.video
        assert scope.single_trigger_mode == scope.SingleTriggerMode.video, _health_check(scope)
        _health_check(scope)


def test_trigger_holdoff_soak(single_trigger_scope):
    scope = single_trigger_scope
    for _ in range(20):
        for holdoff in (100 * u.nanosecond, 1 * u.microsecond, 1 * u.millisecond):
            readback = _set_and_verify(scope, "trigger_holdoff", holdoff)
            unit_eq(readback.to(holdoff.units), holdoff)


def test_video_trigger_soak(single_trigger_scope):
    scope = single_trigger_scope
    scope.single_trigger_mode = scope.SingleTriggerMode.video

    for _ in range(10):
        for standard in (
            scope.VideoStandard.pal,
            scope.VideoStandard.ntsc,
            scope.VideoStandard.secam,
        ):
            _set_and_verify(scope, "video_trigger_standard", standard)

        for sync in (scope.VideoSync.field, scope.VideoSync.line, scope.VideoSync.lnum):
            _set_and_verify(scope, "video_trigger_sync", sync)

        _set_and_verify(scope, "video_trigger_line_number", 2)


def test_single_status_soak(single_trigger_scope):
    scope = single_trigger_scope
    for _ in range(10):
        scope.single(stop_first=True)
        try:
            status = scope.wait_for_trigger_status(
                scope.TriggerStatus.ready,
                timeout=500 * u.millisecond,
                poll_interval=50 * u.millisecond,
            )
        except TimeoutError:
            try:
                status = scope.wait_for_trigger_status(
                    scope.TriggerStatus.trig,
                    timeout=2 * u.second,
                    poll_interval=50 * u.millisecond,
                )
            except TimeoutError:
                try:
                    status = scope.wait_for_trigger_status(
                        scope.TriggerStatus.auto,
                        timeout=500 * u.millisecond,
                        poll_interval=50 * u.millisecond,
                    )
                except TimeoutError:
                    status = scope.wait_for_trigger_status(
                        scope.TriggerStatus.stop,
                        timeout=500 * u.millisecond,
                        poll_interval=50 * u.millisecond,
                    )
        assert isinstance(status, scope.TriggerStatus), _health_check(scope)
        _health_check(scope)


@pytest.mark.skipif(
    not _env_flag("IK_OWON_RUN_EXPERIMENTAL"),
    reason="Set IK_OWON_RUN_EXPERIMENTAL=1 to probe unpromoted commands.",
)
def test_trigger_sweep_probe_experimental(single_trigger_scope):
    scope = single_trigger_scope
    original = scope.query(":TRIGger:SINGle:SWEEp?")
    _health_check(scope)

    for value in ("AUTO", "NORMal", "SINGle"):
        scope.sendcmd(f":TRIGger:SINGle:SWEEp {value}")
        readback = _clean_text_reply(scope.query(":TRIGger:SINGle:SWEEp?")).upper()
        health = _health_check(scope)
        assert (
            readback == value.upper()
        ), f"trigger sweep probe: wrote {value!r}, got {readback!r}; health={health!r}"

    scope.sendcmd(f":TRIGger:SINGle:SWEEp {_clean_text_reply(original)}")
    _health_check(scope)


@pytest.mark.skipif(
    not _env_flag("IK_OWON_FRONT_PANEL_COMPAT"),
    reason="Set IK_OWON_FRONT_PANEL_COMPAT=1 after placing the scope in the desired front-panel mode.",
)
def test_front_panel_compatibility_manual(hardware_scope):
    mode = hardware_scope.single_trigger_mode
    trigger_type = hardware_scope.trigger_type
    health = _health_check(hardware_scope)

    assert isinstance(trigger_type, hardware_scope.TriggerType), health
    assert isinstance(mode, hardware_scope.SingleTriggerMode), health

    if mode == hardware_scope.SingleTriggerMode.pulse:
        assert hardware_scope.single_trigger_mode == hardware_scope.SingleTriggerMode.pulse
    elif mode == hardware_scope.SingleTriggerMode.slope:
        assert hardware_scope.single_trigger_mode == hardware_scope.SingleTriggerMode.slope
    elif mode == hardware_scope.SingleTriggerMode.edge:
        assert isinstance(hardware_scope.trigger_coupling, hardware_scope.TriggerCoupling)
        assert isinstance(hardware_scope.trigger_source, hardware_scope.TriggerSource)
    elif mode == hardware_scope.SingleTriggerMode.video:
        assert isinstance(
            hardware_scope.video_trigger_standard, hardware_scope.VideoStandard
        )


@pytest.mark.skipif(
    not _env_flag("IK_OWON_EDGE_ARMING_MATRIX"),
    reason="Set IK_OWON_EDGE_ARMING_MATRIX=1 to run the DOS1104 edge-arming matrix.",
)
def test_edge_arming_matrix_experimental(tmp_path):
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
    results = []

    for label, sweep, arm_method, stop_first, finalize_method in cases:
        result = {
            "label": label,
            "trigger_sweep": sweep,
            "arm_method": arm_method,
            "single_stop_first": stop_first,
            "finalize_method": finalize_method,
        }
        scope = None
        try:
            scope = _open_hardware_scope_once()
            scope.sendcmd(":TRIGger:TYPE SINGle")
            scope.single_trigger_mode = scope.SingleTriggerMode.edge
            scope.trigger_source = scope.TriggerSource.ch1
            scope.trigger_coupling = scope.TriggerCoupling.dc
            scope.trigger_slope = scope.TriggerSlope.rise
            scope.trigger_level = 480 * u.millivolt
            scope.trigger_holdoff = 100 * u.nanosecond
            scope.trigger_sweep = scope.TriggerSweep(sweep)
            scope.arm_single(
                stop_first=stop_first,
                arm_method=arm_method,
                settle_time=0.05,
            )
            time.sleep(0.5)
            result["trigger_status_before_reads"] = str(scope.trigger_status)
            if finalize_method != "none":
                scope.freeze_acquisition(method=finalize_method, settle_time=0.2)
            result["trigger_status_after_finalize"] = str(scope.trigger_status)

            try:
                result["bmp_len"] = len(scope.read_screen_bmp())
            except Exception as exc:
                result["screenshot_error"] = f"{type(exc).__name__}: {exc}"
            try:
                result["screen_metadata"] = scope.read_waveform_metadata().get("SAMPLE", {})
            except Exception as exc:
                result["waveform_read_error"] = f"{type(exc).__name__}: {exc}"
            try:
                result["deep_metadata"] = scope.read_deep_memory_metadata().get("SAMPLE", {})
                result["deep_metadata_ok"] = True
            except Exception as exc:
                result["deep_metadata_ok"] = False
                result["deep_memory_error"] = f"{type(exc).__name__}: {exc}"
            try:
                result["deep_ch1_samples"] = len(scope.read_deep_memory_channel(1)[1])
                result["deep_ch1_ok"] = True
            except Exception as exc:
                result["deep_ch1_ok"] = False
                result["deep_ch1_error"] = f"{type(exc).__name__}: {exc}"
            result["failure_class"] = _classify_hardware_failure(
                result.get("deep_memory_error")
                or result.get("deep_ch1_error")
                or result.get("waveform_read_error")
                or result.get("screenshot_error")
                or ""
            )
        except Exception as exc:  # pragma: no cover - bench-only failure path
            result["session_error"] = f"{type(exc).__name__}: {exc}"
            result["failure_class"] = _classify_hardware_failure(result["session_error"])
        finally:
            if scope is not None:
                try:
                    scope.close()
                except Exception:
                    pass
        results.append(result)

    out_path = tmp_path / "edge_arming_matrix_results.json"
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    assert out_path.exists()
    assert len(results) == 10


@pytest.mark.skipif(
    not _env_flag("IK_OWON_TRIGGER_TRANSITION_PROBE"),
    reason="Set IK_OWON_TRIGGER_TRANSITION_PROBE=1 to run the DOS1104 trigger transition probe.",
)
def test_trigger_transition_probe_experimental(tmp_path):
    cases = [
        ("control_auto_head", "AUTO", "control"),
        ("normal_set_only_head", "NORMal", "set_only"),
        ("normal_arm_legacy_stopfirst_head", "NORMal", "arm_stopfirst"),
    ]
    results = []

    for label, sweep, behavior in cases:
        result = {
            "label": label,
            "sweep": sweep,
            "behavior": behavior,
        }
        scope = None
        trace_path = tmp_path / f"{label}_scpi_trace.jsonl"
        try:
            scope = _open_hardware_scope_strict_once()
            scope.enable_trace(trace_path)
            scope.sendcmd(":TRIGger:TYPE SINGle")
            scope.single_trigger_mode = scope.SingleTriggerMode.edge
            scope.trigger_source = scope.TriggerSource.ch1
            scope.trigger_coupling = scope.TriggerCoupling.dc
            scope.trigger_slope = scope.TriggerSlope.rise
            scope.trigger_level = 480 * u.millivolt
            scope.trigger_holdoff = 100 * u.nanosecond
            scope.trigger_sweep = scope.TriggerSweep.auto
            result["baseline_status"] = str(scope.trigger_status)
            result["baseline_sweep"] = str(scope.trigger_sweep)

            if behavior == "set_only":
                scope.trigger_sweep = scope.TriggerSweep.normal
                time.sleep(0.05)
            elif behavior == "arm_stopfirst":
                scope.trigger_sweep = scope.TriggerSweep.normal
                time.sleep(0.05)
                scope.single(stop_first=True, arm_method="legacy_single")

            try:
                result["deep_metadata"] = scope.read_deep_memory_metadata().get("SAMPLE", {})
                result["deep_head_ok"] = True
            except Exception as exc:
                result["deep_head_ok"] = False
                result["session_error"] = f"{type(exc).__name__}: {exc}"
                result["failure_class"] = _classify_hardware_failure(result["session_error"])
                raise

            try:
                result["deep_ch1_samples"] = len(scope.read_deep_memory_channel(1)[1])
                result["deep_ch1_ok"] = True
            except Exception as exc:
                result["deep_ch1_ok"] = False
                result["deep_ch1_error"] = f"{type(exc).__name__}: {exc}"
                result["failure_class"] = _classify_hardware_failure(result["deep_ch1_error"])
                raise
        except Exception as exc:  # pragma: no cover - bench-only path
            if "session_error" not in result:
                result["session_error"] = f"{type(exc).__name__}: {exc}"
                result["failure_class"] = _classify_hardware_failure(result["session_error"])
        finally:
            if scope is not None:
                try:
                    scope.disable_trace()
                except Exception:
                    pass
                try:
                    if result.get("failure_class") in {
                        "transport_timeout",
                        "transport_pipe_error",
                        "malformed_length_prefix",
                    }:
                        scope.close(reset_device=True, settle_time=1.5)
                    else:
                        scope.close()
                except Exception:
                    pass
        result["trace_path"] = str(trace_path)
        results.append(result)

    out_path = tmp_path / "trigger_transition_probe_results.json"
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    assert out_path.exists()
    assert len(results) == 3
