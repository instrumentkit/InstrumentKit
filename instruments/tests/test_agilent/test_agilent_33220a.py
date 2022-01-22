#!/usr/bin/env python
"""
Module containing tests for generic SCPI function generator instruments
"""

# IMPORTS ####################################################################

from hypothesis import given, strategies as st
import pytest

from instruments.units import ureg as u

import instruments as ik
from instruments.tests import expected_protocol, make_name_test

# TESTS ######################################################################

test_scpi_func_gen_name = make_name_test(ik.agilent.Agilent33220a)


def test_agilent33220a_amplitude():
    with expected_protocol(
        ik.agilent.Agilent33220a,
        [
            "VOLT:UNIT?",
            "VOLT?",
            "VOLT:UNIT VPP",
            "VOLT 2.0",
            "VOLT:UNIT DBM",
            "VOLT 1.5",
        ],
        ["VPP", "+1.000000E+00"],
    ) as fg:
        assert fg.amplitude == (1 * u.V, fg.VoltageMode.peak_to_peak)
        fg.amplitude = 2 * u.V
        fg.amplitude = (1.5 * u.V, fg.VoltageMode.dBm)


def test_agilent33220a_frequency():
    with expected_protocol(
        ik.agilent.Agilent33220a, ["FREQ?", "FREQ 1.005000e+02"], ["+1.234000E+03"]
    ) as fg:
        assert fg.frequency == 1234 * u.Hz
        fg.frequency = 100.5 * u.Hz


def test_agilent33220a_function():
    with expected_protocol(
        ik.agilent.Agilent33220a, ["FUNC?", "FUNC:SQU"], ["SIN"]
    ) as fg:
        assert fg.function == fg.Function.sinusoid
        fg.function = fg.Function.square


def test_agilent33220a_offset():
    with expected_protocol(
        ik.agilent.Agilent33220a,
        ["VOLT:OFFS?", "VOLT:OFFS 4.321000e-01"],
        [
            "+1.234000E+01",
        ],
    ) as fg:
        assert fg.offset == 12.34 * u.V
        fg.offset = 0.4321 * u.V


def test_agilent33220a_duty_cycle():
    with expected_protocol(
        ik.agilent.Agilent33220a,
        ["FUNC:SQU:DCYC?", "FUNC:SQU:DCYC 75"],
        [
            "53",
        ],
    ) as fg:
        assert fg.duty_cycle == 53
        fg.duty_cycle = 75


def test_agilent33220a_ramp_symmetry():
    with expected_protocol(
        ik.agilent.Agilent33220a,
        ["FUNC:RAMP:SYMM?", "FUNC:RAMP:SYMM 75"],
        [
            "53",
        ],
    ) as fg:
        assert fg.ramp_symmetry == 53
        fg.ramp_symmetry = 75


def test_agilent33220a_output():
    with expected_protocol(
        ik.agilent.Agilent33220a,
        ["OUTP?", "OUTP OFF"],
        [
            "ON",
        ],
    ) as fg:
        assert fg.output is True
        fg.output = False


def test_agilent33220a_output_sync():
    with expected_protocol(
        ik.agilent.Agilent33220a,
        ["OUTP:SYNC?", "OUTP:SYNC OFF"],
        [
            "ON",
        ],
    ) as fg:
        assert fg.output_sync is True
        fg.output_sync = False


def test_agilent33220a_output_polarity():
    with expected_protocol(
        ik.agilent.Agilent33220a,
        ["OUTP:POL?", "OUTP:POL NORM"],
        [
            "INV",
        ],
    ) as fg:
        assert fg.output_polarity == fg.OutputPolarity.inverted
        fg.output_polarity = fg.OutputPolarity.normal


def test_agilent33220a_load_resistance():
    with expected_protocol(
        ik.agilent.Agilent33220a,
        ["OUTP:LOAD?", "OUTP:LOAD?", "OUTP:LOAD 100", "OUTP:LOAD MAX"],
        ["50", "INF"],
    ) as fg:
        assert fg.load_resistance == 50 * u.ohm
        assert fg.load_resistance == fg.LoadResistance.high_impedance
        fg.load_resistance = 100 * u.ohm
        fg.load_resistance = fg.LoadResistance.maximum


@given(value=st.floats().filter(lambda x: x < 0 or x > 10000))
def test_agilent33220a_load_resistance_value_invalid(value):
    """Raise ValueError when resistance value loaded is out of range."""
    with expected_protocol(ik.agilent.Agilent33220a, [], []) as fg:
        with pytest.raises(ValueError) as err_info:
            fg.load_resistance = value
        err_msg = err_info.value.args[0]
        assert err_msg == "Load resistance must be between 0 and 10,000"


def test_phase_not_implemented_error():
    """Raise a NotImplementedError when getting / setting the phase."""
    with expected_protocol(ik.agilent.Agilent33220a, [], []) as fg:
        with pytest.raises(NotImplementedError):
            _ = fg.phase()
        with pytest.raises(NotImplementedError):
            fg.phase = 42
