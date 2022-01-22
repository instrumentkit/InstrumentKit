#!/usr/bin/env python
"""
Module containing tests for the Fluke 3000 FC multimeter
"""

# IMPORTS ####################################################################

import pytest

from instruments.units import ureg as u

import instruments as ik
from instruments.tests import expected_protocol

# TESTS ######################################################################


# pylint: disable=protected-access


# Empty initialization sequence (scan function) that does not uncover
# any available Fluke 3000 FC device.
none_sequence = [
    "rfebd 01 0",
    "rfebd 02 0",
    "rfebd 03 0",
    "rfebd 04 0",
    "rfebd 05 0",
    "rfebd 06 0",
]
none_response = ["CR:Ack=2", "CR:Ack=2", "CR:Ack=2", "CR:Ack=2", "CR:Ack=2", "CR:Ack=2"]

# Default initialization sequence (scan function) that binds a multimeter
# to port 1 and a temperature module to port 2.
init_sequence = [
    "rfebd 01 0",  # 1
    "rfgus 01",  # 2
    "rfebd 02 0",  # 3
    "rfgus 02",  # 4
    "rfebd 03 0",  # 5
    "rfebd 04 0",  # 6
    "rfebd 05 0",  # 7
    "rfebd 06 0",  # 8
]
init_response = [
    "CR:Ack=0:RFEBD",  # 1.1
    "ME:R:S#=01:DCC=012:PH=64",  # 1.2
    "CR:Ack=0:RFGUS",  # 2.1
    "ME:R:S#=01:DCC=004:PH=46333030304643",  # 2.2
    "CR:Ack=0:RFEBD",  # 3.1
    "ME:R:S#=01:DCC=012:PH=64",  # 3.2
    "CR:Ack=0:RFGUS",  # 4.1
    "ME:R:S#=02:DCC=004:PH=54333030304643",  # 4.2
    "CR:Ack=2",  # 5
    "CR:Ack=2",  # 6
    "CR:Ack=2",  # 7
    "CR:Ack=2",  # 8
]


# Default initialization sequence (scan function) that binds a multimeter
# to port 1. Adopted from `init_sequence` and `init_response`, thus
# counting does not contain 4.
init_sequence_mm_only = [
    "rfebd 01 0",  # 1
    "rfgus 01",  # 2
    "rfebd 02 0",  # 3
    "rfebd 03 0",  # 5
    "rfebd 04 0",  # 6
    "rfebd 05 0",  # 7
    "rfebd 06 0",  # 8
]
init_response_mm_only = [
    "CR:Ack=0:RFEBD",  # 1.1
    "ME:R:S#=01:DCC=012:PH=64",  # 1.2
    "CR:Ack=0:RFGUS",  # 2.1
    "ME:R:S#=01:DCC=004:PH=46333030304643",  # 2.2
    "CR:Ack=2",  # 3
    "CR:Ack=2",  # 5
    "CR:Ack=2",  # 6
    "CR:Ack=2",  # 7
    "CR:Ack=2",  # 8
]


def test_mode():
    with expected_protocol(
        ik.fluke.Fluke3000,
        init_sequence + ["rfemd 01 1", "rfemd 01 2"],  # 1  # 2
        init_response
        + [
            "CR:Ack=0:RFEMD",  # 1.1
            "ME:R:S#=01:DCC=010:PH=00000006020C0600",  # 1.2
            "CR:Ack=0:RFEMD",  # 2
        ],
        "\r",
    ) as inst:
        assert inst.mode == inst.Mode.voltage_dc


def test_mode_key_error():
    """Raise KeyError if the Module is not available."""
    with expected_protocol(
        ik.fluke.Fluke3000, init_sequence, init_response, "\r"
    ) as inst:
        # kill positions to trigger error
        inst.positions = {}
        with pytest.raises(KeyError) as err_info:
            _ = inst.mode
        err_msg = err_info.value.args[0]
        assert err_msg == "No `Fluke3000` FC multimeter is bound"


def test_trigger_mode_attribute_error():
    """Raise AttributeError since trigger mode not supported."""
    with expected_protocol(
        ik.fluke.Fluke3000, init_sequence, init_response, "\r"
    ) as inst:
        with pytest.raises(AttributeError) as err_info:
            _ = inst.trigger_mode
        err_msg = err_info.value.args[0]
        assert err_msg == "The `Fluke3000` only supports single trigger when " "queried"


def test_relative_attribute_error():
    """Raise AttributeError since relative measurement mode not supported."""
    with expected_protocol(
        ik.fluke.Fluke3000, init_sequence, init_response, "\r"
    ) as inst:
        with pytest.raises(AttributeError) as err_info:
            _ = inst.relative
        err_msg = err_info.value.args[0]
        assert err_msg == "The `Fluke3000` FC does not support relative " "measurements"


def test_input_range_attribute_error():
    """
    Raise AttributeError since instrument is an auto ranging only
    multimeter.
    """
    with expected_protocol(
        ik.fluke.Fluke3000, init_sequence, init_response, "\r"
    ) as inst:
        with pytest.raises(AttributeError) as err_info:
            _ = inst.input_range
        err_msg = err_info.value.args[0]
        assert err_msg == "The `Fluke3000` FC is an autoranging only " "multimeter"


def test_connect():
    with expected_protocol(
        ik.fluke.Fluke3000,
        none_sequence
        + [
            "ri",  # 1
            "rfsm 1",  # 2
            "rfdis",  # 3
        ]
        + init_sequence,
        none_response
        + [
            "CR:Ack=0:RI",  # 1.1
            "SI:PON=Power On",  # 1.2
            "RE:O",  # 1.3
            "CR:Ack=0:RFSM:Radio On Master",  # 2.1
            "RE:M",  # 2.2
            "CR:Ack=0:RFDIS",  # 3.1
            "ME:S",  # 3.2
            "ME:D:010200000000",  # 3.3
        ]
        + init_response,
        "\r",
    ) as inst:
        assert inst.positions[ik.fluke.Fluke3000.Module.m3000] == 1
        assert inst.positions[ik.fluke.Fluke3000.Module.t3000] == 2


def test_connect_no_modules_available():
    """Raise ValueError if no modules are avilable."""
    with pytest.raises(ValueError) as err_info:
        with expected_protocol(
            ik.fluke.Fluke3000, none_sequence, none_response, "\r"
        ) as inst:
            _ = inst
    err_msg = err_info.value.args[0]
    assert err_msg == "No `Fluke3000` modules available"


def test_scan():
    with expected_protocol(
        ik.fluke.Fluke3000, init_sequence, init_response, "\r"
    ) as inst:
        assert inst.positions[ik.fluke.Fluke3000.Module.m3000] == 1
        assert inst.positions[ik.fluke.Fluke3000.Module.t3000] == 2


def test_scan_module_not_implemented():
    """Raise NotImplementedError if a module with wrong ID is found."""
    # modify response to contain unknown module
    module_id = 42
    mod_response = list(init_response)
    mod_response[3] = f"ME:R:S#=01:DCC=004:PH={module_id}"  # new module id
    with pytest.raises(NotImplementedError) as err_info:
        with expected_protocol(
            ik.fluke.Fluke3000, init_sequence, mod_response, "\r"
        ) as inst:
            _ = inst
    err_msg = err_info.value.args[0]
    assert err_msg == f"Module ID {module_id} not implemented"


def test_reset():
    with expected_protocol(
        ik.fluke.Fluke3000,
        init_sequence + ["ri", "rfsm 1"],  # 1  # 2
        init_response
        + [
            "CR:Ack=0:RI",  # 1.1
            "SI:PON=Power On",  # 1.2
            "RE:O",  # 1.3
            "CR:Ack=0:RFSM:Radio On Master",  # 2.1
            "RE:M",  # 2.2
        ],
        "\r",
    ) as inst:
        inst.reset()


def test_flush(mocker):
    """Test flushing the reads, which raises an OSError here.

    Mocking `read()` to generate the error.
    """
    with expected_protocol(
        ik.fluke.Fluke3000, init_sequence, init_response, "\r"
    ) as inst:
        # mock read to raise OSError
        os_error_mock = mocker.Mock()
        os_error_mock.side_effect = OSError
        read_mock = mocker.patch.object(inst, "read", os_error_mock)
        # now flush
        inst.flush()
        read_mock.assert_called()


def test_measure():
    with expected_protocol(
        ik.fluke.Fluke3000,
        init_sequence + ["rfemd 01 1", "rfemd 01 2", "rfemd 02 0"],  # 1  # 2  # 3
        init_response
        + [
            "CR:Ack=0:RFEMD",  # 1.1
            "ME:R:S#=01:DCC=010:PH=FD010006020C0600",  # 1.2
            "CR:Ack=0:RFEMD",  # 2
            "CR:Ack=0:RFEMD",  # 3.1
            "ME:R:S#=02:DCC=010:PH=FD00C08207220000",  # 3.2
        ],
        "\r",
    ) as inst:
        assert inst.measure(inst.Mode.voltage_dc) == 0.509 * u.volt
        assert inst.measure(inst.Mode.temperature) == u.Quantity(-25.3, u.degC)


def test_measure_invalid_mode():
    """Raise ValueError if measurement mode is not supported."""
    with expected_protocol(
        ik.fluke.Fluke3000, init_sequence, init_response, "\r"
    ) as inst:
        wrong_mode = 42
        with pytest.raises(ValueError) as err_info:
            inst.measure(wrong_mode)
        err_msg = err_info.value.args[0]
        assert err_msg == f"Mode {wrong_mode} is not supported"


def test_measure_no_module_with_mode():
    """
    Raise ValueError if not sensor that supports the requested mode is
    connected.
    """
    mode_not_available = ik.fluke.Fluke3000.Mode.temperature
    with expected_protocol(
        ik.fluke.Fluke3000, init_sequence_mm_only, init_response_mm_only, "\r"
    ) as inst:
        with pytest.raises(ValueError) as err_info:
            inst.measure(mode=mode_not_available)
        err_msg = err_info.value.args[0]
        assert (
            err_msg == f"Device necessary to measure {mode_not_available} "
            f"is not available"
        )


def test_measure_inconsistent_answer(mocker):
    """Measurement test with inconsistent answer.

    The first time around in this measurement an inconsistent answer is
    returend. This would usually call a `flush` routine, which reads
    until no more terminators are found. Here, `flush` is mocked out
    such that the `expected_protocol` can actually be used.
    """
    mode_issue = 42  # expect 02, answer something different - unexpected
    with expected_protocol(
        ik.fluke.Fluke3000,
        init_sequence
        + [
            # bad query
            "rfemd 01 1",  # 1
            "rfemd 01 2",  # 2
            "rfemd 01 2",  # 2
            # try again
            "rfemd 01 1",  # 1
            "rfemd 01 2",  # 2
        ],
        init_response
        + [
            # bad response
            "CR:Ack=0:RFEMD",  # 1.1
            f"ME:R:S#=01:DCC=010:PH=FD010006{mode_issue}0C0600",  # 1.2
            "CR:Ack=0:RFEMD",  # 2
            "CR:Ack=0:RFEMD",  # 2
            # "",  # something to flush
            # try again
            "CR:Ack=0:RFEMD",  # 1.1
            "ME:R:S#=01:DCC=010:PH=FD010006020C0600",  # 1.2
            "CR:Ack=0:RFEMD",  # 2
        ],
        "\r",
    ) as inst:
        # mock out flush
        flush_mock = mocker.patch.object(inst, "flush", return_value=None)
        assert inst.measure(inst.Mode.voltage_dc) == 0.509 * u.volt
        # assert that flush was called once
        flush_mock.assert_called_once()


def test_parse_ph_not_in_result():
    """Raise ValueError if 'PH' is not in `result`."""
    with expected_protocol(
        ik.fluke.Fluke3000, init_sequence, init_response, "\r"
    ) as inst:
        mode = inst.Mode.temperature
        bad_result = "42"
        with pytest.raises(ValueError) as err_info:
            inst._parse(bad_result, mode)
        err_msg = err_info.value.args[0]
        assert (
            err_msg == "Cannot parse a string that does not contain a " "return value"
        )


def test_parse_wrong_mode():
    """Raise ValueError if multimeter not in the right mode."""
    with expected_protocol(
        ik.fluke.Fluke3000, init_sequence, init_response, "\r"
    ) as inst:
        mode_requested = inst.Mode.temperature
        result = "ME:R:S#=01:DCC=010:PH=FD010006020C0600"
        mode_result = inst.Mode(result.split("PH=")[-1][8:10])
        with pytest.raises(ValueError) as err_info:
            inst._parse(result, mode_requested)
        err_msg = err_info.value.args[0]
        assert (
            err_msg == f"Mode {mode_requested.name} was requested but "
            f"the Fluke 3000FC Multimeter is in mode "
            f"{mode_result.name} instead. Could not read the "
            f"requested quantity."
        )


def test_parse_factor_wrong_code():
    """Raise ValueError if code not in prefixes."""
    data = "00000012"
    byte = format(int(data[6:8], 16), "08b")
    code = int(byte[1:4], 2)
    with expected_protocol(
        ik.fluke.Fluke3000, init_sequence, init_response, "\r"
    ) as inst:
        with pytest.raises(ValueError) as err_info:
            inst._parse_factor(data)
        err_msg = err_info.value.args[0]
        assert err_msg == f"Metric prefix not recognized: {code}"
