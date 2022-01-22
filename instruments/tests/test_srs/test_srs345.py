#!/usr/bin/env python
"""
Unit tests for the SRS 345 function generator
"""

# IMPORTS #####################################################################


import instruments as ik
from instruments.tests import (
    expected_protocol,
    iterable_eq,
)
from instruments.units import ureg as u

# TESTS #######################################################################


def test_amplitude():
    with expected_protocol(
        ik.srs.SRS345,
        ["AMPL?", "AMPL 0.1VP", "AMPL 0.1VR"],
        [
            "1.234VP",
        ],
    ) as inst:
        iterable_eq(inst.amplitude, (1.234 * u.V, inst.VoltageMode.peak_to_peak))
        inst.amplitude = 0.1 * u.V
        inst.amplitude = (0.1 * u.V, inst.VoltageMode.rms)


def test_frequency():
    with expected_protocol(
        ik.srs.SRS345,
        [
            "FREQ?",
            f"FREQ {0.1:e}",
        ],
        [
            "1.234",
        ],
    ) as inst:
        assert inst.frequency == 1.234 * u.Hz
        inst.frequency = 0.1 * u.Hz


def test_function():
    with expected_protocol(
        ik.srs.SRS345,
        ["FUNC?", "FUNC 0"],
        [
            "1",
        ],
    ) as inst:
        assert inst.function == inst.Function.square
        inst.function = inst.Function.sinusoid


def test_offset():
    with expected_protocol(
        ik.srs.SRS345,
        [
            "OFFS?",
            f"OFFS {0.1:e}",
        ],
        [
            "1.234",
        ],
    ) as inst:
        assert inst.offset == 1.234 * u.V
        inst.offset = 0.1 * u.V


def test_phase():
    with expected_protocol(
        ik.srs.SRS345,
        [
            "PHSE?",
            f"PHSE {0.1:e}",
        ],
        [
            "1.234",
        ],
    ) as inst:
        assert inst.phase == 1.234 * u.degree
        inst.phase = 0.1 * u.degree
