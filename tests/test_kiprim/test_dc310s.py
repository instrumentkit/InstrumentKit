#!/usr/bin/env python
"""
Unit tests for the Kiprim DC310S single-output power supply.
"""

# IMPORTS #####################################################################

import pytest

import instruments as ik
from instruments.units import ureg as u
from tests import expected_protocol, unit_eq

# TESTS #######################################################################


def test_channel():
    with expected_protocol(ik.kiprim.DC310S, [], [], sep="\n") as psu:
        assert psu.channel[0] == psu
        assert len(psu.channel) == 1


def test_name():
    with expected_protocol(
        ik.kiprim.DC310S, ["*IDN?"], ["KIPRIM,DC310S,22371243,FV:V3.7.0"], sep="\n"
    ) as psu:
        assert psu.name == "KIPRIM DC310S"


def test_name_single_field_reply():
    with expected_protocol(ik.kiprim.DC310S, ["*IDN?"], ["DC310S"], sep="\n") as psu:
        assert psu.name == "DC310S"


def test_voltage():
    with expected_protocol(
        ik.kiprim.DC310S, ["VOLT 5.000", "VOLT?"], ["5.000"], sep="\n"
    ) as psu:
        psu.voltage = 5 * u.volt
        unit_eq(psu.voltage, 5 * u.volt)


def test_voltage_bounds():
    with expected_protocol(ik.kiprim.DC310S, [], [], sep="\n") as psu:
        unit_eq(psu.voltage_min, 0 * u.volt)
        unit_eq(psu.voltage_max, 30 * u.volt)
        with pytest.raises(ValueError):
            psu.voltage = 30.001 * u.volt
        with pytest.raises(ValueError):
            psu.voltage = -0.001 * u.volt


def test_current():
    with expected_protocol(
        ik.kiprim.DC310S, ["CURR 0.250", "CURR?"], ["0.250"], sep="\n"
    ) as psu:
        psu.current = 0.25 * u.amp
        unit_eq(psu.current, 0.25 * u.amp)


def test_current_bounds():
    with expected_protocol(ik.kiprim.DC310S, [], [], sep="\n") as psu:
        unit_eq(psu.current_min, 0 * u.amp)
        unit_eq(psu.current_max, 10 * u.amp)
        with pytest.raises(ValueError):
            psu.current = 10.001 * u.amp
        with pytest.raises(ValueError):
            psu.current = -0.001 * u.amp


def test_voltage_sense():
    with expected_protocol(
        ik.kiprim.DC310S, ["MEAS:VOLT?"], ["12.340"], sep="\n"
    ) as psu:
        unit_eq(psu.voltage_sense, 12.34 * u.volt)


def test_current_sense():
    with expected_protocol(
        ik.kiprim.DC310S, ["MEAS:CURR?"], ["0.456"], sep="\n"
    ) as psu:
        unit_eq(psu.current_sense, 0.456 * u.amp)


def test_power_sense():
    with expected_protocol(ik.kiprim.DC310S, ["MEAS:POW?"], ["5.624"], sep="\n") as psu:
        unit_eq(psu.power_sense, 5.624 * u.watt)


def test_output_on():
    with expected_protocol(
        ik.kiprim.DC310S, ["OUTP ON", "OUTP?"], ["ON"], sep="\n"
    ) as psu:
        psu.output = True
        assert psu.output


def test_output_off_numeric_reply():
    with expected_protocol(
        ik.kiprim.DC310S, ["OUTP OFF", "OUTP?"], ["0"], sep="\n"
    ) as psu:
        psu.output = False
        assert psu.output is False


def test_output_invalid_reply():
    with expected_protocol(ik.kiprim.DC310S, ["OUTP?"], ["MAYBE"], sep="\n") as psu:
        with pytest.raises(ValueError):
            _ = psu.output


def test_output_setter_requires_bool():
    with expected_protocol(ik.kiprim.DC310S, [], [], sep="\n") as psu:
        with pytest.raises(TypeError):
            psu.output = 1


def test_mode_getter_unimplemented():
    with expected_protocol(ik.kiprim.DC310S, [], [], sep="\n") as psu:
        with pytest.raises(NotImplementedError):
            _ = psu.mode


def test_mode_setter_unimplemented():
    with expected_protocol(ik.kiprim.DC310S, [], [], sep="\n") as psu:
        with pytest.raises(NotImplementedError):
            psu.mode = "cv"
