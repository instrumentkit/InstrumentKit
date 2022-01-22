#!/usr/bin/env python
"""
Module containing tests for generic SCPI instruments
"""

# IMPORTS ####################################################################

from hypothesis import given, strategies as st
import pytest

from instruments.units import ureg as u

import instruments as ik
from instruments.tests import expected_protocol, make_name_test, unit_eq

# TESTS ######################################################################


test_scpi_multimeter_name = make_name_test(ik.generic_scpi.SCPIInstrument)


def test_scpi_instrument_scpi_version():
    """Get name of instrument."""
    retval = "12345"
    with expected_protocol(
        ik.generic_scpi.SCPIInstrument, ["SYST:VERS?"], [f"{retval}"]
    ) as inst:
        assert inst.scpi_version == retval


@pytest.mark.parametrize("retval", ("0", "1"))
def test_scpi_instrument_op_complete(retval):
    """Check if operation is completed."""
    with expected_protocol(
        ik.generic_scpi.SCPIInstrument, ["*OPC?"], [f"{retval}"]
    ) as inst:
        assert inst.op_complete == bool(int(retval))


@pytest.mark.parametrize("retval", ("off", "0", 0, False))
def test_scpi_instrument_power_on_status_off(retval):
    """Get / set power on status for instrument to on."""
    with expected_protocol(
        ik.generic_scpi.SCPIInstrument, ["*PSC 0", "*PSC?"], ["0"]
    ) as inst:
        inst.power_on_status = retval
        assert not inst.power_on_status


@pytest.mark.parametrize("retval", ("on", "1", 1, True))
def test_scpi_instrument_power_on_status_on(retval):
    """Get / set power on status for instrument to on."""
    with expected_protocol(
        ik.generic_scpi.SCPIInstrument, ["*PSC 1", "*PSC?"], ["1"]
    ) as inst:
        inst.power_on_status = retval
        assert inst.power_on_status


def test_scpi_instrument_power_on_status_value_error():
    """Raise ValueError if power on status set with invalid value."""
    with expected_protocol(ik.generic_scpi.SCPIInstrument, [], []) as inst:
        with pytest.raises(ValueError):
            inst.power_on_status = 42


def test_scpi_instrument_self_test_ok():
    """Check if self test returns okay."""
    with expected_protocol(
        ik.generic_scpi.SCPIInstrument, ["*TST?", "*TST?"], ["0", "not ok"]  # ok
    ) as inst:
        assert inst.self_test_ok
        assert not inst.self_test_ok


def test_scpi_instrument_reset():
    """Reset the instrument."""
    with expected_protocol(ik.generic_scpi.SCPIInstrument, ["*RST"], []) as inst:
        inst.reset()


def test_scpi_instrument_clear():
    """Clear the instrument."""
    with expected_protocol(ik.generic_scpi.SCPIInstrument, ["*CLS"], []) as inst:
        inst.clear()


def test_scpi_instrument_trigger():
    """Trigger the instrument."""
    with expected_protocol(ik.generic_scpi.SCPIInstrument, ["*TRG"], []) as inst:
        inst.trigger()


def test_scpi_instrument_wait_to_continue():
    """Wait to continue the instrument."""
    with expected_protocol(ik.generic_scpi.SCPIInstrument, ["*WAI"], []) as inst:
        inst.wait_to_continue()


def test_scpi_instrument_line_frequency():
    """Get / set line frequency."""
    freq_hz = 100
    freq_mhz = u.Quantity(100000, u.mHz)
    with expected_protocol(
        ik.generic_scpi.SCPIInstrument,
        [
            f"SYST:LFR {freq_hz}",
            "SYST:LFR?",
            f"SYST:LFR {freq_mhz.to('Hz').magnitude}",
        ],
        [
            f"{freq_hz}",
        ],
    ) as inst:
        inst.line_frequency = freq_hz
        unit_eq(inst.line_frequency, freq_hz * u.hertz)
        # send a value as mHz
        inst.line_frequency = freq_mhz


def test_scpi_instrument_check_error_queue():
    """Check and clear error queue."""
    ErrorCodes = ik.generic_scpi.SCPIInstrument.ErrorCodes
    err1 = ErrorCodes.no_error  # is skipped
    err2 = ErrorCodes.invalid_separator
    err3 = 13  # invalid error number
    with expected_protocol(
        ik.generic_scpi.SCPIInstrument,
        [f"SYST:ERR:CODE:ALL?"],
        [
            f"{err1.value},{err2.value},{err3}",
        ],
    ) as inst:
        assert inst.check_error_queue() == [err2, err3]


@given(val=st.floats(min_value=0, max_value=1))
def test_scpi_instrument_display_brightness(val):
    """Get / set display brightness."""
    with expected_protocol(
        ik.generic_scpi.SCPIInstrument,
        [f"DISP:BRIG {val}", f"DISP:BRIG?"],
        [
            f"{val}",
        ],
    ) as inst:
        inst.display_brightness = val
        assert inst.display_brightness == val


@given(
    val=st.floats(allow_nan=False, allow_infinity=False).filter(
        lambda x: x < 0 or x > 1
    )
)
def test_scpi_instrument_display_brightness_invalid_value(val):
    """Raise ValueError if display brightness set with invalid value."""
    with expected_protocol(ik.generic_scpi.SCPIInstrument, [], []) as inst:
        with pytest.raises(ValueError) as err_info:
            inst.display_brightness = val
        err_msg = err_info.value.args[0]
        assert err_msg == "Display brightness must be a number between 0 " "and 1."


@given(val=st.floats(min_value=0, max_value=1))
def test_scpi_instrument_display_contrast(val):
    """Get / set display contrast."""
    with expected_protocol(
        ik.generic_scpi.SCPIInstrument,
        [f"DISP:CONT {val}", f"DISP:CONT?"],
        [
            f"{val}",
        ],
    ) as inst:
        inst.display_contrast = val
        assert inst.display_contrast == val


@given(
    val=st.floats(allow_nan=False, allow_infinity=False).filter(
        lambda x: x < 0 or x > 1
    )
)
def test_scpi_instrument_display_contrast_invalid_value(val):
    """Raise ValueError if display contrast set with invalid value."""
    with expected_protocol(ik.generic_scpi.SCPIInstrument, [], []) as inst:
        with pytest.raises(ValueError) as err_info:
            inst.display_contrast = val
        err_msg = err_info.value.args[0]
        assert err_msg == "Display contrast must be a number between 0 " "and 1."
