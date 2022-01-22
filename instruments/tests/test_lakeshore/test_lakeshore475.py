#!/usr/bin/env python
"""
Module containing tests for the Lakeshore 475 Gaussmeter
"""

# IMPORTS ####################################################################

import pytest

import instruments as ik
from instruments.units import ureg as u
from instruments.tests import expected_protocol

# TESTS ######################################################################


# TEST LAKESHORE475 CLASS PROPERTIES #


def test_lakeshore475_field():
    """
    Get field from connected probe unitful.
    """
    with expected_protocol(
        ik.lakeshore.Lakeshore475,
        ["RDGFIELD?", "UNIT?"],
        ["200.", "2"],
    ) as lsh:
        assert lsh.field == u.Quantity(200.0, u.tesla)


def test_lakeshore475_field_units():
    """
    Get / set field unit on device.
    """
    with expected_protocol(
        ik.lakeshore.Lakeshore475,
        ["UNIT?", "UNIT 2"],
        ["3"],
    ) as lsh:
        assert lsh.field_units == u.oersted
        lsh.field_units = u.tesla


def test_lakeshore475_field_units_invalid_unit():
    """
    Raise a ValueError if an invalid unit is given.
    """
    with expected_protocol(
        ik.lakeshore.Lakeshore475,
        [],
        [],
    ) as lsh:
        with pytest.raises(ValueError) as exc_info:
            lsh.field_units = u.m
        exc_msg = exc_info.value.args[0]
        assert exc_msg == "Not an acceptable Python quantities object"


def test_lakeshore475_field_units_not_a_unit():
    """
    Raise a ValueError if something else than a quantity is given.
    """
    with expected_protocol(
        ik.lakeshore.Lakeshore475,
        [],
        [],
    ) as lsh:
        with pytest.raises(TypeError) as exc_info:
            lsh.field_units = 42
        exc_msg = exc_info.value.args[0]
        assert exc_msg == "Field units must be a Python quantity"


def test_lakeshore475_temp_units():
    """
    Get / set temperature unit on device.
    """
    with expected_protocol(
        ik.lakeshore.Lakeshore475,
        ["TUNIT?", "TUNIT 2"],
        ["1"],
    ) as lsh:
        assert lsh.temp_units == u.celsius
        lsh.temp_units = u.kelvin


def test_lakeshore475_temp_units_invalid_unit():
    """
    Raise a ValueError if an invalid unit is given.
    """
    with expected_protocol(
        ik.lakeshore.Lakeshore475,
        [],
        [],
    ) as lsh:
        with pytest.raises(TypeError) as exc_info:
            lsh.temp_units = u.fahrenheit
        exc_msg = exc_info.value.args[0]
        assert exc_msg == "Not an acceptable Python quantities object"


def test_lakeshore475_temp_units_not_a_unit():
    """
    Raise a ValueError if something else than a quantity is given.
    """
    with expected_protocol(
        ik.lakeshore.Lakeshore475,
        [],
        [],
    ) as lsh:
        with pytest.raises(TypeError) as exc_info:
            lsh.temp_units = 42
        exc_msg = exc_info.value.args[0]
        assert exc_msg == "Temperature units must be a Python quantity"


def test_lakeshore475_field_setpoint():
    """
    Get / set field set point.
    """
    with expected_protocol(
        ik.lakeshore.Lakeshore475,
        [
            "CSETP?",
            "UNIT?",
            "UNIT?",
            "CSETP 1.0",  # send 1 tesla
            "UNIT?",
            "CSETP 23.0",  # send 23 unitless (equals gauss)
        ],
        ["10.", "1", "2", "1"],
    ) as lsh:
        assert lsh.field_setpoint == u.Quantity(10, u.gauss)

        lsh.field_setpoint = u.Quantity(1.0, u.tesla)
        lsh.field_setpoint = 23.0


def test_lakeshore475_field_setpoint_wrong_units():
    """
    Setting the field setpoint with the wrong units
    """
    with expected_protocol(
        ik.lakeshore.Lakeshore475,
        [
            "UNIT?",
        ],
        ["1"],
    ) as lsh:
        with pytest.raises(ValueError) as exc_info:
            lsh.field_setpoint = u.Quantity(1.0, u.tesla)
        exc_msg = exc_info.value.args[0]
        assert "Field setpoint must be specified in the same units" in exc_msg


def test_lakeshore475_field_get_control_params():
    """
    Get field control parameters.
    """
    with expected_protocol(
        ik.lakeshore.Lakeshore475,
        ["CPARAM?", "UNIT?"],
        ["+1.0E+0,+1.0E+1,+4.2E+1,+1.0E+2", "2"],  # teslas
    ) as lsh:
        current_params = lsh.field_control_params
        assert current_params == (
            1.0,
            10.0,
            u.Quantity(42.0, u.tesla / u.min),
            u.Quantity(100.0, u.volt / u.min),
        )


def test_lakeshore475_field_set_control_params():
    """
    Set field control parameters, unitful and using assumed units.
    """
    with expected_protocol(
        ik.lakeshore.Lakeshore475,
        ["UNIT?", "CPARAM 5.0,50.0,120.0,60.0", "UNIT?", "CPARAM 5.0,50.0,120.0,60.0"],
        ["2", "2"],  # teslas  # teslas
    ) as lsh:
        # currently set units are used
        lsh.field_control_params = (
            5.0,
            50.0,
            u.Quantity(120.0, u.tesla / u.min),
            u.Quantity(60.0, u.volt / u.min),
        )
        # no units are used
        lsh.field_control_params = (5.0, 50.0, 120.0, 60.0)


def test_lakeshore475_field_set_control_params_not_a_tuple():
    """
    Set field control parameters with wrong type.
    """
    with expected_protocol(
        ik.lakeshore.Lakeshore475,
        [],
        [],
    ) as lsh:
        with pytest.raises(TypeError) as exc_info:
            lsh.field_control_params = 42
        exc_msg = exc_info.value.args[0]
        assert exc_msg == "Field control parameters must be specified as " " a tuple"


def test_lakeshore475_field_set_control_params_wrong_units():
    """
    Set field control parameters with the wrong units
    """
    with expected_protocol(
        ik.lakeshore.Lakeshore475,
        [
            "UNIT?",
        ],
        [
            "1",  # gauss
        ],
    ) as lsh:
        with pytest.raises(ValueError) as exc_info:
            lsh.field_control_params = (
                5.0,
                50.0,
                u.Quantity(120.0, u.tesla / u.min),
                u.Quantity(60.0, u.volt / u.min),
            )
        exc_msg = exc_info.value.args[0]
        assert (
            "Field control params ramp rate must be specified in the same units"
            in exc_msg
        )


def test_lakeshore475_p_value():
    """
    Get / set p-value.
    """
    with expected_protocol(
        ik.lakeshore.Lakeshore475,
        [
            "CPARAM?",
            "UNIT?",
            "CPARAM?",
            "UNIT?",
            "UNIT?",
            "CPARAM 5.0,10.0,42.0,100.0",
        ],
        [
            "+1.0E+0,+1.0E+1,+4.2E+1,+1.0E+2",
            "2",  # teslas
            "+1.0E+0,+1.0E+1,+4.2E+1,+1.0E+2",
            "2",  # teslas
            "2",
        ],
    ) as lsh:
        assert lsh.p_value == 1.0
        lsh.p_value = 5.0


def test_lakeshore475_i_value():
    """
    Get / set i-value.
    """
    with expected_protocol(
        ik.lakeshore.Lakeshore475,
        [
            "CPARAM?",
            "UNIT?",
            "CPARAM?",
            "UNIT?",
            "UNIT?",
            "CPARAM 1.0,5.0,42.0,100.0",
        ],
        [
            "+1.0E+0,+1.0E+1,+4.2E+1,+1.0E+2",
            "2",  # teslas
            "+1.0E+0,+1.0E+1,+4.2E+1,+1.0E+2",
            "2",  # teslas
            "2",
        ],
    ) as lsh:
        assert lsh.i_value == 10.0
        lsh.i_value = 5.0


def test_lakeshore475_ramp_rate():
    """
    Get / set ramp rate, unitful and not.
    """
    with expected_protocol(
        ik.lakeshore.Lakeshore475,
        [
            "CPARAM?",
            "UNIT?",
            "UNIT?",
            "CPARAM?",
            "UNIT?",
            "UNIT?",
            "CPARAM 1.0,10.0,420.0,100.0",
            "UNIT?",
            "CPARAM?",
            "UNIT?",
            "UNIT?",
            "CPARAM 1.0,10.0,420.0,100.0",
        ],
        [
            "+1.0E+0,+1.0E+1,+4.2E+1,+1.0E+2",
            "2",  # teslas
            "2",
            "+1.0E+0,+1.0E+1,+4.2E+1,+1.0E+2",
            "2",  # teslas
            "2",
            "2",
            "+1.0E+0,+1.0E+1,+4.2E+1,+1.0E+2",
            "2",
            "2",
        ],
    ) as lsh:
        assert lsh.ramp_rate == u.Quantity(42.0, u.tesla / u.min)
        lsh.ramp_rate = u.Quantity(420.0, u.tesla / u.min)
        lsh.ramp_rate = 420.0


def test_lakeshore475_control_slope_limit():
    """
    Get / set slope limit, unitful and not.
    """
    with expected_protocol(
        ik.lakeshore.Lakeshore475,
        [
            "CPARAM?",
            "UNIT?",
            "CPARAM?",
            "UNIT?",
            "UNIT?",
            "CPARAM 1.0,10.0,42.0,42.0",
            "CPARAM?",
            "UNIT?",
            "UNIT?",
            "CPARAM 1.0,10.0,42.0,42.0",
        ],
        [
            "+1.0E+0,+1.0E+1,+4.2E+1,+1.0E+2",
            "2",  # teslas
            "+1.0E+0,+1.0E+1,+4.2E+1,+1.0E+2",
            "2",  # teslas
            "2",
            "+1.0E+0,+1.0E+1,+4.2E+1,+1.0E+2",
            "2",
            "2",
        ],
    ) as lsh:
        assert lsh.control_slope_limit == u.Quantity(100.0, u.V / u.min)
        lsh.control_slope_limit = u.Quantity(42000.0, u.mV / u.min)
        lsh.control_slope_limit = 42.0


def test_lakeshore475_control_mode():
    """
    Get / set control mode.
    """
    with expected_protocol(
        ik.lakeshore.Lakeshore475,
        ["CMODE?", "CMODE 1"],
        ["0"],
    ) as lsh:
        assert not lsh.control_mode
        lsh.control_mode = True


# TEST LAKESHORE475 CLASS METHODS #


def test_lakeshore475_change_measurement_mode():
    """
    Change the measurement mode with valid values and ensure properly
    sent to device.
    """
    with expected_protocol(
        ik.lakeshore.Lakeshore475,
        ["RDGMODE 1,2,3,2,1"],
        [],
    ) as lsh:
        # parameters to send
        mode = lsh.Mode.dc
        resolution = 4
        filter_type = lsh.Filter.lowpass
        peak_mode = lsh.PeakMode.pulse
        peak_disp = lsh.PeakDisplay.positive
        # send them
        lsh.change_measurement_mode(mode, resolution, filter_type, peak_mode, peak_disp)


def test_lakeshore475_change_measurement_mode_mismatched_type():
    """
    Ensure that mismatched input type raises a TypeError.
    """
    with expected_protocol(
        ik.lakeshore.Lakeshore475,
        [],
        [],
    ) as lsh:
        # parameters to send
        mode = lsh.Mode.dc
        resolution = 4
        filter_type = lsh.Filter.lowpass
        peak_mode = lsh.PeakMode.pulse
        peak_disp = lsh.PeakDisplay.positive
        # check mode
        with pytest.raises(TypeError) as exc_info:
            lsh.change_measurement_mode(
                42, resolution, filter_type, peak_mode, peak_disp
            )
        exc_msg = exc_info.value.args[0]
        assert (
            exc_msg == f"Mode setting must be a `Lakeshore475.Mode` "
            f"value, got {type(42)} instead."
        )
        # check resolution
        with pytest.raises(TypeError) as exc_info:
            lsh.change_measurement_mode(mode, 3.14, filter_type, peak_mode, peak_disp)
        exc_msg = exc_info.value.args[0]
        assert exc_msg == 'Parameter "resolution" must be an integer.'
        # check filter_type
        with pytest.raises(TypeError) as exc_info:
            lsh.change_measurement_mode(mode, resolution, 42, peak_mode, peak_disp)
        exc_msg = exc_info.value.args[0]
        assert (
            exc_msg == f"Filter type setting must be a "
            f"`Lakeshore475.Filter` value, "
            f"got {type(42)} instead."
        )
        # check peak_mode
        with pytest.raises(TypeError) as exc_info:
            lsh.change_measurement_mode(mode, resolution, filter_type, 42, peak_disp)
        exc_msg = exc_info.value.args[0]
        assert (
            exc_msg == f"Peak measurement type setting must be a "
            f"`Lakeshore475.PeakMode` value, "
            f"got {type(42)} instead."
        )
        # check peak_display
        with pytest.raises(TypeError) as exc_info:
            lsh.change_measurement_mode(mode, resolution, filter_type, peak_mode, 42)
        exc_msg = exc_info.value.args[0]
        assert (
            exc_msg == f"Peak display type setting must be a "
            f"`Lakeshore475.PeakDisplay` value, "
            f"got {type(42)} instead."
        )


def test_lakeshore475_change_measurement_mode_invalid_resolution():
    """
    Ensure that mismatched input type raises a TypeError.
    """
    with expected_protocol(
        ik.lakeshore.Lakeshore475,
        [],
        [],
    ) as lsh:
        # parameters to send
        mode = lsh.Mode.dc
        filter_type = lsh.Filter.lowpass
        peak_mode = lsh.PeakMode.pulse
        peak_disp = lsh.PeakDisplay.positive
        # check resolution too low
        with pytest.raises(ValueError) as exc_info:
            lsh.change_measurement_mode(mode, 2, filter_type, peak_mode, peak_disp)
        exc_msg = exc_info.value.args[0]
        assert exc_msg == "Only 3,4,5 are valid resolutions."
        # check resolution too high
        with pytest.raises(ValueError) as exc_info:
            lsh.change_measurement_mode(mode, 6, filter_type, peak_mode, peak_disp)
        exc_msg = exc_info.value.args[0]
        assert exc_msg == "Only 3,4,5 are valid resolutions."
