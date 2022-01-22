#!/usr/bin/env python
"""
Module containing tests for the Keithley 485 picoammeter
"""

# IMPORTS ####################################################################

import pytest

from instruments.units import ureg as u

import instruments as ik
from instruments.tests import expected_protocol


# TESTS ######################################################################

# pylint: disable=protected-access


def test_zero_check():
    with expected_protocol(
        ik.keithley.Keithley485, ["C0X", "C1X", "U0X"], ["4851000000000:"]
    ) as inst:
        inst.zero_check = False
        inst.zero_check = True
        assert inst.zero_check
        with pytest.raises(TypeError) as err_info:
            inst.zero_check = 42
        err_msg = err_info.value.args[0]
        assert err_msg == "Zero Check mode must be a boolean."


def test_log():
    with expected_protocol(
        ik.keithley.Keithley485, ["D0X", "D1X", "U0X"], ["4850100000000:"]
    ) as inst:
        inst.log = False
        inst.log = True
        assert inst.log
        with pytest.raises(TypeError) as err_info:
            inst.log = 42
        err_msg = err_info.value.args[0]
        assert err_msg == "Log mode must be a boolean."


def test_input_range():
    with expected_protocol(
        ik.keithley.Keithley485, ["R0X", "R7X", "U0X"], ["4850070000000:"]
    ) as inst:
        inst.input_range = "auto"
        inst.input_range = 2e-3
        assert inst.input_range == 2.0 * u.milliamp


def test_relative():
    with expected_protocol(
        ik.keithley.Keithley485, ["Z0X", "Z1X", "U0X"], ["4850001000000:"]
    ) as inst:
        inst.relative = False
        inst.relative = True
        assert inst.relative
        with pytest.raises(TypeError) as err_info:
            inst.relative = 42
        err_msg = err_info.value.args[0]
        assert err_msg == "Relative mode must be a boolean."


def test_eoi_mode():
    with expected_protocol(
        ik.keithley.Keithley485, ["K0X", "K1X", "U0X"], ["4850000100000:"]
    ) as inst:
        inst.eoi_mode = True
        inst.eoi_mode = False
        assert not inst.eoi_mode
        with pytest.raises(TypeError) as err_info:
            inst.eoi_mode = 42
        err_msg = err_info.value.args[0]
        assert err_msg == "EOI mode must be a boolean."


def test_trigger_mode():
    with expected_protocol(
        ik.keithley.Keithley485, ["T0X", "T5X", "U0X"], ["4850000050000:"]
    ) as inst:
        inst.trigger_mode = "continuous_ontalk"
        inst.trigger_mode = "oneshot_onx"
        assert inst.trigger_mode == "oneshot_onx"
        with pytest.raises(TypeError) as err_info:
            newval = 42
            inst.trigger_mode = newval
        err_msg = err_info.value.args[0]
        assert (
            err_msg == f"Drive must be specified as a "
            f"Keithley485.TriggerMode, got {newval} instead."
        )


def test_auto_range():
    with expected_protocol(
        ik.keithley.Keithley485, ["R0X", "U0X"], ["4850000000000:"]
    ) as inst:
        inst.auto_range()
        assert inst.input_range == "auto"


@pytest.mark.parametrize("newval", (2e-9, 2e-8, 2e-7, 2e-6, 2e-5, 2e-4, 2e-3))
def test_input_range_value(newval):
    """Set input range with a given value from list."""
    valid = ("auto", 2e-9, 2e-8, 2e-7, 2e-6, 2e-5, 2e-4, 2e-3)
    with expected_protocol(
        ik.keithley.Keithley485, [f"R{valid.index(newval)}X"], []
    ) as inst:
        inst.input_range = newval


def test_input_range_quantity():
    """Set input range with a given value from list."""
    valid = ("auto", 2e-9, 2e-8, 2e-7, 2e-6, 2e-5, 2e-4, 2e-3)
    newval = 2e-9
    quant = u.Quantity(newval, u.A)
    with expected_protocol(
        ik.keithley.Keithley485, [f"R{valid.index(newval)}X"], []
    ) as inst:
        inst.input_range = quant


def test_input_range_invalid_value():
    """Raise ValueError if invalid value is given."""
    valid = ("auto", 2e-9, 2e-8, 2e-7, 2e-6, 2e-5, 2e-4, 2e-3)
    with expected_protocol(ik.keithley.Keithley485, [], []) as inst:
        with pytest.raises(ValueError) as err_info:
            inst.input_range = 42
        err_msg = err_info.value.args[0]
        assert err_msg == f"Valid range settings are: {valid}"


def test_input_range_invalid_type():
    """Raise TypeError if invalid type is given."""
    invalid_type = [42]
    with expected_protocol(ik.keithley.Keithley485, [], []) as inst:
        with pytest.raises(TypeError) as err_info:
            inst.input_range = invalid_type
        err_msg = err_info.value.args[0]
        assert (
            err_msg == f"Range setting must be specified as a float, "
            f"int, or the string `auto`, got "
            f"{type(invalid_type)}"
        )


def test_input_range_invalid_string():
    """Raise ValueError if input range set with invalid string."""
    with expected_protocol(ik.keithley.Keithley485, [], []) as inst:
        with pytest.raises(ValueError) as err_info:
            inst.input_range = "2e-9"
        err_msg = err_info.value.args[0]
        assert (
            err_msg == "Only `auto` is acceptable when specifying the "
            "range as a string."
        )


def test_get_status():
    with expected_protocol(
        ik.keithley.Keithley485, ["U0X"], ["4850000000000:"]
    ) as inst:
        inst.get_status()


def test_measure():
    with expected_protocol(
        ik.keithley.Keithley485, ["X", "X"], ["NDCA+1.2345E-9", "NDCL-9.0000E+0"]
    ) as inst:
        assert 1.2345 * u.nanoamp == inst.measure()
        assert 1 * u.nanoamp == inst.measure()


def test_get_status_word_fails():
    """Raise IOError if status word query fails > 5 times."""
    with expected_protocol(
        ik.keithley.Keithley485,
        ["U0X", "U0X", "U0X", "U0X", "U0X"],
        ["", "", "", "", ""],
    ) as inst:
        with pytest.raises(IOError) as err_info:
            inst._get_status_word()
        err_msg = err_info.value.args[0]
        assert err_msg == "Could not retrieve status word"


def test_parse_status_word_wrong_prefix():
    """Raise ValueError if statusword has wrong prefix."""
    wrong_statusword = "wrong statusword"
    with expected_protocol(ik.keithley.Keithley485, [], []) as inst:
        with pytest.raises(ValueError) as err_info:
            inst._parse_status_word(wrong_statusword)
        err_msg = err_info.value.args[0]
        assert (
            err_msg == f"Status word starts with wrong prefix: " f"{wrong_statusword}"
        )


def test_parse_status_word_cannot_parse():
    """Raise RuntimeError if statusword cannot be parsed."""
    bad_statusword = "485FFFFFFFFFF"
    with expected_protocol(ik.keithley.Keithley485, [], []) as inst:
        with pytest.raises(RuntimeError) as err_info:
            inst._parse_status_word(bad_statusword)
        err_msg = err_info.value.args[0]
        assert err_msg == f"Cannot parse status word: {bad_statusword}"


def test_parse_measurement_invalid_status():
    """Raise ValueError if invalild status encountered."""
    status = "L"
    bad_measurement = f"{status}DCA+1.2345E-9"
    with expected_protocol(ik.keithley.Keithley485, [], []) as inst:
        with pytest.raises(ValueError) as err_info:
            inst._parse_measurement(bad_measurement)
        err_msg = err_info.value.args[0]
        assert (
            err_msg == f"Invalid status word in measurement: "
            f"{bytes(status, 'utf-8')}"
        )


def test_parse_measurement_bad_status():
    """Raise ValueError if non-normal status encountered."""
    status = ik.keithley.Keithley485.Status.overflow
    bad_measurement = f"{status.value.decode('utf-8')}DCA+1.2345E-9"
    with expected_protocol(ik.keithley.Keithley485, [], []) as inst:
        with pytest.raises(ValueError) as err_info:
            inst._parse_measurement(bad_measurement)
        err_msg = err_info.value.args[0]
        assert err_msg == f"Instrument not in normal mode: {status.name}"


def test_parse_measurement_bad_function():
    """Raise ValueError if non-normal function encountered."""
    function = "XX"
    bad_measurement = f"N{function}A+1.2345E-9"
    with expected_protocol(ik.keithley.Keithley485, [], []) as inst:
        with pytest.raises(ValueError) as err_info:
            inst._parse_measurement(bad_measurement)
        err_msg = err_info.value.args[0]
        assert (
            err_msg == f"Instrument not returning DC function: "
            f"{bytes(function, 'utf-8')}"
        )


def test_parse_measurement_bad_measurement():
    """Raise ValueError if non-normal function encountered."""
    bad_measurement = f"NDCA+1.23X5E-9"
    with expected_protocol(ik.keithley.Keithley485, [], []) as inst:
        with pytest.raises(Exception) as err_info:
            inst._parse_measurement(bad_measurement)
        err_msg = err_info.value.args[0]
        assert err_msg == f"Cannot parse measurement: {bad_measurement}"
