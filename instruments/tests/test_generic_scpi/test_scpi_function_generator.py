#!/usr/bin/env python
"""
Module containing tests for generic SCPI function generator instruments
"""

# IMPORTS ####################################################################

import pytest

from instruments.units import ureg as u

import instruments as ik
from instruments.tests import expected_protocol, make_name_test

# TESTS ######################################################################

test_scpi_func_gen_name = make_name_test(ik.generic_scpi.SCPIFunctionGenerator)


def test_scpi_func_gen_amplitude():
    with expected_protocol(
        ik.generic_scpi.SCPIFunctionGenerator,
        [
            "VOLT:UNIT?",
            "VOLT?",
            "VOLT:UNIT VPP",
            "VOLT 2.0",
            "VOLT:UNIT DBM",
            "VOLT 1.5",
        ],
        ["VPP", "+1.000000E+00"],
        repeat=2,
    ) as fg:
        assert fg.amplitude == (1 * u.V, fg.VoltageMode.peak_to_peak)
        fg.amplitude = 2 * u.V
        fg.amplitude = (1.5 * u.V, fg.VoltageMode.dBm)

        assert fg.channel[0].amplitude == (1 * u.V, fg.VoltageMode.peak_to_peak)
        fg.channel[0].amplitude = 2 * u.V
        fg.channel[0].amplitude = (1.5 * u.V, fg.VoltageMode.dBm)


def test_scpi_func_gen_frequency():
    with expected_protocol(
        ik.generic_scpi.SCPIFunctionGenerator,
        ["FREQ?", "FREQ 1.005000e+02"],
        ["+1.234000E+03"],
        repeat=2,
    ) as fg:
        assert fg.frequency == 1234 * u.Hz
        fg.frequency = 100.5 * u.Hz

        assert fg.channel[0].frequency == 1234 * u.Hz
        fg.channel[0].frequency = 100.5 * u.Hz


def test_scpi_func_gen_function():
    with expected_protocol(
        ik.generic_scpi.SCPIFunctionGenerator, ["FUNC?", "FUNC SQU"], ["SIN"], repeat=2
    ) as fg:
        assert fg.function == fg.Function.sinusoid
        fg.function = fg.Function.square

        assert fg.channel[0].function == fg.Function.sinusoid
        fg.channel[0].function = fg.Function.square


def test_scpi_func_gen_offset():
    with expected_protocol(
        ik.generic_scpi.SCPIFunctionGenerator,
        ["VOLT:OFFS?", "VOLT:OFFS 4.321000e-01"],
        [
            "+1.234000E+01",
        ],
        repeat=2,
    ) as fg:
        assert fg.offset == 12.34 * u.V
        fg.offset = 0.4321 * u.V

        assert fg.channel[0].offset == 12.34 * u.V
        fg.channel[0].offset = 0.4321 * u.V


def test_scpi_func_gen_phase():
    """Raise NotImplementedError when set / get phase."""
    with expected_protocol(
        ik.generic_scpi.SCPIFunctionGenerator,
        [],
        [],
    ) as fg:
        with pytest.raises(NotImplementedError):
            _ = fg.phase
        with pytest.raises(NotImplementedError):
            fg.phase = 42
