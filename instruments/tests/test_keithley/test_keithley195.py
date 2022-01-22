#!/usr/bin/env python
"""
Module containing tests for the Keithley 195 digital multimeter.
"""

# IMPORTS ####################################################################

import struct
import time

from hypothesis import (
    given,
    strategies as st,
)
import pytest

import instruments as ik
from instruments.tests import expected_protocol
from instruments.units import ureg as u

# TESTS ######################################################################


# pylint: disable=redefined-outer-name


# PYTEST FIXTURES FOR INITIALIZATION #


@pytest.fixture
def init():
    """Returns the initialization command that is sent to instrument."""
    return "YX\nG1DX"


@pytest.fixture
def statusword():
    """Return a standard statusword for the status of the instrument."""
    trigger = b"1"  # talk_one_shot
    mode = b"2"  # resistance
    range = b"3"  # 2kOhm in resistance mode
    eoi = b"1"  # disabled
    buffer = b"3"  # reading done, currently unused
    rate = b"5"  # Line cycle integration
    srqmode = b"0"  # disabled
    relative = b"1"  # relative mode is activated
    delay = b"0"  # no delay, currently unused
    multiplex = b"0"  # multiplex enabled
    selftest = b"2"  # self test successful, currently unused
    dataformat = b"1"  # Readings without prefix/suffix.
    datacontrol = b"0"  # Readings without prefix/suffix.
    filter = b"0"  # filter disabled
    terminator = b"1"

    statusword_p1 = b"195 "  # sends a space after 195!
    statusword_p2 = struct.pack(
        "@4c2s3c2s5c2s",
        trigger,
        mode,
        range,
        eoi,
        buffer,
        rate,
        srqmode,
        relative,
        delay,
        multiplex,
        selftest,
        dataformat,
        datacontrol,
        filter,
        terminator,
    )
    return statusword_p1 + statusword_p2


# TEST INSTRUMENT #


def test_keithley195_mode(init, statusword):
    """Get / set the measurement mode."""
    with expected_protocol(
        ik.keithley.Keithley195, [init, "F2DX", "U0DX"], [statusword], sep="\n"
    ) as mul:
        mul.mode = mul.Mode.resistance
        assert mul.mode == mul.Mode.resistance


def test_keithley195_mode_string(init, statusword):
    """Get / set the measurement mode using a string."""
    with expected_protocol(
        ik.keithley.Keithley195, [init, "F2DX", "U0DX"], [statusword], sep="\n"
    ) as mul:
        mul.mode = "resistance"
        assert mul.mode == mul.Mode.resistance


def test_keithley195_mode_type_error(init):
    """Raise type error when setting the mode with the wrong type."""
    wrong_type = 42
    with expected_protocol(ik.keithley.Keithley195, [init], [], sep="\n") as mul:
        with pytest.raises(TypeError) as err_info:
            mul.mode = wrong_type
        err_msg = err_info.value.args[0]
        assert (
            err_msg == f"Mode must be specified as a Keithley195.Mode "
            f"value, got {wrong_type} instead."
        )


def test_keithley195_trigger_mode(init, statusword):
    """Get / set the trigger mode."""
    with expected_protocol(
        ik.keithley.Keithley195, [init, "T1X", "U0DX"], [statusword], sep="\n"
    ) as mul:
        mul.trigger_mode = mul.TriggerMode.talk_one_shot
        assert mul.trigger_mode == mul.TriggerMode.talk_one_shot


def test_keithley195_trigger_mode_string(init, statusword):
    """Get / set the trigger using a string."""
    with expected_protocol(
        ik.keithley.Keithley195, [init, "T1X", "U0DX"], [statusword], sep="\n"
    ) as mul:
        mul.trigger_mode = "talk_one_shot"
        assert mul.trigger_mode == mul.TriggerMode.talk_one_shot


def test_keithley195_trigger_mode_type_error(init):
    """Raise type error when setting the trigger mode with the wrong type."""
    wrong_type = 42
    with expected_protocol(ik.keithley.Keithley195, [init], [], sep="\n") as mul:
        with pytest.raises(TypeError) as err_info:
            mul.trigger_mode = wrong_type
        err_msg = err_info.value.args[0]
        assert (
            err_msg == f"Drive must be specified as a "
            f"Keithley195.TriggerMode, got {wrong_type} instead."
        )


def test_keithley195_relative(init, statusword):
    """Get / set the relative mode"""
    with expected_protocol(
        ik.keithley.Keithley195, [init, "Z0DX", "Z1DX", "U0DX"], [statusword], sep="\n"
    ) as mul:
        mul.relative = False
        mul.relative = True
        assert mul.relative


def test_keithley195_relative_type_error(init):
    """Raise type error when setting relative non-bool."""
    wrong_type = 42
    with expected_protocol(
        ik.keithley.Keithley195,
        [
            init,
        ],
        [],
        sep="\n",
    ) as mul:
        with pytest.raises(TypeError) as err_info:
            mul.relative = wrong_type
        err_msg = err_info.value.args[0]
        assert err_msg == "Relative mode must be a boolean."


@pytest.mark.parametrize("range", ik.keithley.Keithley195.ValidRange.resistance.value)
def test_keithley195_input_range(init, statusword, range):
    """Get / set input range.

    Set unitful and w/o units.
    """
    mode = ik.keithley.Keithley195.Mode(int(statusword.decode()[5]))
    index = ik.keithley.Keithley195.ValidRange[mode.name].value.index(range)
    # new statusword
    new_statusword = list(statusword.decode())
    new_statusword[6] = str(index + 1)
    new_statusword = "".join(new_statusword)
    # units
    units = ik.keithley.keithley195.UNITS2[mode]
    with expected_protocol(
        ik.keithley.Keithley195,
        [
            init,
            "U0DX",
            f"R{index + 1}DX",
            "U0DX",
            f"R{index + 1}DX",
            "U0DX",  # query
            "U0DX",
        ],
        [statusword, statusword, new_statusword, new_statusword],
        sep="\n",
    ) as mul:
        mul.input_range = range
        mul.input_range = u.Quantity(range, units)
        assert mul.input_range == range * units


def test_keithley195_input_range_auto(init, statusword):
    """Get / set input range auto."""
    # new statusword
    new_statusword = list(statusword.decode())
    new_statusword[6] = "0"
    new_statusword = "".join(new_statusword)
    with expected_protocol(
        ik.keithley.Keithley195, [init, "R0DX", "U0DX"], [new_statusword], sep="\n"
    ) as mul:
        mul.input_range = "Auto"
        assert mul.input_range == "auto"


def test_keithley195_input_range_set_wrong_string(init):
    """Raise Value error if input range set w/ string other than 'auto'."""
    bad_string = "forty-two"
    with expected_protocol(ik.keithley.Keithley195, [init], [], sep="\n") as mul:
        with pytest.raises(ValueError) as err_info:
            mul.input_range = bad_string
        err_msg = err_info.value.args[0]
        assert (
            err_msg == 'Only "auto" is acceptable when specifying the '
            "input range as a string."
        )


def test_keithley195_input_range_set_wrong_range(init, statusword):
    """Raise Value error if input range set w/ out of range value."""
    mode = ik.keithley.Keithley195.Mode(int(statusword.decode()[5]))
    valid = ik.keithley.Keithley195.ValidRange[mode.name].value
    out_of_range_value = 42
    with expected_protocol(
        ik.keithley.Keithley195, [init, "U0DX"], [statusword], sep="\n"
    ) as mul:
        with pytest.raises(ValueError) as err_info:
            mul.input_range = out_of_range_value
        err_msg = err_info.value.args[0]
        assert err_msg == f"Valid range settings for mode {mode} are: {valid}"


def test_keithley195_input_range_set_wrong_type(init, statusword):
    """Raise TypeError  if input range set w/ wrong type."""
    wrong_type = {"The Answer": 42}
    with expected_protocol(
        ik.keithley.Keithley195, [init, "U0DX"], [statusword], sep="\n"
    ) as mul:
        with pytest.raises(TypeError) as err_info:
            mul.input_range = wrong_type
        err_msg = err_info.value.args[0]
        assert (
            err_msg == f"Range setting must be specified as a float, "
            f'int, or the string "auto", got '
            f"{type(wrong_type)}"
        )


@given(value=st.floats(allow_infinity=False, allow_nan=False))
def test_measure_mode_is_none(init, statusword, value):
    """Get a measurement in current measure mode."""
    mode = ik.keithley.Keithley195.Mode(int(statusword.decode()[5]))
    units = ik.keithley.keithley195.UNITS2[mode]
    with expected_protocol(
        ik.keithley.Keithley195, [init, "U0DX"], [statusword, f"{value}"], sep="\n"
    ) as mul:
        assert mul.measure() == value * units


def test_measure_mode_is_current(init, statusword):
    """Get a measurement with given mode, which is already set."""
    mode = ik.keithley.Keithley195.Mode(int(statusword.decode()[5]))
    units = ik.keithley.keithley195.UNITS2[mode]
    value = 3.14
    with expected_protocol(
        ik.keithley.Keithley195, [init, "U0DX"], [statusword, f"{value}"], sep="\n"
    ) as mul:
        assert mul.measure(mode=mode) == value * units


def test_measure_new_mode(init, statusword, mocker):
    """Get a measurement with given mode, which is already set.

    Mock time.sleep() call and assert it is called with 2 seconds.
    """
    # patch call to time.sleep with mock
    mock_time = mocker.patch.object(time, "sleep", return_value=None)

    # new modes
    new_mode = ik.keithley.Keithley195.Mode(0)
    units = ik.keithley.keithley195.UNITS2[new_mode]
    value = 3.14
    with expected_protocol(
        ik.keithley.Keithley195,
        [init, "U0DX", "F0DX"],  # send new mode
        [statusword, f"{value}"],
        sep="\n",
    ) as mul:
        assert mul.measure(mode=new_mode) == value * units

        # assert time.sleep is called with 2 second argument
        mock_time.assert_called_with(2)


def test_parse_status_word_value_error(init):
    """Raise ValueError if status word does not start with '195'."""
    wrong_statusword = "42 314"
    with expected_protocol(
        ik.keithley.Keithley195,
        [
            init,
        ],
        [],
        sep="\n",
    ) as mul:
        with pytest.raises(ValueError) as err_info:
            mul.parse_status_word(wrong_statusword)
        err_msg = err_info.value.args[0]
        assert (
            err_msg == f"Status word starts with wrong prefix, expected "
            f"195, got {wrong_statusword}"
        )


def test_trigger(init):
    """Send a trigger command."""
    with expected_protocol(ik.keithley.Keithley195, [init, "X"], [], sep="\n") as mul:
        mul.trigger()


def test_auto_range(init):
    """Set input range to 'auto'."""
    with expected_protocol(
        ik.keithley.Keithley195,
        [
            init,
            "R0DX",
        ],
        [],
        sep="\n",
    ) as mul:
        mul.auto_range()
