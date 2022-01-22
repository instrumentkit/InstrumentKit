#!/usr/bin/env python
"""
Module containing tests for the Gentec-eo Blu
"""

# IMPORTS ####################################################################

from hypothesis import given, strategies as st
import pytest

import instruments as ik
from instruments.tests import expected_protocol
from instruments.units import ureg as u

# TESTS ######################################################################

# pylint: disable=protected-access


# TESTS FOR Blu #


def test_blu_initialization():
    """Initialize the device."""
    with expected_protocol(
        ik.gentec_eo.Blu,
        [],
        [],
        sep="\r\n",
    ) as blu:
        assert blu.terminator == "\r\n"
        assert blu._power_mode is None


# TEST PROPERTIES #


def test_blu_anticipation():
    """Get / Set the instrument into anticipation mode."""
    with expected_protocol(
        ik.gentec_eo.Blu,
        ["*GAN", "*ANT0"],
        ["Anticipation: 1", "ACK"],
        sep="\r\n",
    ) as blu:
        assert blu.anticipation
        blu.anticipation = False


def test_blu_auto_scale():
    """Get / Set the instrument into automatic scaling mode."""
    with expected_protocol(
        ik.gentec_eo.Blu,
        ["*GAS", "*SAS0"],
        ["Autoscale: 1", "ACK"],
        sep="\r\n",
    ) as blu:
        assert blu.auto_scale
        blu.auto_scale = False


def test_blu_available_scales():
    """Get the available scales that are on teh blue device.

    Note that the routine tested here will temporarily overwrite the
    terminator and the timeout. The function here is special in the
    sense that it returns a list of parameters, all individual entries
    are separated by the terminator. There is no clear end to when this
    should be finished. It is assumed that 1 second is enough time to
    send all the data.
    """
    with expected_protocol(
        ik.gentec_eo.Blu,
        ["*DVS"],
        [
            "[22]: 100.0 m\r\n"
            "[23]: 300.0 m\r\n"
            "[24]: 1.000\r\n"
            "[25]: 3.000\r\n"
            "[26]: 10.00\r\n"
            "[27]: 30.00\r\n"
            "[28]: 100.0\r\n"
        ],
        sep="",
    ) as blu:
        ret_scale = [
            blu.Scale.max100milli,
            blu.Scale.max300milli,
            blu.Scale.max1,
            blu.Scale.max3,
            blu.Scale.max10,
            blu.Scale.max30,
            blu.Scale.max100,
        ]
        assert blu.available_scales == ret_scale


def test_blu_available_scales_error():
    """Ensure that temporary variables are reset if read errors.

    Return a `bogus` value, which is not an available scale, and ensure
    that the temporary variables are reset afterwards. This specific
    case raises a ValueError.
    """
    with expected_protocol(
        ik.gentec_eo.Blu,
        ["*DVS"],
        ["bogus"],
        sep="",
    ) as blu:
        _terminator = blu.terminator
        _timeout = blu.timeout
        with pytest.raises(ValueError):
            _ = blu.available_scales
        assert blu.terminator == _terminator
        assert blu.timeout == _timeout


def test_blu_battery_state():
    """Get the battery state of the instrument in percent."""
    with expected_protocol(
        ik.gentec_eo.Blu,
        ["*QSO"],
        ["98"],
        sep="\r\n",
    ) as blu:
        assert blu.battery_state == u.Quantity(98, u.percent)


def test_blu_current_value_watts():
    """Get the current value in Watt mode."""
    with expected_protocol(
        ik.gentec_eo.Blu,
        ["*GMD", "*CVU"],
        ["Mode: 0", "42"],
        sep="\r\n",
    ) as blu:
        assert blu.current_value == u.Quantity(42, u.W)


def test_blu_current_value_joules():
    """Get the current value in Watt mode."""
    with expected_protocol(
        ik.gentec_eo.Blu,
        ["*GMD", "*CVU"],
        ["Mode: 2", "42"],
        sep="\r\n",
    ) as blu:
        assert blu.current_value == u.Quantity(42, u.J)


def test_blu_head_type():
    """Get information on the connected power meter head.

    Here, an example head is returned.
    """
    with expected_protocol(
        ik.gentec_eo.Blu,
        ["*GFW"],
        ["NIG : 104552, Wattmeter, V1.95"],
        sep="\r\n",
    ) as blu:
        example_head = "NIG : 104552, Wattmeter, V1.95"
        assert blu.head_type == example_head


def test_blu_measure_mode():
    """Get the measure mode the head is in.

    This routine is also run when a unitful response is returned from
    another routine and the measurement mode has not been determined
    before.
    """
    with expected_protocol(
        ik.gentec_eo.Blu,
        ["*GMD", "*GMD"],
        ["Mode: 0", "Mode: 2"],
        sep="\r\n",
    ) as blu:
        # power mode
        assert blu.measure_mode == "power"
        assert blu._power_mode

        # single shot energy mode (J)
        assert blu.measure_mode == "sse"
        assert not blu._power_mode


def test_blu_new_value_ready():
    """Query if a new value is ready for reading."""
    with expected_protocol(
        ik.gentec_eo.Blu,
        ["*NVU", "*NVU"],
        ["New Data Not Available", "New Data Available"],
        sep="\r\n",
    ) as blu:
        assert not blu.new_value_ready
        assert blu.new_value_ready


@pytest.mark.parametrize("scale", ik.gentec_eo.Blu.Scale)
def test_blu_scale(scale):
    """Get / set the instrument scale manually."""
    with expected_protocol(
        ik.gentec_eo.Blu,
        [f"*SCS{scale.value}", "*GCR"],
        ["ACK", f"Range: {scale.value}"],
        sep="\r\n",
    ) as blu:
        blu.scale = scale
        assert blu.scale == scale


def test_blu_single_shot_energy_mode():
    """Get / set the single shot energy mode."""
    with expected_protocol(
        ik.gentec_eo.Blu,
        ["*GSE", "*SSE1"],
        ["SSE: 0", "ACK"],
        sep="\r\n",
    ) as blu:
        assert not blu.single_shot_energy_mode
        assert blu._power_mode
        blu.single_shot_energy_mode = True
        assert not blu._power_mode


def test_blu_trigger_level():
    """Get / set the trigger level."""
    with expected_protocol(
        ik.gentec_eo.Blu,
        ["*GTL", "*STL53.4", "*STL01.2", "*STL1.23"],
        [
            "Trigger level: 15.4% (4.6 Watts) of max power: 30 Watts",
            "ACK",
            "ACK",
            "ACK",
        ],
        sep="\r\n",
    ) as blu:
        assert blu.trigger_level == 0.154
        blu.trigger_level = 0.534
        blu.trigger_level = 0.012
        blu.trigger_level = 0.0123


def test_blu_trigger_level_invalid_value():
    """Raise error when trigger level value set is out of bound."""
    with expected_protocol(
        ik.gentec_eo.Blu,
        [],
        [],
        sep="\r\n",
    ) as blu:
        with pytest.raises(ValueError):
            blu.trigger_level = -0.3
        with pytest.raises(ValueError):
            blu.trigger_level = 1.1


def test_blu_usb_state():
    """Get the status if USB cable is plugged in."""
    with expected_protocol(
        ik.gentec_eo.Blu,
        ["*USB"],
        ["USB: 1"],
        sep="\r\n",
    ) as blu:
        assert blu.usb_state


def test_blu_user_multiplier():
    """Get / set user multiplier."""
    with expected_protocol(
        ik.gentec_eo.Blu,
        ["*GUM", "*MUL435.6666"],
        ["User Multiplier: 3.3000000e+01", "ACK"],
        sep="\r\n",
    ) as blu:
        assert blu.user_multiplier == 33.0
        blu.user_multiplier = 435.6666


def test_blu_user_offset_watts():
    """Get / set user offset in watts."""
    with expected_protocol(
        ik.gentec_eo.Blu,
        ["*GMD", "*GUO", "*OFF000042.0"],  # get power mode
        ["Mode: 0", "User Offset : 1.500e-3", "ACK"],  # power mode watts
        sep="\r\n",
    ) as blu:
        assert blu.user_offset == u.Quantity(1.5, u.mW)
        blu.user_offset = u.Quantity(42.0, u.W)


def test_blu_user_offset_joules():
    """Get / set user offset in joules."""
    with expected_protocol(
        ik.gentec_eo.Blu,
        ["*GMD", "*GUO", "*OFF000042.0"],  # get power mode
        ["Mode: 2", "User Offset : 1.500e-3", "ACK"],  # power mode joules
        sep="\r\n",
    ) as blu:
        assert blu.user_offset == u.Quantity(0.0015, u.J)
        blu.user_offset = u.Quantity(42.0, u.J)


def test_blu_user_offset_unitless():
    """Set user offset unitless."""
    with expected_protocol(
        ik.gentec_eo.Blu,
        ["*OFF000042.0"],
        ["ACK"],
        sep="\r\n",
    ) as blu:
        blu.user_offset = 42.0


def test_blu_user_offset_unit_error():
    """Raise ValueError if unit is invalid."""
    with expected_protocol(
        ik.gentec_eo.Blu,
        [],
        [],
        sep="\r\n",
    ) as blu:
        with pytest.raises(ValueError):
            blu.user_offset = u.Quantity(42, u.mm)


def test_blu_version():
    """Query version of device."""
    with expected_protocol(
        ik.gentec_eo.Blu,
        ["*VER"],
        ["Blu firmware Version 1.95"],
        sep="\r\n",
    ) as blu:
        version = "Blu firmware Version 1.95"
        assert blu.version == version


def test_blu_wavelength():
    """Get / set the wavelength."""
    with expected_protocol(
        ik.gentec_eo.Blu,
        ["*GWL", "*PWC00527", "*PWC00527"],
        ["PWC: 1064", "ACK", "ACK"],
        sep="\r\n",
    ) as blu:
        assert blu.wavelength == u.Quantity(1064, u.nm)
        blu.wavelength = u.Quantity(0.527, u.um)
        blu.wavelength = 527


def test_blu_wavelength_out_of_bound():
    """Get / set the wavelength when value is out of bound."""
    with expected_protocol(
        ik.gentec_eo.Blu,
        ["*PWC00000", "*PWC00000"],
        ["ACK", "ACK"],
        sep="\r\n",
    ) as blu:
        blu.wavelength = u.Quantity(1000, u.um)
        blu.wavelength = -3


def test_blu_zero_offset():
    """Get / set the zero offset."""
    with expected_protocol(
        ik.gentec_eo.Blu,
        ["*GZO", "*SOU", "*COU"],
        ["Zero: 1", "ACK", "ACK"],
        sep="\r\n",
    ) as blu:
        assert blu.zero_offset
        blu.zero_offset = True
        blu.zero_offset = False


# TEST METHODS #


def test_blu_confirm_connection():
    """Confirm a bluetooth connection."""
    with expected_protocol(
        ik.gentec_eo.Blu,
        ["*RDY"],
        ["ACK"],
        sep="\r\n",
    ) as blu:
        blu.confirm_connection()


def test_blu_disconnect():
    """Disconnect bluetooth connection."""
    with expected_protocol(
        ik.gentec_eo.Blu,
        ["*BTD"],
        ["ACK"],
        sep="\r\n",
    ) as blu:
        blu.disconnect()


def test_blu_scale_down():
    """Set the scale one level lower."""
    with expected_protocol(
        ik.gentec_eo.Blu,
        ["*SSD"],
        ["ACK"],
        sep="\r\n",
    ) as blu:
        blu.scale_down()


def test_blu_scale_up():
    """Set the scale one level higher."""
    with expected_protocol(
        ik.gentec_eo.Blu,
        ["*SSU"],
        ["ACK"],
        sep="\r\n",
    ) as blu:
        blu.scale_up()


def test_no_ack_query_error(mocker):
    """Ensure temporary variables reset if `_no_ack_query` errors.

    Mocking query here in order to raise an error on query.
    """
    with expected_protocol(
        ik.gentec_eo.Blu,
        [],
        [],
        sep="\r\n",
    ) as blu:
        # mock query w/ IOError
        io_error_mock = mocker.Mock()
        io_error_mock.side_effect = IOError
        mocker.patch.object(blu, "query", io_error_mock)
        # do the query
        with pytest.raises(IOError):
            _ = blu._no_ack_query("QUERY")
        assert blu._ack_message == "ACK"


# NON-Blu ROUTINES #


def test_format_eight_type():
    """Ensure type returned is string."""
    assert isinstance(ik.gentec_eo.blu._format_eight(3.0), str)


@given(
    value=st.floats(
        min_value=-1e100, max_value=1e100, exclude_min=True, exclude_max=True
    )
)
def test_format_eight_length_values(value):
    """Ensure format eight routine works.

    This is a helper routine for the blu device to cut any number to
    eight characters. Make sure this is the case with various numbers
    and that it is correct to 1% with given number.
    """
    value_read = ik.gentec_eo.blu._format_eight(value)
    assert value == pytest.approx(float(value_read), abs(value) / 100.0)
    assert len(value_read) == 8
