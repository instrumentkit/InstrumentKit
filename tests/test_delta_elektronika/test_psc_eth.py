#!/usr/bin/env python
"""Tests for the Delta Elektronika PSC-ETH interface."""

from hypothesis import given, strategies as st
import pytest

import instruments as ik
from instruments.units import ureg as u
from tests import expected_protocol, make_name_test, unit_eq

# TEST CLASS PROPERTIES #


test_psc_eth_device_name = make_name_test(ik.delta_elektronika.PscEth)


def test_current_limit():
    """Get the current limit of the instrument."""
    with expected_protocol(
        ik.delta_elektronika.PscEth,
        ["SYST:LIM:CUR?", "SYST:LIM:CUR?"],
        ["0.0,OFF", "0.2,ON"],
        sep="\n",
    ) as rf:
        status, value = rf.current_limit
        assert status == ik.delta_elektronika.PscEth.LimitStatus.OFF
        unit_eq(value, 0.0 * u.A)

        status, value = rf.current_limit
        assert status == ik.delta_elektronika.PscEth.LimitStatus.ON
        unit_eq(value, 0.2 * u.A)


def test_voltage_limit():
    """Get the voltage limit of the instrument."""
    with expected_protocol(
        ik.delta_elektronika.PscEth,
        ["SYST:LIM:VOL?", "SYST:LIM:VOL?"],
        ["0.0,OFF", "20.0,ON"],
        sep="\n",
    ) as rf:
        status, value = rf.voltage_limit
        assert status == ik.delta_elektronika.PscEth.LimitStatus.OFF
        unit_eq(value, 0.0 * u.V)

        status, value = rf.voltage_limit
        assert status == ik.delta_elektronika.PscEth.LimitStatus.ON
        unit_eq(value, 20.0 * u.V)


def test_current():
    """Get/set the output current of the instrument."""
    with expected_protocol(
        ik.delta_elektronika.PscEth,
        ["SOUR:CURR?", f"SOUR:CURR {0.1:.15f}", "SOUR:CURR?"],
        ["0.0", "0.1"],
        sep="\n",
    ) as rf:
        unit_eq(rf.current, 0.0 * u.A)
        rf.current = 0.1 * u.A
        unit_eq(rf.current, 0.1 * u.A)


def test_current_max():
    """Get/set the maximum output current of the instrument."""
    with expected_protocol(
        ik.delta_elektronika.PscEth,
        ["SOUR:CURR:MAX?", f"SOUR:CURR:MAX {0.2:.15f}", "SOUR:CURR:MAX?"],
        ["0.1", "0.2"],
        sep="\n",
    ) as rf:
        unit_eq(rf.current_max, 0.1 * u.A)
        rf.current_max = 0.2 * u.A
        unit_eq(rf.current_max, 0.2 * u.A)


def test_current_measure():
    """Get the measured output current of the instrument."""
    with expected_protocol(
        ik.delta_elektronika.PscEth,
        ["MEAS:CURR?", "MEAS:CURR?"],
        ["0.0", "0.1"],
        sep="\n",
    ) as rf:
        unit_eq(rf.current_measure, 0.0 * u.A)
        unit_eq(rf.current_measure, 0.1 * u.A)


def test_current_stepsize():
    """Get the current stepsize of the instrument."""
    with expected_protocol(
        ik.delta_elektronika.PscEth,
        ["SOUR:CUR:STE?", "SOUR:CUR:STE?"],
        ["0.001", "0.01"],
        sep="\n",
    ) as rf:
        unit_eq(rf.current_stepsize, 0.001 * u.A)
        unit_eq(rf.current_stepsize, 0.01 * u.A)


def test_voltage():
    """Get/set the output voltage of the instrument."""
    with expected_protocol(
        ik.delta_elektronika.PscEth,
        ["SOUR:VOL?", f"SOUR:VOL {10.0:.15f}", "SOUR:VOL?"],
        ["0.0", "10.0"],
        sep="\n",
    ) as rf:
        unit_eq(rf.voltage, 0.0 * u.V)
        rf.voltage = 10.0 * u.V
        unit_eq(rf.voltage, 10.0 * u.V)


def test_voltage_max():
    """Get/set the maximum output voltage of the instrument."""
    with expected_protocol(
        ik.delta_elektronika.PscEth,
        ["SOUR:VOLT:MAX?", f"SOUR:VOLT:MAX {20.0:.15f}", "SOUR:VOLT:MAX?"],
        ["10.0", "20.0"],
        sep="\n",
    ) as rf:
        unit_eq(rf.voltage_max, 10.0 * u.V)
        rf.voltage_max = 20.0 * u.V
        unit_eq(rf.voltage_max, 20.0 * u.V)


def test_voltage_measure():
    """Get the measured output voltage of the instrument."""
    with expected_protocol(
        ik.delta_elektronika.PscEth,
        ["MEAS:VOLT?", "MEAS:VOLT?"],
        ["0.0", "10.0"],
        sep="\n",
    ) as rf:
        unit_eq(rf.voltage_measure, 0.0 * u.V)
        unit_eq(rf.voltage_measure, 10.0 * u.V)


def test_voltage_stepsize():
    """Get the voltage stepsize of the instrument."""
    with expected_protocol(
        ik.delta_elektronika.PscEth,
        ["SOUR:VOL:STE?", "SOUR:VOL:STE?"],
        ["0.01", "0.1"],
        sep="\n",
    ) as rf:
        unit_eq(rf.voltage_stepsize, 0.01 * u.V)
        unit_eq(rf.voltage_stepsize, 0.1 * u.V)


# TEST CLASS METHODS #


def test_recall():
    """Recall a stored setting from non-volatile memory."""
    with expected_protocol(
        ik.delta_elektronika.PscEth,
        ["*RCL"],
        [],
        sep="\n",
    ) as rf:
        rf.recall()


def test_reset():
    """Reset the instrument to default settings."""
    with expected_protocol(
        ik.delta_elektronika.PscEth,
        ["*RST"],
        [],
        sep="\n",
    ) as rf:
        rf.reset()


def test_save():
    """Save the current settings to non-volatile memory."""
    with expected_protocol(
        ik.delta_elektronika.PscEth,
        ["*SAV"],
        [],
        sep="\n",
    ) as rf:
        rf.save()


def test_set_current_limit():
    """Set the current limit of the instrument."""
    with expected_protocol(
        ik.delta_elektronika.PscEth,
        [f"SYST:LIM:CUR {0.0:.15f},OFF", f"SYST:LIM:CUR {0.2:.15f},ON"],
        [],
        sep="\n",
    ) as rf:
        rf.set_current_limit(ik.delta_elektronika.PscEth.LimitStatus.OFF)
        rf.set_current_limit(ik.delta_elektronika.PscEth.LimitStatus.ON, 0.2 * u.A)


def test_set_current_limit_invalid_type():
    """Setting current limit with invalid type raises TypeError."""
    with expected_protocol(
        ik.delta_elektronika.PscEth,
        [],
        [],
        sep="\n",
    ) as rf:
        with pytest.raises(TypeError):
            rf.set_current_limit("ON", 0.2 * u.A)


def test_set_voltage_limit():
    """Set the voltage limit of the instrument."""
    with expected_protocol(
        ik.delta_elektronika.PscEth,
        [f"SYST:LIM:VOL {0.0:.15f},OFF", f"SYST:LIM:VOL {20.0:.15f},ON"],
        [],
        sep="\n",
    ) as rf:
        rf.set_voltage_limit(ik.delta_elektronika.PscEth.LimitStatus.OFF)
        rf.set_voltage_limit(ik.delta_elektronika.PscEth.LimitStatus.ON, 20.0 * u.V)


def test_set_voltage_limit_invalid_type():
    """Setting voltage limit with invalid type raises TypeError."""
    with expected_protocol(
        ik.delta_elektronika.PscEth,
        [],
        [],
        sep="\n",
    ) as rf:
        with pytest.raises(TypeError):
            rf.set_voltage_limit("ON", 20.0 * u.V)
