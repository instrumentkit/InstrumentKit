#!/usr/bin/env python
"""
Module containing tests for the Keithley 580 digital multimeter.
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
    return "Y:X:"


@pytest.fixture
def create_statusword():
    """Create a function that can create a status word.

    Variables used in tests can be set manually, but useful default
    values are set as well. Note: The terminator is not created, since
    it is already sent by `expected_protocol`.

    :return: Method to make a status word.
    :rtype: `method`
    """

    def make_statusword(
        drive=b"1",
        polarity=b"0",
        drycircuit=b"0",
        operate=b"0",
        rng=b"0",
        relative=b"0",
        trigger=b"1",
        linefreq=b"0",
    ):
        """Create the status word."""
        # other variables
        eoi = b"0"
        sqrondata = b"0"
        sqronerror = b"0"

        status_word = struct.pack(
            "@8c2s2sc",
            drive,
            polarity,
            drycircuit,
            operate,
            rng,
            relative,
            eoi,
            trigger,
            sqrondata,
            sqronerror,
            linefreq,
        )

        return b"580" + status_word

    return make_statusword


@pytest.fixture
def create_measurement():
    """Create a function that can create a measurement.

    Variables used in tests can be set manually, but useful default
    values are set as well.

    :return: Method to make a measurement.
    :rtype: `method`
    """

    def make_measurement(
        status=b"N", polarity=b"+", drycircuit=b"D", drive=b"P", resistance=b"42"
    ):
        """Create a measurement."""
        resistance = bytes(resistance.decode().zfill(11), "utf-8")
        measurement = struct.pack(
            "@4c11s", status, polarity, drycircuit, drive, resistance
        )

        return measurement

    return make_measurement


@pytest.fixture(autouse=True)
def mock_time(mocker):
    """Mock the time.sleep object for use.

    Use by default, such that getting status word is fast in tests.
    """
    return mocker.patch.object(time, "sleep", return_value=None)


# PROPERTIES #


@pytest.mark.parametrize("newval", ik.keithley.Keithley580.Polarity)
def test_polarity(init, create_statusword, newval):
    """Get / set instrument polarity."""
    status_word = create_statusword(polarity=bytes(str(newval.value), "utf-8"))
    with expected_protocol(
        ik.keithley.Keithley580,
        [init, f"P{newval.value}X" + ":", "U0X:", ":"],
        [status_word + b":"],
        sep="\n",
    ) as inst:
        inst.polarity = newval
        assert inst.polarity == newval


@pytest.mark.parametrize(
    "newval_str", [it.name for it in ik.keithley.Keithley580.Polarity]
)
def test_polarity_string(init, newval_str):
    """Set polarity with a string."""
    newval = ik.keithley.Keithley580.Polarity[newval_str]
    with expected_protocol(
        ik.keithley.Keithley580,
        [
            init,
            f"P{newval.value}X" + ":",
        ],
        [],
        sep="\n",
    ) as inst:
        inst.polarity = newval_str


def test_polarity_wrong_type(init):
    """Raise TypeError if setting polarity with wrong type."""
    wrong_type = 42
    with expected_protocol(
        ik.keithley.Keithley580,
        [
            init,
        ],
        [],
        sep="\n",
    ) as inst:
        with pytest.raises(TypeError) as err_info:
            inst.polarity = wrong_type
        err_msg = err_info.value.args[0]
        assert (
            err_msg == f"Polarity must be specified as a "
            f"Keithley580.Polarity, got {wrong_type} "
            f"instead."
        )


@pytest.mark.parametrize("newval", ik.keithley.Keithley580.Drive)
def test_drive(init, create_statusword, newval):
    """Get / set instrument drive."""
    status_word = create_statusword(drive=bytes(str(newval.value), "utf-8"))
    with expected_protocol(
        ik.keithley.Keithley580,
        [init, f"D{newval.value}X" + ":", "U0X:", ":"],
        [status_word + b":"],
        sep="\n",
    ) as inst:
        inst.drive = newval
        assert inst.drive == newval


@pytest.mark.parametrize(
    "newval_str", [it.name for it in ik.keithley.Keithley580.Drive]
)
def test_drive_string(init, newval_str):
    """Set drive with a string."""
    newval = ik.keithley.Keithley580.Drive[newval_str]
    with expected_protocol(
        ik.keithley.Keithley580,
        [
            init,
            f"D{newval.value}X" + ":",
        ],
        [],
        sep="\n",
    ) as inst:
        inst.drive = newval_str


def test_drive_wrong_type(init):
    """Raise TypeError if setting drive with wrong type."""
    wrong_type = 42
    with expected_protocol(
        ik.keithley.Keithley580,
        [
            init,
        ],
        [],
        sep="\n",
    ) as inst:
        with pytest.raises(TypeError) as err_info:
            inst.drive = wrong_type
        err_msg = err_info.value.args[0]
        assert (
            err_msg == f"Drive must be specified as a "
            f"Keithley580.Drive, got {wrong_type} "
            f"instead."
        )


@pytest.mark.parametrize("newval", (True, False))
def test_dry_circuit_test(init, create_statusword, newval):
    """Get / set dry circuit test."""
    status_word = create_statusword(drycircuit=bytes(str(int(newval)), "utf-8"))
    with expected_protocol(
        ik.keithley.Keithley580,
        [init, f"C{int(newval)}X" + ":", "U0X:", ":"],
        [status_word + b":"],
        sep="\n",
    ) as inst:
        inst.dry_circuit_test = newval
        assert inst.dry_circuit_test == newval


def test_dry_circuit_test_wrong_type(init):
    """Raise TypeError if setting dry circuit test with wrong type."""
    wrong_type = 42
    with expected_protocol(
        ik.keithley.Keithley580,
        [
            init,
        ],
        [],
        sep="\n",
    ) as inst:
        with pytest.raises(TypeError) as err_info:
            inst.dry_circuit_test = wrong_type
        err_msg = err_info.value.args[0]
        assert err_msg == "DryCircuitTest mode must be a boolean."


@pytest.mark.parametrize("newval", (True, False))
def test_operate(init, create_statusword, newval):
    """Get / set operate."""
    status_word = create_statusword(operate=bytes(str(int(newval)), "utf-8"))
    with expected_protocol(
        ik.keithley.Keithley580,
        [init, f"O{int(newval)}X" + ":", "U0X:", ":"],
        [status_word + b":"],
        sep="\n",
    ) as inst:
        inst.operate = newval
        assert inst.operate == newval


def test_operate_wrong_type(init):
    """Raise TypeError if setting operate with wrong type."""
    wrong_type = 42
    with expected_protocol(
        ik.keithley.Keithley580,
        [
            init,
        ],
        [],
        sep="\n",
    ) as inst:
        with pytest.raises(TypeError) as err_info:
            inst.operate = wrong_type
        err_msg = err_info.value.args[0]
        assert err_msg == "Operate mode must be a boolean."


@pytest.mark.parametrize("newval", (True, False))
def test_relative(init, create_statusword, newval):
    """Get / set relative."""
    status_word = create_statusword(relative=bytes(str(int(newval)), "utf-8"))
    with expected_protocol(
        ik.keithley.Keithley580,
        [init, f"Z{int(newval)}X" + ":", "U0X:", ":"],
        [status_word + b":"],
        sep="\n",
    ) as inst:
        inst.relative = newval
        assert inst.relative == newval


def test_relative_wrong_type(init):
    """Raise TypeError if setting relative with wrong type."""
    wrong_type = 42
    with expected_protocol(
        ik.keithley.Keithley580,
        [
            init,
        ],
        [],
        sep="\n",
    ) as inst:
        with pytest.raises(TypeError) as err_info:
            inst.relative = wrong_type
        err_msg = err_info.value.args[0]
        assert err_msg == "Relative mode must be a boolean."


def test_trigger_mode_get(init):
    """Getting trigger mode raises NotImplementedError.

    Unclear why this is not implemented.
    """
    with expected_protocol(
        ik.keithley.Keithley580,
        [
            init,
        ],
        [],
        sep="\n",
    ) as inst:
        with pytest.raises(NotImplementedError):
            assert inst.trigger_mode


@pytest.mark.parametrize("newval", ik.keithley.Keithley580.TriggerMode)
def test_trigger_mode_set(init, newval):
    """Set instrument trigger mode."""
    with expected_protocol(
        ik.keithley.Keithley580, [init, f"T{newval.value}X" + ":"], [], sep="\n"
    ) as inst:
        inst.trigger_mode = newval


@pytest.mark.parametrize("newval", ik.keithley.Keithley580.TriggerMode)
def test_trigger_mode_set_string(init, newval):
    """Set instrument trigger mode as a string."""
    newval_str = newval.name
    with expected_protocol(
        ik.keithley.Keithley580, [init, f"T{newval.value}X" + ":"], [], sep="\n"
    ) as inst:
        inst.trigger_mode = newval_str


def test_trigger_mode_set_type_error(init):
    """Raise TypeError when setting trigger mode with wrong type."""
    wrong_type = 42
    with expected_protocol(ik.keithley.Keithley580, [init], [], sep="\n") as inst:
        with pytest.raises(TypeError) as err_info:
            inst.trigger_mode = wrong_type
        err_msg = err_info.value.args[0]
        assert (
            err_msg == f"Drive must be specified as a "
            f"Keithley580.TriggerMode, got "
            f"{wrong_type} instead."
        )


@pytest.mark.parametrize("newval", (2e-1, 2e0, 2e1, 2e2, 2e3, 2e4, 2e5))
def test_input_range_float(init, create_statusword, newval):
    """Get / set input range with a float, unitful and unitless."""
    valid = ("auto", 2e-1, 2e0, 2e1, 2e2, 2e3, 2e4, 2e5)
    newval_unitful = newval * u.ohm
    newval_index = valid.index(newval)

    status_word = create_statusword(rng=bytes(str(newval_index), "utf-8"))

    with expected_protocol(
        ik.keithley.Keithley580,
        [init, f"R{newval_index}X" + ":", f"R{newval_index}X" + ":", "U0X:", ":"],
        [status_word + b":"],
        sep="\n",
    ) as inst:
        inst.input_range = newval
        inst.input_range = newval_unitful
        assert inst.input_range == newval_unitful


def test_input_range_auto(init, create_statusword):
    """Get / set input range auto."""
    newval = "auto"
    newval_index = 0

    status_word = create_statusword(rng=bytes(str(newval_index), "utf-8"))

    with expected_protocol(
        ik.keithley.Keithley580,
        [init, f"R{newval_index}X" + ":", "U0X:", ":"],
        [status_word + b":"],
        sep="\n",
    ) as inst:
        inst.input_range = newval
        assert inst.input_range == newval


@given(
    newval=st.floats().filter(lambda x: x not in (2e-1, 2e0, 2e1, 2e2, 2e3, 2e4, 2e5))
)
def test_input_range_float_value_error(init, newval):
    """Raise ValueError if input range set to invalid value."""
    valid = ("auto", 2e-1, 2e0, 2e1, 2e2, 2e3, 2e4, 2e5)
    with expected_protocol(ik.keithley.Keithley580, [init], [], sep="\n") as inst:
        with pytest.raises(ValueError) as err_info:
            inst.input_range = newval
        err_msg = err_info.value.args[0]
        assert err_msg == f"Valid range settings are: {valid}"


def test_input_range_auto_value_error(init):
    """Raise ValueError if string set as input range is not 'auto'."""
    newval = "automatic"

    with expected_protocol(ik.keithley.Keithley580, [init], [], sep="\n") as inst:
        with pytest.raises(ValueError) as err_info:
            inst.input_range = newval
        err_msg = err_info.value.args[0]
        assert (
            err_msg == 'Only "auto" is acceptable when specifying the '
            "input range as a string."
        )


def test_input_range_type_error(init):
    """Raise TypeError if input range is set with wrong type."""
    wrong_type = {"The Answer": 42}

    with expected_protocol(ik.keithley.Keithley580, [init], [], sep="\n") as inst:
        with pytest.raises(TypeError) as err_info:
            inst.input_range = wrong_type
        err_msg = err_info.value.args[0]
        assert (
            err_msg == f"Range setting must be specified as a float, "
            f'int, or the string "auto", got '
            f"{type(wrong_type)}"
        )


# METHODS #


def test_trigger(init):
    """Send a trigger to instrument."""
    with expected_protocol(ik.keithley.Keithley580, [init, "X:"], [], sep="\n") as inst:
        inst.trigger()


def test_auto_range(init):
    """Put instrument into auto range mode."""
    with expected_protocol(
        ik.keithley.Keithley580, [init, "R0X:"], [], sep="\n"
    ) as inst:
        inst.auto_range()


def test_set_calibration_value(init):
    """Raise NotImplementedError when trying to set calibration value."""
    value = None
    with expected_protocol(ik.keithley.Keithley580, [init], [], sep="\n") as inst:
        with pytest.raises(NotImplementedError) as err_info:
            inst.set_calibration_value(value)
        err_msg = err_info.value.args[0]
        assert err_msg == "setCalibrationValue not implemented"


def test_store_calibration_constants(init):
    """Raise NotImplementedError when trying to store calibration constants."""
    with expected_protocol(ik.keithley.Keithley580, [init], [], sep="\n") as inst:
        with pytest.raises(NotImplementedError) as err_info:
            inst.store_calibration_constants()
        err_msg = err_info.value.args[0]
        assert err_msg == "storeCalibrationConstants not implemented"


# STATUS WORD #


def test_get_status_word(init, create_statusword, mock_time):
    """Test getting a default status word."""
    status_word = create_statusword()

    with expected_protocol(
        ik.keithley.Keithley580, [init, "U0X:", ":"], [status_word + b":"], sep="\n"
    ) as inst:
        assert inst.get_status_word() == status_word
        mock_time.assert_called_with(1)


def test_get_status_word_fails(init, mock_time):
    """Raise IOError after 5 reads with bad returns."""
    wrong_status_word = b"195 12345"

    with expected_protocol(
        ik.keithley.Keithley580,
        [init, "U0X:", ":", "U0X:", ":", "U0X:", ":", "U0X:", ":", "U0X:", ":"],
        [
            wrong_status_word,
            wrong_status_word,
            wrong_status_word,
            wrong_status_word,
            wrong_status_word,
        ],
        sep="\n",
    ) as inst:
        with pytest.raises(IOError) as err_info:
            inst.get_status_word()
        err_msg = err_info.value.args[0]
        assert err_msg == "could not retrieve status word"

        mock_time.assert_called_with(1)


@pytest.mark.parametrize("line_frequency", (("0", "60Hz"), ("1", "50Hz")))
def test_parse_status_word(init, create_statusword, line_frequency):
    """Parse a given status word.

    Note: full range of parameters explored in individual routines.
    Here, we thus just use the default status word created by the
    fixture and only parametrize where other routines do not.
    """
    status_word = create_statusword(linefreq=bytes(line_frequency[0], "utf-8"))
    # create the dictionary to compare to
    expected_dict = {
        "drive": "dc",
        "polarity": "+",
        "drycircuit": False,
        "operate": False,
        "range": "auto",
        "relative": False,
        "eoi": b"0",
        "trigger": True,
        "sqrondata": struct.pack("@2s", b"0"),
        "sqronerror": struct.pack("@2s", b"0"),
        "linefreq": line_frequency[1],
    }
    with expected_protocol(ik.keithley.Keithley580, [init], [], sep="\n") as inst:
        # add terminator to expected dict:
        expected_dict["terminator"] = inst.terminator
        assert inst.parse_status_word(status_word) == expected_dict


@given(
    drive=st.integers(min_value=2, max_value=9),
    polarity=st.integers(min_value=2, max_value=9),
    rng=st.integers(min_value=8, max_value=9),
    linefreq=st.integers(min_value=2, max_value=9),
)
def test_parse_status_word_invalid_values(
    init, create_statusword, drive, polarity, rng, linefreq
):
    """Raise RuntimeError if status word contains invalid values."""
    status_word = create_statusword(
        drive=bytes(str(drive), "utf-8"),
        polarity=bytes(str(polarity), "utf-8"),
        rng=bytes(str(rng), "utf-8"),
        linefreq=bytes(str(linefreq), "utf-8"),
    )
    with expected_protocol(ik.keithley.Keithley580, [init], [], sep="\n") as inst:
        with pytest.raises(RuntimeError) as err_info:
            inst.parse_status_word(status_word)
        err_msg = err_info.value.args[0]
        assert err_msg == f"Cannot parse status word: {status_word}"


def test_parse_status_word_invalid_prefix(init):
    """Raise ValueError if status word has invalid prefix."""
    invalid_status_word = b"314 424242"
    with expected_protocol(ik.keithley.Keithley580, [init], [], sep="\n") as inst:
        with pytest.raises(ValueError) as err_info:
            inst.parse_status_word(invalid_status_word)
        err_msg = err_info.value.args[0]
        assert (
            err_msg == f"Status word starts with wrong prefix: "
            f"{invalid_status_word}"
        )


# MEASUREMENT #


@given(resistance=st.floats(min_value=0.001, max_value=1000000))
def test_measure(init, create_measurement, resistance):
    """Perform a resistance measurement."""
    # cap resistance at max of 11 character with given max_value
    resistance_byte = bytes(f"{resistance:.3f}", "utf-8")
    measurement = create_measurement(resistance=resistance_byte)
    with expected_protocol(
        ik.keithley.Keithley580,
        [init, "X:", ":"],  # trigger
        [measurement + b":"],
        sep="\n",
    ) as inst:
        read_value = inst.measure()
        assert read_value.magnitude == pytest.approx(resistance, rel=1e-5)
        assert read_value.units == u.ohm


@pytest.mark.parametrize("status", (b"S", b"N", b"O", b"Z"))
@pytest.mark.parametrize("polarity", (b"+", b"-"))
@pytest.mark.parametrize("drycircuit", (b"N", b"D"))
@pytest.mark.parametrize("drive", (b"P", b"D"))
def test_parse_measurement(
    init, create_measurement, status, polarity, drycircuit, drive
):
    """Parse a given measurement."""
    resistance = b"42"
    measurement = create_measurement(
        status=status,
        polarity=polarity,
        drycircuit=drycircuit,
        drive=drive,
        resistance=resistance,
    )

    # valid states
    valid = {
        "status": {b"S": "standby", b"N": "normal", b"O": "overflow", b"Z": "relative"},
        "polarity": {b"+": "+", b"-": "-"},
        "drycircuit": {b"N": False, b"D": True},
        "drive": {b"P": "pulsed", b"D": "dc"},
    }

    # create expected dictionary
    dict_expected = {
        "status": valid["status"][status],
        "polarity": valid["polarity"][polarity],
        "drycircuit": valid["drycircuit"][drycircuit],
        "drive": valid["drive"][drive],
        "resistance": float(resistance.decode()) * u.ohm,
    }

    with expected_protocol(
        ik.keithley.Keithley580,
        [
            init,
        ],
        [],
        sep="\n",
    ) as inst:
        assert inst.parse_measurement(measurement) == dict_expected


def test_parse_measurement_invalid(init, create_measurement):
    """Raise an exception if the status contains invalid character."""
    measurement = create_measurement(status=bytes("V", "utf-8"))

    with expected_protocol(
        ik.keithley.Keithley580,
        [
            init,
        ],
        [],
        sep="\n",
    ) as inst:
        with pytest.raises(Exception) as exc_info:
            inst.parse_measurement(measurement)
        err_msg = exc_info.value.args[0]
        assert err_msg == f"Cannot parse measurement: {measurement}"


# COMMUNICATION METHODS #


def test_sendcmd(init):
    """Send a command to the instrument."""
    cmd = "COMMAND"
    with expected_protocol(
        ik.keithley.Keithley580, [init, cmd + ":"], [], sep="\n"
    ) as inst:
        inst.sendcmd(cmd)


def test_query(init):
    """Query the instrument."""
    cmd = "COMMAND"
    answer = "ANSWER"
    with expected_protocol(
        ik.keithley.Keithley580, [init, cmd + ":"], [answer + ":"], sep="\n"
    ) as inst:
        assert inst.query(cmd) == answer
