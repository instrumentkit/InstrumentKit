#!/usr/bin/env python
"""
Tests for the OWON SDS1104 oscilloscope driver.
"""

# IMPORTS ####################################################################


from io import BytesIO
import json
import struct

import pytest
import usb.core

import instruments as ik
import instruments.owon.sds1104 as owon_sds1104
from instruments.abstract_instruments.comm import LoopbackCommunicator
from instruments.units import ureg as u
from tests import expected_protocol, unit_eq

# TESTS ######################################################################


def _make_length_prefixed_payload(body):
    return struct.pack("<I", len(body)) + body


def _make_binary_scope(binary_replies=None, exact_replies=None):
    stdout = BytesIO()
    comm = LoopbackCommunicator(BytesIO(), stdout)
    binary_replies = list(binary_replies or [])
    exact_replies = list(exact_replies or [])

    def read_binary(size=-1):
        assert size == -1
        payload = binary_replies.pop(0)
        if isinstance(payload, Exception):
            raise payload
        return payload

    def read_exact(size):
        payload = exact_replies.pop(0)
        if isinstance(payload, Exception):
            raise payload
        return payload

    comm.read_binary = read_binary
    comm.read_exact = read_exact
    return ik.owon.OWONSDS1104(comm), stdout


class _PartialReadError(OSError):
    def __init__(self, message, partial=b""):
        super().__init__(message)
        self.partial = partial


def test_name_cleans_prompt_suffix():
    with expected_protocol(
        ik.owon.OWONSDS1104, ["*IDN?"], ["OWON,SDS1104,1234,V1.0->"]
    ) as scope:
        assert scope.name == "OWON,SDS1104,1234,V1.0"


def test_channel_proxy():
    with expected_protocol(ik.owon.OWONSDS1104, [], []) as scope:
        assert scope.channel[0].name == "CH1"
        assert scope.channel[3].name == "CH4"


def test_channel_display():
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [":CH1:DISP?", ":CH2:DISP ON"],
        ["1"],
    ) as scope:
        assert scope.channel[0].display is True
        scope.channel[1].display = True


def test_channel_display_type_error():
    with expected_protocol(ik.owon.OWONSDS1104, [], []) as scope:
        with pytest.raises(TypeError) as err:
            scope.channel[0].display = "ON"
        assert (
            err.value.args[0] == "Display state must be specified with a boolean value."
        )


def test_channel_coupling():
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [":CH1:COUP?", ":CH2:COUP AC"],
        ["DC"],
    ) as scope:
        assert scope.channel[0].coupling == scope.Coupling.dc
        scope.channel[1].coupling = scope.Coupling.ac


def test_channel_coupling_type_error():
    with expected_protocol(ik.owon.OWONSDS1104, [], []) as scope:
        with pytest.raises(TypeError) as err:
            scope.channel[0].coupling = "DC"
        assert (
            err.value.args[0]
            == "Coupling setting must be a `OWONSDS1104.Coupling` value."
        )


def test_channel_probe():
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [":CH1:PROB?", ":CH2:PROB 100X"],
        ["10X"],
    ) as scope:
        assert scope.channel[0].probe_attenuation == 10
        scope.channel[1].probe_attenuation = 100


def test_channel_probe_value_error():
    with expected_protocol(ik.owon.OWONSDS1104, [], []) as scope:
        with pytest.raises(ValueError) as err:
            scope.channel[0].probe_attenuation = 3
        assert (
            err.value.args[0] == "Probe attenuation must be one of 1, 10, 100, or 1000."
        )


def test_channel_scale():
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [":CH1:SCAL?", ":CH2:SCAL 500mv"],
        ["100mV"],
    ) as scope:
        unit_eq(scope.channel[0].scale, 0.1 * u.volt)
        scope.channel[1].scale = 0.5 * u.volt


def test_channel_scale_value_error():
    with expected_protocol(ik.owon.OWONSDS1104, [], []) as scope:
        with pytest.raises(ValueError) as err:
            scope.channel[0].scale = 3.0 * u.volt
        assert (
            err.value.args[0]
            == "Unsupported vertical scale. Must be one of the documented discrete values."
        )


def test_channel_offset():
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [":CH1:OFFS?", ":CH2:OFFS 0.25"],
        ["-0.5"],
    ) as scope:
        unit_eq(scope.channel[0].offset, -0.5 * u.volt)
        scope.channel[1].offset = 0.25 * u.volt


def test_channel_position():
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [":CH1:POS?", ":CH2:POS -1.5"],
        ["0.25"],
    ) as scope:
        assert scope.channel[0].position == pytest.approx(0.25)
        scope.channel[1].position = -1.5


def test_channel_invert():
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [":CH1:INVErse?", ":CH2:INVErse OFF"],
        ["ON"],
    ) as scope:
        assert scope.channel[0].invert is True
        scope.channel[1].invert = False


def test_channel_invert_type_error():
    with expected_protocol(ik.owon.OWONSDS1104, [], []) as scope:
        with pytest.raises(TypeError) as err:
            scope.channel[0].invert = 1
        assert (
            err.value.args[0] == "Invert state must be specified with a boolean value."
        )


def test_acquire_mode():
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [":ACQUire:Mode?", ":ACQUire:Mode AVERage"],
        ["SAMP"],
    ) as scope:
        assert scope.acquire_mode == scope.AcquisitionMode.sample
        scope.acquire_mode = scope.AcquisitionMode.average


def test_acquire_mode_type_error():
    with expected_protocol(ik.owon.OWONSDS1104, [], []) as scope:
        with pytest.raises(TypeError) as err:
            scope.acquire_mode = "SAMPle"
        assert (
            err.value.args[0]
            == 'Acquisition mode must be one of "SAMPle", "AVERage", or "PEAK".'
        )


def test_acquire_averages():
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [":ACQUire:average:num?", ":ACQUire:average:num 64"],
        ["16"],
    ) as scope:
        assert scope.acquire_averages == 16
        scope.acquire_averages = 64


def test_acquire_averages_value_error():
    with expected_protocol(ik.owon.OWONSDS1104, [], []) as scope:
        with pytest.raises(ValueError) as err:
            scope.acquire_averages = 8
        assert (
            err.value.args[0]
            == "Average count not supported by instrument; must be one of {4, 16, 64, 128}."
        )


def test_memory_depth():
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [":ACQUIRE:DEPMEM?", ":ACQUIRE:DEPMEM 100K"],
        ["10K"],
    ) as scope:
        assert scope.memory_depth == 10_000
        scope.memory_depth = 100_000


def test_memory_depth_value_error():
    with expected_protocol(ik.owon.OWONSDS1104, [], []) as scope:
        with pytest.raises(ValueError) as err:
            scope.memory_depth = 42
        assert (
            err.value.args[0]
            == "Memory depth must be one of 1K, 5K, 10K, 100K, 1M, or 10M. 20M and 40M are documented, but are not yet verified in this driver."
        )


def test_timebase_scale():
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [":HORIzontal:Scale?", ":HORIzontal:Scale 10ms"],
        ["1ms"],
    ) as scope:
        unit_eq(scope.timebase_scale, 1e-3 * u.second)
        scope.timebase_scale = 10e-3 * u.second


def test_timebase_scale_value_error():
    with expected_protocol(ik.owon.OWONSDS1104, [], []) as scope:
        with pytest.raises(ValueError) as err:
            scope.timebase_scale = 3e-3 * u.second
        assert (
            err.value.args[0]
            == "Unsupported timebase scale. Must be one of the documented discrete values."
        )


def test_horizontal_offset():
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [":HORIzontal:OFFSET?", ":HORIzontal:OFFSET 1.5"],
        ["0.25"],
    ) as scope:
        assert scope.horizontal_offset == pytest.approx(0.25)
        scope.horizontal_offset = 1.5


def test_measurement_display_enabled():
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [":MEASUrement:DISPlay?", ":MEASUrement:DISPlay OFF"],
        ["ON"],
    ) as scope:
        assert scope.measurement_display_enabled is True
        scope.measurement_display_enabled = False


def test_measurement_display_enabled_type_error():
    with expected_protocol(ik.owon.OWONSDS1104, [], []) as scope:
        with pytest.raises(TypeError) as err:
            scope.measurement_display_enabled = "OFF"
        assert (
            err.value.args[0]
            == "Measurement display state must be specified with a boolean value."
        )


def test_run_stop():
    with expected_protocol(ik.owon.OWONSDS1104, [":RUN", ":STOP"], []) as scope:
        scope.run()
        scope.stop()


def test_scpi_trace_sendcmd_and_query(tmp_path):
    trace_path = tmp_path / "scpi_trace.jsonl"
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [":RUN", ":TRIGger:STATUS?"],
        ["READy"],
    ) as scope:
        scope.enable_trace(trace_path)
        scope.run()
        assert scope.trigger_status == scope.TriggerStatus.ready
        scope.disable_trace()

    events = [json.loads(line) for line in trace_path.read_text(encoding="utf-8").splitlines()]
    assert [event["direction"] for event in events] == ["sendcmd", "query"]
    assert events[0]["command"] == ":RUN"
    assert events[0]["ok"] is True
    assert events[1]["command"] == ":TRIGger:STATUS?"
    assert events[1]["reply_kind"] == "text"
    assert events[1]["reply_text"] == "READy"
    assert events[1]["ok"] is True


def test_scpi_trace_binary_queries(tmp_path):
    trace_path = tmp_path / "scpi_trace.jsonl"
    metadata = {
        "CHANNEL": [{"SCALE": "100mV", "PROBE": "10X", "OFFSET": "0"}] * 4,
        "SAMPLE": {"SAMPLERATE": "1MS/s", "DATALEN": "4"},
        "TIMEBASE": {"HOFFSET": "0"},
    }
    metadata_payload = b"\x00\x00\x00\x00" + json.dumps(metadata).encode("ascii")
    waveform_payload = b"\x00\x00\x00\x00" + struct.pack("<4h", 0, 82, -82, 410)
    bmp_body = b"BM" + struct.pack("<I", 14) + b"\x00\x00\x00\x00" + b"\x36\x00\x00\x00"

    scope, _ = _make_binary_scope(
        binary_replies=[metadata_payload],
        exact_replies=[
            struct.pack("<I", len(bmp_body)),
            bmp_body,
            waveform_payload,
        ],
    )
    scope.enable_trace(trace_path)
    assert scope.read_screen_bmp() == bmp_body
    x_axis, y_axis = scope.read_waveform(1)
    assert len(x_axis) == 4
    assert len(y_axis) == 4
    scope.disable_trace()

    events = [json.loads(line) for line in trace_path.read_text(encoding="utf-8").splitlines()]
    assert [event["direction"] for event in events] == [
        "binary_length_prefixed_query",
        "binary_query",
        "binary_query_exact",
    ]
    assert events[0]["command"] == ":DATA:WAVE:SCREen:BMP?"
    assert events[0]["phase"] == "complete"
    assert events[0]["header_length"] == len(bmp_body)
    assert events[0]["payload_length"] == len(bmp_body)
    assert events[1]["command"] == ":DATA:WAVE:SCREen:HEAD?"
    assert events[1]["phase"] == "read"
    assert events[1]["payload_length"] == len(metadata_payload)
    assert events[2]["command"] == ":DATA:WAVE:SCREEN:CH1?"
    assert events[2]["phase"] == "read"
    assert events[2]["expected_length"] == len(waveform_payload)
    assert events[2]["payload_length"] == len(waveform_payload)


def test_scpi_trace_length_prefixed_header_timeout(tmp_path):
    trace_path = tmp_path / "scpi_trace.jsonl"
    scope, _ = _make_binary_scope(exact_replies=[usb.core.USBTimeoutError("timeout")])
    scope.enable_trace(trace_path)
    with pytest.raises(usb.core.USBTimeoutError):
        scope._query_length_prefixed_binary(":DATA:WAVE:DEPMEM:HEAD?")
    events = [json.loads(line) for line in trace_path.read_text(encoding="utf-8").splitlines()]
    assert events[-1]["direction"] == "binary_length_prefixed_query"
    assert events[-1]["ok"] is False
    assert events[-1]["phase"] == "header"


def test_scpi_trace_length_prefixed_partial_header(tmp_path):
    trace_path = tmp_path / "scpi_trace.jsonl"
    scope, _ = _make_binary_scope(
        exact_replies=[_PartialReadError("short header", partial=b"\x01\x02")]
    )
    scope.enable_trace(trace_path)
    with pytest.raises(_PartialReadError):
        scope._query_length_prefixed_binary(":DATA:WAVE:DEPMEM:HEAD?")
    events = [json.loads(line) for line in trace_path.read_text(encoding="utf-8").splitlines()]
    assert events[-1]["phase"] == "header"
    assert events[-1]["header_bytes_received"] == 2
    assert events[-1]["header_preview_hex"] == "0102"


def test_scpi_trace_length_prefixed_body_timeout(tmp_path):
    trace_path = tmp_path / "scpi_trace.jsonl"
    scope, _ = _make_binary_scope(
        exact_replies=[
            struct.pack("<I", 10),
            _PartialReadError("body timeout", partial=b"\xAA\xBB\xCC"),
        ]
    )
    scope.enable_trace(trace_path)
    with pytest.raises(_PartialReadError):
        scope._query_length_prefixed_binary(":DATA:WAVE:DEPMEM:HEAD?")
    events = [json.loads(line) for line in trace_path.read_text(encoding="utf-8").splitlines()]
    assert events[-1]["phase"] == "body"
    assert events[-1]["body_length_expected"] == 10
    assert events[-1]["body_bytes_received"] == 3


def test_scpi_trace_binary_query_exact_write_failure(tmp_path):
    trace_path = tmp_path / "scpi_trace.jsonl"
    scope, _ = _make_binary_scope()
    scope.enable_trace(trace_path)
    scope._file.write_raw = lambda msg: (_ for _ in ()).throw(OSError("write fail"))
    with pytest.raises(OSError):
        scope._binary_query_exact(":DATA:WAVE:SCREEN:CH1?", 12)
    events = [json.loads(line) for line in trace_path.read_text(encoding="utf-8").splitlines()]
    assert events[-1]["direction"] == "binary_query_exact"
    assert events[-1]["phase"] == "write"
    assert events[-1]["ok"] is False


def test_scpi_trace_binary_query_exact_read_failure(tmp_path):
    trace_path = tmp_path / "scpi_trace.jsonl"
    scope, _ = _make_binary_scope(exact_replies=[_PartialReadError("read fail", partial=b"\x10\x20")])
    scope.enable_trace(trace_path)
    with pytest.raises(_PartialReadError):
        scope._binary_query_exact(":DATA:WAVE:SCREEN:CH1?", 12)
    events = [json.loads(line) for line in trace_path.read_text(encoding="utf-8").splitlines()]
    assert events[-1]["direction"] == "binary_query_exact"
    assert events[-1]["phase"] == "read"
    assert events[-1]["expected_length"] == 12
    assert events[-1]["bytes_received"] == 2
    assert events[-1]["header_preview_hex"] == "1020"


def test_close_reset_device(monkeypatch):
    with expected_protocol(ik.owon.OWONSDS1104, [], []) as scope:
        called = {"flush": 0, "close": 0, "reset": 0, "dispose": 0}

        def flush_input():
            called["flush"] += 1

        def close_transport():
            called["close"] += 1

        class DummyDev:
            def reset(self_inner):
                called["reset"] += 1

        monkeypatch.setattr(
            owon_sds1104.usb.util,
            "dispose_resources",
            lambda dev: called.__setitem__("dispose", called["dispose"] + 1),
        )
        scope._file.flush_input = flush_input
        scope._file.close = close_transport
        scope._file._dev = DummyDev()

        scope.close(reset_device=True, settle_time=0.0)

        assert called["flush"] == 1
        assert called["close"] == 1
        assert called["reset"] == 1
        assert called["dispose"] == 1


def test_trigger_sweep_property():
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [
            ":TRIGger:SINGle:SWEEp?",
            ":TRIGger:SINGle:SWEEp?",
            ":TRIGger:SINGle:SWEEp?",
            ":TRIGger:SINGle:SWEEp AUTO",
        ],
        ["AUTO", "NORMal", "SINGle"],
    ) as scope:
        assert scope.trigger_sweep == scope.TriggerSweep.auto
        assert scope.trigger_sweep == scope.TriggerSweep.normal
        assert scope.trigger_sweep == scope.TriggerSweep.single
        scope.trigger_sweep = scope.TriggerSweep.auto


def test_trigger_sweep_type_error():
    with expected_protocol(ik.owon.OWONSDS1104, [], []) as scope:
        with pytest.raises(TypeError) as err:
            scope.trigger_sweep = "AUTO"
        assert (
            err.value.args[0]
            == "Trigger sweep must be specified with a `OWONSDS1104.TriggerSweep` value."
        )


def test_running_state_helpers():
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [":RUNning RUN", ":RUNning STOP", ":RUNning RUN", ":RUNning STOP"],
        [],
    ) as scope:
        scope.set_running_state(scope.RunningState.run)
        scope.set_running_state(scope.RunningState.stop)
        scope.run_front_panel()
        scope.stop_front_panel()


def test_running_state_type_error():
    with expected_protocol(ik.owon.OWONSDS1104, [], []) as scope:
        with pytest.raises(TypeError) as err:
            scope.set_running_state("RUN")
        assert (
            err.value.args[0]
            == "Running state must be specified with a `OWONSDS1104.RunningState` value."
        )


def test_arm_single_sequences():
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [":STOP", ":SINGle", ":SINGle", ":RUNning STOP", ":RUNning RUN", ":RUNning RUN"],
        [],
    ) as scope:
        scope.arm_single(stop_first=True, settle_time=0, arm_method="legacy_single")
        scope.arm_single(stop_first=False, settle_time=0, arm_method="legacy_single")
        scope.arm_single(stop_first=True, settle_time=0, arm_method="running_run")
        scope.arm_single(stop_first=False, settle_time=0, arm_method="running_run")


def test_single_wrapper_passes_arm_method():
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [":RUNning STOP", ":RUNning RUN"],
        [],
    ) as scope:
        scope.single(stop_first=True, settle_time=0, arm_method="running_run")


def test_arm_single_invalid_method():
    with expected_protocol(ik.owon.OWONSDS1104, [], []) as scope:
        with pytest.raises(ValueError) as err:
            scope.arm_single(arm_method="bad")
        assert err.value.args[0] == "arm_method must be one of {'legacy_single', 'running_run'}."


def test_freeze_acquisition_sequences():
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [":STOP", ":RUNning STOP"],
        [],
    ) as scope:
        scope.freeze_acquisition(method="legacy_stop", settle_time=0)
        scope.freeze_acquisition(method="running_stop", settle_time=0)


def test_freeze_acquisition_invalid_method():
    with expected_protocol(ik.owon.OWONSDS1104, [], []) as scope:
        with pytest.raises(ValueError) as err:
            scope.freeze_acquisition(method="bad")
        assert err.value.args[0] == "method must be one of {'legacy_stop', 'running_stop'}."


def test_trigger_status():
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [":TRIGger:STATUS?"],
        ["READy"],
    ) as scope:
        assert scope.trigger_status == scope.TriggerStatus.ready


@pytest.mark.parametrize(
    ("reply", "expected_name"),
    [
        ("SINGle", "single"),
        ("ALT", "alt"),
        ("LOGic", "logic"),
        ("BUS", "bus"),
    ],
)
def test_trigger_type_parsing(reply, expected_name):
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [":TRIGger:TYPE?"],
        [reply],
    ) as scope:
        assert scope.trigger_type == getattr(scope.TriggerType, expected_name)


@pytest.mark.parametrize(
    ("reply", "expected_name"),
    [
        ("EDGE", "edge"),
        ("VIDEO", "video"),
        ("PULSe", "pulse"),
        ("SLOPe", "slope"),
    ],
)
def test_single_trigger_mode_parsing(reply, expected_name):
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [":TRIGger:SINGle:MODE?"],
        [reply],
    ) as scope:
        assert scope.single_trigger_mode == getattr(scope.SingleTriggerMode, expected_name)


def test_single_trigger_mode_and_trigger_mode_alias_setters():
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [":TRIGger:SINGle:MODE VIDEO", ":TRIGger:SINGle:MODE EDGE"],
        [],
    ) as scope:
        scope.single_trigger_mode = scope.SingleTriggerMode.video
        scope.trigger_mode = scope.TriggerMode.edge


def test_single_trigger_mode_type_error():
    with expected_protocol(ik.owon.OWONSDS1104, [], []) as scope:
        with pytest.raises(TypeError) as err:
            scope.single_trigger_mode = "EDGE"
        assert (
            err.value.args[0]
            == "Trigger mode must be specified with a `OWONSDS1104.SingleTriggerMode` value."
        )


@pytest.mark.parametrize(
    ("reply", "expected_name"),
    [
        ("CH1", "ch1"),
        ("CH2", "ch2"),
        ("CH3", "ch3"),
        ("CH4", "ch4"),
        ("EXT", "ext"),
        ("EXT/5", "ext_div5"),
        ("ACLine", "ac_line"),
    ],
)
def test_trigger_source_parsing(reply, expected_name):
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [":TRIGger:SINGle:MODE?", ":TRIGger:SINGle:EDGE:SOURce?"],
        ["EDGE", reply],
    ) as scope:
        assert scope.trigger_source == getattr(scope.TriggerSource, expected_name)


@pytest.mark.parametrize(
    ("reply", "expected_name"),
    [("DC", "dc"), ("AC", "ac"), ("HF", "hf")],
)
def test_trigger_coupling_parsing(reply, expected_name):
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [":TRIGger:SINGle:MODE?", ":TRIGger:SINGle:EDGE:COUPling?"],
        ["EDGE", reply],
    ) as scope:
        assert scope.trigger_coupling == getattr(scope.TriggerCoupling, expected_name)


@pytest.mark.parametrize(
    ("reply", "expected"),
    [("25mv", 25e-3), ("0.025v", 25e-3)],
)
def test_trigger_level_parsing(reply, expected):
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [
            ":TRIGger:SINGle:MODE?",
            ":TRIGger:SINGle:EDGE:LEVel?",
        ],
        [
            "EDGE",
            reply,
        ],
    ) as scope:
        unit_eq(scope.trigger_level, expected * u.volt)


def test_edge_trigger_properties_require_edge_mode():
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [":TRIGger:SINGle:MODE?"],
        ["VIDEO"],
    ) as scope:
        with pytest.raises(NotImplementedError) as err:
            _ = scope.trigger_source
        assert (
            err.value.args[0]
            == "Edge trigger source, coupling, slope, and level are only exposed when single_trigger_mode is EDGE in this driver."
        )


def test_edge_trigger_type_errors():
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [
            ":TRIGger:SINGle:MODE?",
            ":TRIGger:SINGle:MODE?",
            ":TRIGger:SINGle:MODE?",
            ":TRIGger:SINGle:MODE?",
        ],
        ["EDGE", "EDGE", "EDGE", "EDGE"],
    ) as scope:
        with pytest.raises(TypeError) as err:
            scope.trigger_source = "CH1"
        assert (
            err.value.args[0]
            == "Trigger source must be specified with a `OWONSDS1104.TriggerSource` value."
        )

        with pytest.raises(TypeError) as err:
            scope.trigger_coupling = "DC"
        assert (
            err.value.args[0]
            == "Trigger coupling must be specified with a `OWONSDS1104.TriggerCoupling` value."
        )

        with pytest.raises(TypeError) as err:
            scope.trigger_slope = "RISE"
        assert (
            err.value.args[0]
            == "Trigger slope must be specified with a `OWONSDS1104.TriggerSlope` value."
        )

        with pytest.raises(ValueError) as err:
            scope.trigger_source = scope.TriggerSource.ext_div5
        assert (
            err.value.args[0]
            == "Edge trigger source write support is currently verified only for CH1-CH4 and ACLine."
        )


def test_edge_trigger_properties_and_aliases():
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [
            ":TRIGger:SINGle:MODE?",
            ":TRIGger:SINGle:EDGE:SOURce?",
            ":TRIGger:SINGle:MODE?",
            ":TRIGger:SINGle:EDGE:SOURce CH4",
            ":TRIGger:SINGle:MODE?",
            ":TRIGger:SINGle:EDGE:SOURce ACLine",
            ":TRIGger:SINGle:MODE?",
            ":TRIGger:SINGle:EDGE:COUPling?",
            ":TRIGger:SINGle:MODE?",
            ":TRIGger:SINGle:EDGE:COUPling HF",
            ":TRIGger:SINGle:MODE?",
            ":TRIGger:SINGle:EDGE:SLOPe?",
            ":TRIGger:SINGle:MODE?",
            ":TRIGger:SINGle:EDGE:SLOPe FALL",
            ":TRIGger:SINGle:MODE?",
            ":TRIGger:SINGle:EDGE:LEVel?",
            ":TRIGger:SINGle:MODE?",
            ":TRIGger:SINGle:EDGE:LEVel 25mv",
        ],
        [
            "EDGE",
            "ACLine",
            "EDGE",
            "EDGE",
            "EDGE",
            "HF",
            "EDGE",
            "EDGE",
            "RISE",
            "EDGE",
            "EDGE",
            "0.025v",
            "EDGE",
        ],
    ) as scope:
        assert scope.edge_trigger_source == scope.TriggerSource.ac_line
        scope.trigger_source = scope.TriggerSource.ch4
        scope.edge_trigger_source = scope.TriggerSource.ac_line
        assert scope.edge_trigger_coupling == scope.TriggerCoupling.hf
        scope.trigger_coupling = scope.TriggerCoupling.hf
        assert scope.edge_trigger_slope == scope.TriggerSlope.rise
        scope.edge_trigger_slope = scope.TriggerSlope.fall
        unit_eq(scope.edge_trigger_level, 25e-3 * u.volt)
        scope.edge_trigger_level = 25 * u.millivolt


@pytest.mark.parametrize(
    ("reply", "expected"),
    [("100ns", 100e-9), ("1ms", 1e-3), ("10s", 10.0)],
)
def test_trigger_holdoff_parsing(reply, expected):
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [":TRIGger:SINGle:HOLDoff?"],
        [reply],
    ) as scope:
        unit_eq(scope.trigger_holdoff, expected * u.second)


def test_trigger_holdoff_setter():
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [":TRIGger:SINGle:HOLDoff 1ms"],
        [],
    ) as scope:
        scope.trigger_holdoff = 1 * u.millisecond


@pytest.mark.parametrize("value", [99 * u.nanosecond, 11 * u.second])
def test_trigger_holdoff_value_error(value):
    with expected_protocol(ik.owon.OWONSDS1104, [], []) as scope:
        with pytest.raises(ValueError) as err:
            scope.trigger_holdoff = value
        assert err.value.args[0] == "Trigger holdoff must be between 100 ns and 10 s."


@pytest.mark.parametrize(
    ("reply", "expected_name"),
    [("PAL", "pal"), ("SECam", "secam"), ("NTSC", "ntsc")],
)
def test_video_trigger_standard_parsing(reply, expected_name):
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [":TRIGger:SINGle:MODE?", ":TRIGger:SINGle:VIDeo:MODU?"],
        ["VIDEO", reply],
    ) as scope:
        assert scope.video_trigger_standard == getattr(scope.VideoStandard, expected_name)


@pytest.mark.parametrize(
    ("reply", "expected_name"),
    [
        ("LINE", "line"),
        ("FIELd", "field"),
        ("ODD", "odd"),
        ("EVEN", "even"),
        ("LNUM", "lnum"),
    ],
)
def test_video_trigger_sync_parsing(reply, expected_name):
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [":TRIGger:SINGle:MODE?", ":TRIGger:SINGle:VIDeo:SYNC?"],
        ["VIDEO", reply],
    ) as scope:
        assert scope.video_trigger_sync == getattr(scope.VideoSync, expected_name)


def test_video_trigger_source_properties():
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [
            ":TRIGger:SINGle:MODE?",
            ":TRIGger:SINGle:VIDeo:SOURce?",
            ":TRIGger:SINGle:MODE?",
            ":TRIGger:SINGle:VIDeo:SOURce CH1",
        ],
        ["VIDEO", "CH2", "VIDEO"],
    ) as scope:
        assert scope.video_trigger_source == scope.TriggerSource.ch2
        scope.video_trigger_source = scope.TriggerSource.ch1


def test_video_trigger_source_type_and_value_errors():
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [":TRIGger:SINGle:MODE?", ":TRIGger:SINGle:MODE?"],
        ["VIDEO", "VIDEO"],
    ) as scope:
        with pytest.raises(TypeError) as err:
            scope.video_trigger_source = "CH1"
        assert (
            err.value.args[0]
            == "Video trigger source must be specified with a `OWONSDS1104.TriggerSource` value."
        )

        with pytest.raises(ValueError) as err:
            scope.video_trigger_source = scope.TriggerSource.ch3
        assert (
            err.value.args[0]
            == "Video trigger source write support is currently verified only for CH1 and CH2."
        )


def test_video_trigger_properties():
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [
            ":TRIGger:SINGle:MODE?",
            ":TRIGger:SINGle:VIDeo:MODU?",
            ":TRIGger:SINGle:MODE?",
            ":TRIGger:SINGle:System PAL",
            ":TRIGger:SINGle:MODE?",
            ":TRIGger:SINGle:VIDeo:SYNC?",
            ":TRIGger:SINGle:MODE?",
            ":TRIGger:SINGle:Sync FIELD",
            ":TRIGger:SINGle:MODE?",
            ":TRIGger:SINGle:VIDeo:SYNC?",
            ":TRIGger:SINGle:MODE?",
            ":TRIGger:SINGle:MODE?",
            ":TRIGger:SINGle:VIDeo:SYNC?",
            ":TRIGger:SINGle:LineNum 12",
            ":TRIGger:SINGle:MODE?",
            ":TRIGger:SINGle:VIDeo:LNUM?",
        ],
        [
            "VIDEO",
            "SECam",
            "VIDEO",
            "VIDEO",
            "FIELd",
            "VIDEO",
            "VIDEO",
            "LNUM",
            "VIDEO",
            "VIDEO",
            "LNUM",
            "VIDEO",
            "12",
        ],
    ) as scope:
        assert scope.video_trigger_standard == scope.VideoStandard.secam
        scope.video_trigger_standard = scope.VideoStandard.pal
        assert scope.video_trigger_sync == scope.VideoSync.field
        scope.video_trigger_sync = scope.VideoSync.field
        assert scope.video_trigger_sync == scope.VideoSync.lnum
        scope.video_trigger_line_number = 12
        assert scope.video_trigger_line_number == 12


def test_video_trigger_line_number_requires_lnum():
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [
            ":TRIGger:SINGle:MODE?",
            ":TRIGger:SINGle:MODE?",
            ":TRIGger:SINGle:VIDeo:SYNC?",
        ],
        ["VIDEO", "VIDEO", "LINE"],
    ) as scope:
        with pytest.raises(ValueError) as err:
            scope.video_trigger_line_number = 7
        assert (
            err.value.args[0]
            == "Video trigger line number can only be set when video_trigger_sync is LNUM."
        )


def test_video_trigger_properties_require_video_mode():
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [":TRIGger:SINGle:MODE?"],
        ["EDGE"],
    ) as scope:
        with pytest.raises(NotImplementedError) as err:
            _ = scope.video_trigger_standard
        assert (
            err.value.args[0]
            == "Video trigger source, standard, sync, and line number are only exposed when single_trigger_mode is VIDEO in this driver."
        )


def test_trigger_snapshot_edge():
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [
            ":TRIGger:STATUS?",
            ":TRIGger:TYPE?",
            ":TRIGger:SINGle:MODE?",
            ":TRIGger:SINGle:HOLDoff?",
            ":TRIGger:SINGle:SWEEp?",
            ":TRIGger:SINGle:MODE?",
            ":TRIGger:SINGle:EDGE:SOURce?",
            ":TRIGger:SINGle:MODE?",
            ":TRIGger:SINGle:EDGE:COUPling?",
            ":TRIGger:SINGle:MODE?",
            ":TRIGger:SINGle:EDGE:SLOPe?",
            ":TRIGger:SINGle:MODE?",
            ":TRIGger:SINGle:EDGE:LEVel?",
        ],
        [
            "TRIG",
            "SINGle",
            "EDGE",
            "100ns",
            "AUTO",
            "EDGE",
            "CH4",
            "EDGE",
            "HF",
            "EDGE",
            "FALL",
            "EDGE",
            "25mv",
        ],
    ) as scope:
        config = scope.read_trigger_configuration()

    assert config.status == ik.owon.OWONSDS1104.TriggerStatus.trig
    assert config.trigger_type == ik.owon.OWONSDS1104.TriggerType.single
    assert config.single_trigger_mode == ik.owon.OWONSDS1104.SingleTriggerMode.edge
    unit_eq(config.holdoff, 100e-9 * u.second)
    assert config.trigger_sweep == ik.owon.OWONSDS1104.TriggerSweep.auto
    assert config.edge_source == ik.owon.OWONSDS1104.TriggerSource.ch4
    assert config.edge_coupling == ik.owon.OWONSDS1104.TriggerCoupling.hf
    assert config.edge_slope == ik.owon.OWONSDS1104.TriggerSlope.fall
    unit_eq(config.edge_level, 25e-3 * u.volt)
    assert config.video_source is None


def test_trigger_snapshot_video():
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [
            ":TRIGger:STATUS?",
            ":TRIGger:TYPE?",
            ":TRIGger:SINGle:MODE?",
            ":TRIGger:SINGle:HOLDoff?",
            ":TRIGger:SINGle:SWEEp?",
            ":TRIGger:SINGle:MODE?",
            ":TRIGger:SINGle:VIDeo:SOURce?",
            ":TRIGger:SINGle:MODE?",
            ":TRIGger:SINGle:VIDeo:MODU?",
            ":TRIGger:SINGle:MODE?",
            ":TRIGger:SINGle:VIDeo:SYNC?",
            ":TRIGger:SINGle:MODE?",
            ":TRIGger:SINGle:VIDeo:LNUM?",
        ],
        [
            "READY",
            "SINGle",
            "VIDEO",
            "1ms",
            "NORMal",
            "VIDEO",
            "CH2",
            "VIDEO",
            "NTSC",
            "VIDEO",
            "LNUM",
            "VIDEO",
            "525",
        ],
    ) as scope:
        config = scope.read_trigger_configuration()

    assert config.single_trigger_mode == ik.owon.OWONSDS1104.SingleTriggerMode.video
    assert config.trigger_sweep == ik.owon.OWONSDS1104.TriggerSweep.normal
    assert config.video_source == ik.owon.OWONSDS1104.TriggerSource.ch2
    assert config.video_standard == ik.owon.OWONSDS1104.VideoStandard.ntsc
    assert config.video_sync == ik.owon.OWONSDS1104.VideoSync.lnum
    assert config.video_line_number == 525
    assert config.edge_source is None


def test_trigger_snapshot_pulse_only_includes_general_fields():
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [
            ":TRIGger:STATUS?",
            ":TRIGger:TYPE?",
            ":TRIGger:SINGle:MODE?",
            ":TRIGger:SINGle:HOLDoff?",
            ":TRIGger:SINGle:SWEEp?",
        ],
        ["AUTO", "SINGle", "PULSe", "100ns", "SINGle"],
    ) as scope:
        config = scope.read_trigger_configuration()

    assert config.single_trigger_mode == ik.owon.OWONSDS1104.SingleTriggerMode.pulse
    assert config.trigger_sweep == ik.owon.OWONSDS1104.TriggerSweep.single
    assert config.edge_source is None
    assert config.video_source is None


def test_wait_for_trigger_status_success():
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [":TRIGger:STATUS?", ":TRIGger:STATUS?", ":TRIGger:STATUS?"],
        ["AUTO", "READy", "TRIG"],
    ) as scope:
        assert (
            scope.wait_for_trigger_status("trig", timeout=0.1 * u.second, poll_interval=0 * u.second)
            == scope.TriggerStatus.trig
        )


def test_wait_for_trigger_status_timeout(monkeypatch):
    monotonic_values = iter([0.0, 0.0, 0.0, 0.0])
    monkeypatch.setattr(owon_sds1104.time, "monotonic", lambda: next(monotonic_values))
    monkeypatch.setattr(owon_sds1104.time, "sleep", lambda _: None)

    with expected_protocol(
        ik.owon.OWONSDS1104,
        [":TRIGger:STATUS?"],
        ["AUTO"],
    ) as scope:
        with pytest.raises(TimeoutError) as err:
            scope.wait_for_trigger_status(
                scope.TriggerStatus.trig,
                timeout=0 * u.second,
                poll_interval=0 * u.second,
            )
        assert "TRIG" in err.value.args[0]


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (25 * u.millivolt, "25mv"),
        (1 * u.volt, "1v"),
        (100 * u.nanosecond, "100ns"),
        (1 * u.millisecond, "1ms"),
    ],
)
def test_trigger_token_formatters(value, expected):
    if value.check("[time]"):
        token = owon_sds1104._format_time_token(value)
    else:
        token = owon_sds1104._format_quantity_token(value)
    assert token == expected
    assert "e" not in token.lower()


def test_autoscale():
    with expected_protocol(ik.owon.OWONSDS1104, [":AUTOscale ON"], []) as scope:
        scope.autoscale()


def test_measure_frequency():
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [":MEASUrement:CH1:FREQuency?"],
        ["12.5kHz"],
    ) as scope:
        unit_eq(scope.measure_frequency(1), 12_500 * u.hertz)


def test_measure_period():
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [":MEASUrement:CH2:PERiod?"],
        ["5ms"],
    ) as scope:
        unit_eq(scope.measure_period(2), 5e-3 * u.second)


def test_measure_peak_to_peak():
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [":MEASUrement:CH3:PKPK?"],
        ["2.5V"],
    ) as scope:
        unit_eq(scope.measure_peak_to_peak(3), 2.5 * u.volt)


def test_measure_rms():
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [":MEASUrement:CH4:CYCRms?"],
        ["125mV"],
    ) as scope:
        unit_eq(scope.measure_rms(4), 0.125 * u.volt)


def test_extended_long_form_measurements():
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [
            ":MEASUrement:CH1:AVERage?",
            ":MEASUrement:CH1:MAX?",
            ":MEASUrement:CH1:MIN?",
            ":MEASUrement:CH1:VTOP?",
            ":MEASUrement:CH1:VBASe?",
            ":MEASUrement:CH1:VAMP?",
            ":MEASUrement:CH1:RTime?",
            ":MEASUrement:CH1:FTime?",
            ":MEASUrement:CH1:PWIDth?",
            ":MEASUrement:CH1:NWIDth?",
            ":MEASUrement:CH1:PDUTy?",
            ":MEASUrement:CH1:NDUTy?",
            ":MEASUrement:CH1:OVERshoot?",
            ":MEASUrement:CH1:PREShoot?",
        ],
        [
            "V : 10.00mV",
            "Vmax : 80.00mV",
            "Vmin : -10.00mV",
            "Vtop : 70.00mV",
            "Vbase : 5.00mV",
            "Vamp : 65.00mV",
            "Rt : 400us",
            "Ft : 500us",
            "PW : 2.00ms",
            "NW : 3.00ms",
            "PD : 60.0%",
            "ND : 40.0%",
            "OS : 5.0%",
            "PS : 2.5%",
        ],
    ) as scope:
        unit_eq(scope.measure_average(1), 10e-3 * u.volt)
        unit_eq(scope.measure_maximum(1), 80e-3 * u.volt)
        unit_eq(scope.measure_minimum(1), -10e-3 * u.volt)
        unit_eq(scope.measure_top(1), 70e-3 * u.volt)
        unit_eq(scope.measure_base(1), 5e-3 * u.volt)
        unit_eq(scope.measure_amplitude(1), 65e-3 * u.volt)
        unit_eq(scope.measure_rise_time(1), 400e-6 * u.second)
        unit_eq(scope.measure_fall_time(1), 500e-6 * u.second)
        unit_eq(scope.measure_positive_width(1), 2e-3 * u.second)
        unit_eq(scope.measure_negative_width(1), 3e-3 * u.second)
        unit_eq(scope.measure_positive_duty(1), 60 * u.percent)
        unit_eq(scope.measure_negative_duty(1), 40 * u.percent)
        unit_eq(scope.measure_overshoot(1), 5 * u.percent)
        unit_eq(scope.measure_preshoot(1), 2.5 * u.percent)


def test_extended_short_form_measurements():
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [
            ":MEAS:CH1:SQUARESUM?",
            ":MEAS:CH1:CURSorrms?",
            ":MEAS:CH1:SCREenduty?",
            ":MEAS:CH1:PPULSENUM?",
            ":MEAS:CH1:NPULSENUM?",
            ":MEAS:CH1:AREA?",
            ":MEAS:CH1:CYCLEAREA?",
        ],
        [
            "Vr : 20.00mV",
            "CR : 5.000mV",
            "WP : 40.0%",
            "+PC : 4",
            "-PC : 3",
            "AR : 1.5mV*s",
            "CA : 500uV*s",
        ],
    ) as scope:
        unit_eq(scope.measure_square_sum(1), 20e-3 * u.volt)
        unit_eq(scope.measure_cursor_rms(1), 5e-3 * u.volt)
        unit_eq(scope.measure_screen_duty(1), 40 * u.percent)
        assert scope.measure_positive_pulse_count(1) == 4
        assert scope.measure_negative_pulse_count(1) == 3
        unit_eq(scope.measure_area(1), 1.5e-3 * u.volt * u.second)
        unit_eq(scope.measure_cycle_area(1), 500e-6 * u.volt * u.second)


def test_edge_count_and_hard_frequency_measurements():
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [
            ":MEASUrement:CH1:RISEedgenum?",
            ":MEASUrement:CH1:FALLedgenum?",
            ":MEASUrement:CH1:HARDfrequency?",
        ],
        [
            "+E : 4",
            "-E : 3",
            "<2Hz",
        ],
    ) as scope:
        assert scope.measure_rise_edge_count(1) == 4
        assert scope.measure_fall_edge_count(1) == 3
        unit_eq(scope.measure_hard_frequency(1), 2 * u.hertz)


def test_channel_measurement_helpers():
    with expected_protocol(
        ik.owon.OWONSDS1104,
        [
            ":MEASUrement:CH1:FREQuency?",
            ":MEASUrement:CH1:PERiod?",
            ":MEASUrement:CH1:PKPK?",
            ":MEASUrement:CH1:CYCRms?",
            ":MEASUrement:CH1:AVERage?",
            ":MEASUrement:CH1:MAX?",
            ":MEASUrement:CH1:MIN?",
        ],
        ["100Hz", "10ms", "800mV", "200mV", "100mV", "900mV", "-50mV"],
    ) as scope:
        unit_eq(scope.channel[0].measure_frequency(), 100 * u.hertz)
        unit_eq(scope.channel[0].measure_period(), 10e-3 * u.second)
        unit_eq(scope.channel[0].measure_peak_to_peak(), 0.8 * u.volt)
        unit_eq(scope.channel[0].measure_rms(), 0.2 * u.volt)
        unit_eq(scope.channel[0].measure_average(), 0.1 * u.volt)
        unit_eq(scope.channel[0].measure_maximum(), 0.9 * u.volt)
        unit_eq(scope.channel[0].measure_minimum(), -0.05 * u.volt)


def test_measurement_channel_validation():
    with expected_protocol(ik.owon.OWONSDS1104, [], []) as scope:
        with pytest.raises(ValueError) as err:
            scope.measure_frequency(0)
        assert err.value.args[0] == "Channel index must be between 1 and 4."


def test_force_trigger_not_implemented():
    with expected_protocol(ik.owon.OWONSDS1104, [], []) as scope:
        with pytest.raises(NotImplementedError):
            scope.force_trigger()


def test_channel_read_waveform_binary():
    metadata = {
        "CHANNEL": [
            {"SCALE": "100mV", "PROBE": "10X", "OFFSET": "0"},
            {"SCALE": "100mV", "PROBE": "10X", "OFFSET": "0"},
            {"SCALE": "100mV", "PROBE": "10X", "OFFSET": "0"},
            {"SCALE": "100mV", "PROBE": "10X", "OFFSET": "0"},
        ],
        "SAMPLE": {"SAMPLERATE": "1MS/s", "DATALEN": "4"},
        "TIMEBASE": {"HOFFSET": "0"},
    }
    metadata_payload = b"\x00\x00\x00\x00" + json.dumps(metadata).encode("ascii")
    waveform_payload = b"\x00\x00\x00\x00" + struct.pack("<4h", 0, 82, -82, 410)

    scope, stdout = _make_binary_scope(
        binary_replies=[metadata_payload],
        exact_replies=[waveform_payload],
    )

    x, y = scope.channel[0].read_waveform()

    assert stdout.getvalue() == (b":DATA:WAVE:SCREen:HEAD?" b":DATA:WAVE:SCREEN:CH1?")
    assert tuple(float(value) for value in x) == pytest.approx(
        (-10e-6, -5e-6, 0.0, 5e-6)
    )
    assert tuple(float(value) for value in y) == pytest.approx((0.0, 0.2, -0.2, 1.0))


def test_channel_read_waveform_binary_parenthesized_sample_rate():
    metadata = {
        "CHANNEL": [
            {"SCALE": "100mV", "PROBE": "10X", "OFFSET": "0"},
            {"SCALE": "100mV", "PROBE": "10X", "OFFSET": "0"},
            {"SCALE": "100mV", "PROBE": "10X", "OFFSET": "0"},
            {"SCALE": "100mV", "PROBE": "10X", "OFFSET": "0"},
        ],
        "SAMPLE": {"SAMPLERATE": "(1MS/s)", "DATALEN": "4"},
        "TIMEBASE": {"HOFFSET": "0"},
    }
    metadata_payload = b"\x00\x00\x00\x00" + json.dumps(metadata).encode("ascii")
    waveform_payload = b"\x00\x00\x00\x00" + struct.pack("<4h", 0, 82, -82, 410)

    scope, stdout = _make_binary_scope(
        binary_replies=[metadata_payload],
        exact_replies=[waveform_payload],
    )

    x, y = scope.channel[0].read_waveform()

    assert stdout.getvalue() == (b":DATA:WAVE:SCREen:HEAD?" b":DATA:WAVE:SCREEN:CH1?")
    assert tuple(float(value) for value in x) == pytest.approx(
        (-10e-6, -5e-6, 0.0, 5e-6)
    )
    assert tuple(float(value) for value in y) == pytest.approx((0.0, 0.2, -0.2, 1.0))


def test_channel_read_waveform_binary_current_rate_ratio_scaling():
    metadata = {
        "CHANNEL": [
            {
                "SCALE": "1.00V",
                "PROBE": "1X",
                "OFFSET": "50",
                "Current_Rate": 10000.0,
                "Current_Ratio": 1.5625,
            },
            {"SCALE": "1.00V", "PROBE": "1X", "OFFSET": "0"},
            {"SCALE": "1.00V", "PROBE": "1X", "OFFSET": "0"},
            {"SCALE": "1.00V", "PROBE": "1X", "OFFSET": "0"},
        ],
        "SAMPLE": {"SAMPLERATE": "(1MS/s)", "DATALEN": "2"},
        "TIMEBASE": {"HOFFSET": "0"},
    }
    metadata_payload = b"\x00\x00\x00\x00" + json.dumps(metadata).encode("ascii")
    waveform_payload = b"\x00\x00\x00\x00" + struct.pack("<2h", 6144, 27648)

    scope, stdout = _make_binary_scope(
        binary_replies=[metadata_payload],
        exact_replies=[waveform_payload],
    )

    x, y = scope.channel[0].read_waveform()

    assert stdout.getvalue() == (b":DATA:WAVE:SCREen:HEAD?" b":DATA:WAVE:SCREEN:CH1?")
    assert tuple(float(value) for value in x) == pytest.approx((-5e-6, 0.0))
    assert tuple(float(value) for value in y) == pytest.approx((0.0, 3.36))


def test_read_waveform_metadata():
    metadata = {
        "CHANNEL": [
            {"SCALE": "100mV", "PROBE": "10X", "OFFSET": "0"},
            {"SCALE": "100mV", "PROBE": "10X", "OFFSET": "0"},
            {"SCALE": "100mV", "PROBE": "10X", "OFFSET": "0"},
            {"SCALE": "100mV", "PROBE": "10X", "OFFSET": "0"},
        ],
        "SAMPLE": {"SAMPLERATE": "1MS/s", "DATALEN": "4"},
        "TIMEBASE": {"HOFFSET": "0"},
    }
    metadata_payload = b"\x00\x00\x00\x00" + json.dumps(metadata).encode("ascii")

    scope, stdout = _make_binary_scope(binary_replies=[metadata_payload])

    result = scope.read_waveform_metadata()

    assert result["SAMPLE"]["DATALEN"] == "4"
    assert stdout.getvalue() == b":DATA:WAVE:SCREen:HEAD?"


def test_channel_read_waveform_ascii_not_implemented():
    with expected_protocol(ik.owon.OWONSDS1104, [], []) as scope:
        with pytest.raises(NotImplementedError):
            scope.channel[0].read_waveform(bin_format=False)


def test_math_read_waveform_not_implemented():
    with expected_protocol(ik.owon.OWONSDS1104, [], []) as scope:
        with pytest.raises(NotImplementedError):
            scope.math.read_waveform()


def test_read_measurement_data_short_and_long():
    short_payload = (
        b"\x00\x00\x00\x00" + b'{"CH1":{"FREQuency":"1.00kHz","PKPK":"2.00V"}}'
    )
    long_payload = (
        b"\x00\x00\x00\x00" + b'{"CH1":{"FREQuency":"1.00kHz","PKPK":"2.00V"}}'
    )
    scope, stdout = _make_binary_scope(
        binary_replies=[short_payload, long_payload],
    )

    assert scope.read_measurement_data(1) == {"FREQuency": "1.00kHz", "PKPK": "2.00V"}
    assert scope.channel[0].read_measurement_data(long_form=True) == {
        "FREQuency": "1.00kHz",
        "PKPK": "2.00V",
    }
    assert stdout.getvalue() == (b":MEAS:CH1?" b":MEASUrement:CH1?")


def test_read_all_measurement_data_short_and_long():
    short_payload = (
        b"\x00\x00\x00\x00" + b'{"CH1":{"FREQuency":"1.00kHz"},"CH2":{"PKPK":"2.00V"}}'
    )
    long_payload = (
        b"\x00\x00\x00\x00" + b'{"CH1":{"FREQuency":"1.00kHz"},"CH2":{"PKPK":"2.00V"}}'
    )
    scope, stdout = _make_binary_scope(
        binary_replies=[short_payload, long_payload],
    )

    assert scope.read_all_measurement_data() == {
        1: {"FREQuency": "1.00kHz"},
        2: {"PKPK": "2.00V"},
    }
    assert scope.read_all_measurement_data(long_form=True) == {
        1: {"FREQuency": "1.00kHz"},
        2: {"PKPK": "2.00V"},
    }
    assert stdout.getvalue() == (b":MEAS?" b":MEASUrement:ALL?")


def test_read_screen_bmp():
    bmp_body = b"BM" + struct.pack("<I", 14) + b"\x00\x00\x00\x00" + b"\x36\x00\x00\x00"
    scope, stdout = _make_binary_scope(
        exact_replies=[
            struct.pack("<I", len(bmp_body)),
            bmp_body,
        ]
    )

    assert scope.read_screen_bmp() == bmp_body
    assert stdout.getvalue() == b":DATA:WAVE:SCREen:BMP?"


def test_read_deep_memory_metadata():
    metadata_body = json.dumps(
        {
            "CHANNEL": [{"SCALE": "100mV", "PROBE": "10X", "OFFSET": "0"}] * 4,
            "SAMPLE": {"SAMPLERATE": "1MS/s", "DATALEN": "4"},
            "TIMEBASE": {"HOFFSET": "0"},
        }
    ).encode("ascii")
    scope, stdout = _make_binary_scope(
        exact_replies=[
            struct.pack("<I", len(metadata_body)),
            metadata_body,
        ]
    )

    assert scope.read_deep_memory_metadata()["SAMPLE"]["DATALEN"] == "4"
    assert stdout.getvalue() == b":DATA:WAVE:DEPMEM:HEAD?"


def test_read_deep_memory_channel():
    metadata_body = json.dumps(
        {
            "CHANNEL": [{"SCALE": "100mV", "PROBE": "10X", "OFFSET": "0"}] * 4,
            "SAMPLE": {"SAMPLERATE": "1MS/s", "DATALEN": "4"},
            "TIMEBASE": {"HOFFSET": "0"},
        }
    ).encode("ascii")
    waveform_body = struct.pack("<4h", 0, 82, -82, 410)
    scope, stdout = _make_binary_scope(
        exact_replies=[
            struct.pack("<I", len(metadata_body)),
            metadata_body,
            struct.pack("<I", len(waveform_body)),
            waveform_body,
        ]
    )

    x, y = scope.channel[0].read_deep_memory()

    assert tuple(float(value) for value in x) == pytest.approx(
        (-10e-6, -5e-6, 0.0, 5e-6)
    )
    assert tuple(float(value) for value in y) == pytest.approx((0.0, 0.2, -0.2, 1.0))
    assert stdout.getvalue() == (b":DATA:WAVE:DEPMEM:HEAD?" b":DATA:WAVE:DEPMEM:CH1?")


def test_read_deep_memory_channel_current_rate_ratio_scaling():
    metadata = {
        "CHANNEL": [
            {
                "SCALE": "1.00V",
                "PROBE": "1X",
                "OFFSET": "50",
                "Current_Rate": 10000.0,
                "Current_Ratio": 1.5625,
            },
            {
                "SCALE": "1.00V",
                "PROBE": "1X",
                "OFFSET": "-100",
                "Current_Rate": 10000.0,
                "Current_Ratio": 1.5625,
            },
            {"SCALE": "1.00V", "PROBE": "1X", "OFFSET": "0"},
            {"SCALE": "1.00V", "PROBE": "1X", "OFFSET": "0"},
        ],
        "SAMPLE": {"SAMPLERATE": "(1MS/s)", "DATALEN": "2"},
        "TIMEBASE": {"HOFFSET": "0"},
    }
    metadata_body = json.dumps(metadata).encode("ascii")
    waveform_body = struct.pack("<2h", -12800, 8448)
    scope, stdout = _make_binary_scope(
        exact_replies=[
            struct.pack("<I", len(metadata_body)),
            metadata_body,
            struct.pack("<I", len(waveform_body)),
            waveform_body,
        ]
    )

    x, y = scope.read_deep_memory_channel(2)

    assert tuple(float(value) for value in x) == pytest.approx((-5e-6, 0.0))
    assert tuple(float(value) for value in y) == pytest.approx((0.04, 3.36))
    assert stdout.getvalue() == (b":DATA:WAVE:DEPMEM:HEAD?" b":DATA:WAVE:DEPMEM:CH2?")


def test_read_deep_memory_all():
    metadata = {
        "CHANNEL": [
            {"DISPLAY": "ON"},
            {"DISPLAY": "OFF"},
            {"DISPLAY": "ON"},
            {"DISPLAY": "OFF"},
        ],
        "SAMPLE": {"SAMPLERATE": "1MS/s", "DATALEN": "4"},
    }
    metadata_body = json.dumps(metadata).encode("ascii")
    block1 = struct.pack("<4h", 1, 2, 3, 4)
    block2 = struct.pack("<4h", 5, 6, 7, 8)
    bundle_body = (
        struct.pack("<I", len(metadata_body))
        + metadata_body
        + struct.pack("<I", len(block1))
        + block1
        + struct.pack("<I", len(block2))
        + block2
    )
    scope, stdout = _make_binary_scope(
        exact_replies=[
            struct.pack("<I", len(bundle_body)),
            bundle_body,
        ]
    )

    capture = scope.read_deep_memory_all()

    assert capture.metadata["SAMPLE"]["DATALEN"] == "4"
    assert tuple(int(value) for value in capture.raw_channels[1]) == (1, 2, 3, 4)
    assert tuple(int(value) for value in capture.raw_channels[3]) == (5, 6, 7, 8)
    assert stdout.getvalue() == b":DATA:WAVE:DEPMem:All?"


def test_list_saved_waveforms_and_read_data():
    head_body = b'[{"Index":"0-0","Wave_Character":"CH1"},{"Index":"1-0","Wave_Character":"CH2"}]'
    data_body = struct.pack("<4h", 9, 10, 11, 12)
    scope, stdout = _make_binary_scope(
        exact_replies=[
            struct.pack("<I", len(head_body)),
            head_body,
            struct.pack("<I", len(data_body)),
            data_body,
        ]
    )

    entries = scope.list_saved_waveforms()
    samples = scope.read_saved_waveform_data("0-0")

    assert [entry.index for entry in entries] == ["0-0", "1-0"]
    assert tuple(int(value) for value in samples) == (9, 10, 11, 12)
    assert stdout.getvalue() == (b":SAVE:READ:HEAD?" b":SAVE:READ:DATA 0-0")
