#!/usr/bin/env python
"""
Module containing tests for the Glassman FR power supply
"""

# IMPORTS ####################################################################

import pytest

import instruments as ik
from instruments.tests import expected_protocol
from instruments.units import ureg as u


# TESTS ######################################################################

# pylint: disable=protected-access


def set_defaults(inst):
    """
    Sets default values for the voltage and current range of the Glassman FR
    to be used to test the voltage and current property getters/setters.
    """
    inst.voltage_max = 50.0 * u.kilovolt
    inst.current_max = 6.0 * u.milliamp
    inst.polarity = +1


def test_channel():
    with expected_protocol(ik.glassman.GlassmanFR, [], [], "\r") as inst:
        assert len(inst.channel) == 1
        assert inst.channel[0] == inst


def test_voltage():
    with expected_protocol(
        ik.glassman.GlassmanFR,
        ["\x01Q51", "\x01S3330000000001CD"],
        ["R00000000000040", "A"],
        "\r",
    ) as inst:
        set_defaults(inst)
        inst.voltage = 10.0 * u.kilovolt
        assert inst.voltage == 10.0 * u.kilovolt


def test_current():
    with expected_protocol(
        ik.glassman.GlassmanFR,
        ["\x01Q51", "\x01S0003330000001CD"],
        ["R00000000000040", "A"],
        "\r",
    ) as inst:
        set_defaults(inst)
        inst.current = 1.2 * u.milliamp
        assert inst.current == 1.2 * u.milliamp


def test_voltage_sense():
    with expected_protocol(
        ik.glassman.GlassmanFR, ["\x01Q51"], ["R10A00000010053"], "\r"
    ) as inst:
        set_defaults(inst)
        assert round(inst.voltage_sense) == 13.0 * u.kilovolt


def test_current_sense():
    with expected_protocol(
        ik.glassman.GlassmanFR, ["\x01Q51"], ["R0001550001004C"], "\r"
    ) as inst:
        set_defaults(inst)
        assert inst.current_sense == 2.0 * u.milliamp


def test_mode():
    with expected_protocol(
        ik.glassman.GlassmanFR,
        ["\x01Q51", "\x01Q51"],
        ["R00000000000040", "R00000000010041"],
        "\r",
    ) as inst:
        assert inst.mode == inst.Mode.voltage
        assert inst.mode == inst.Mode.current


def test_output():
    with expected_protocol(
        ik.glassman.GlassmanFR,
        ["\x01S0000000000001C4", "\x01Q51", "\x01S0000000000002C5", "\x01Q51"],
        ["A", "R00000000000040", "A", "R00000000040044"],
        "\r",
    ) as inst:
        inst.output = False
        assert not inst.output
        inst.output = True
        assert inst.output


def test_output_type_error():
    """Raise TypeError when setting output w non-boolean value."""
    with expected_protocol(ik.glassman.GlassmanFR, [], [], "\r") as inst:
        with pytest.raises(TypeError) as err_info:
            inst.output = 42
        err_msg = err_info.value.args[0]
        assert err_msg == "Output status mode must be a boolean."


@pytest.mark.parametrize("value", [0, 2])
def test_fault(value):
    """Get the instrument status: True if fault."""
    with expected_protocol(
        ik.glassman.GlassmanFR,
        ["\x01Q51"],
        [
            f"R000000000{value}004{value}",
        ],
        "\r",
    ) as inst:
        assert inst.fault == bool(value)


def test_version():
    with expected_protocol(
        ik.glassman.GlassmanFR, ["\x01V56"], ["B1465"], "\r"
    ) as inst:
        assert inst.version == "14"


def test_device_timeout():
    with expected_protocol(
        ik.glassman.GlassmanFR, ["\x01C073", "\x01C174"], ["A", "A"], "\r"
    ) as inst:
        inst.device_timeout = True
        assert inst.device_timeout
        inst.device_timeout = False
        assert not inst.device_timeout


def test_device_timeout_type_error():
    """Raise TypeError if device timeout mode not set with boolean."""
    with expected_protocol(ik.glassman.GlassmanFR, [], [], "\r") as inst:
        with pytest.raises(TypeError) as err_info:
            inst.device_timeout = 42
        err_msg = err_info.value.args[0]
        assert err_msg == "Device timeout mode must be a boolean."


def test_sendcmd():
    with expected_protocol(ik.glassman.GlassmanFR, ["\x01123ABC5C"], [], "\r") as inst:
        inst.sendcmd("123ABC")


def test_query():
    """Query the instrument."""
    response = "R123ABC5C"
    with expected_protocol(
        ik.glassman.GlassmanFR, ["\x01Q123ABCAD"], [response], "\r"
    ) as inst:
        assert inst.query("Q123ABC") == response[1:-2]


def test_query_invalid_response_code():
    """Raise ValueError when query receives an invalid response code."""
    response = "A123ABC5C"
    with expected_protocol(
        ik.glassman.GlassmanFR, ["\x01Q123ABCAD"], [response], "\r"
    ) as inst:
        with pytest.raises(ValueError) as err_info:
            inst.query("Q123ABC")
        err_msg = err_info.value.args[0]
        assert err_msg == f"Invalid response code: {response}"


def test_query_invalid_checksum():
    """Raise ValueError if query returns with invalid checksum."""
    response = "R123ABC5A"
    with expected_protocol(
        ik.glassman.GlassmanFR, ["\x01Q123ABCAD"], [response], "\r"
    ) as inst:
        with pytest.raises(ValueError) as err_info:
            inst.query("Q123ABC")
        err_msg = err_info.value.args[0]
        assert err_msg == f"Invalid checksum: {response}"


@pytest.mark.parametrize("err", ik.glassman.GlassmanFR.ErrorCode)
def test_query_error(err):
    """Raise ValueError if query returns with error."""
    err_code = err.value
    check_sum = ord(err_code) % 256
    response = f"E{err_code}{format(check_sum, '02X')}"
    with expected_protocol(
        ik.glassman.GlassmanFR, ["\x01Q123ABCAD"], [response], "\r"
    ) as inst:
        with pytest.raises(ValueError) as err_info:
            inst.query("Q123ABC")
        err_msg = err_info.value.args[0]
        assert err_msg == f"Instrument responded with error: {err.name}"


def test_reset():
    with expected_protocol(
        ik.glassman.GlassmanFR, ["\x01S0000000000004C7"], ["A"], "\r"
    ) as inst:
        inst.reset()


def test_set_status():
    with expected_protocol(
        ik.glassman.GlassmanFR,
        ["\x01S3333330000002D7", "\x01Q51"],
        ["A", "R00000000040044"],
        "\r",
    ) as inst:
        set_defaults(inst)
        inst.set_status(voltage=10 * u.kilovolt, current=1.2 * u.milliamp, output=True)
        assert inst.output
        assert inst.voltage == 10 * u.kilovolt
        assert inst.current == 1.2 * u.milliamp


def test_parse_invalid_response():
    """Raise a RunTime error if response cannot be parsed."""
    response = "000000000X00"  # invalid monitors
    with expected_protocol(ik.glassman.GlassmanFR, [], [], "\r") as inst:
        with pytest.raises(RuntimeError) as err_info:
            inst._parse_response(response)
        err_msg = err_info.value.args[0]
        assert err_msg == f"Cannot parse response packet: {response}"
