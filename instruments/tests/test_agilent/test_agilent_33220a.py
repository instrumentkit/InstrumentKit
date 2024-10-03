#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing tests for generic SCPI function generator instruments
"""

# IMPORTS ####################################################################

from __future__ import absolute_import

import quantities as pq

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
            "VOLT 1.5"
        ], [
            "VPP",
            "+1.000000E+00"
        ]
    ) as fg:
        assert fg.amplitude == (1 * pq.V, fg.VoltageMode.peak_to_peak)
        fg.amplitude = 2 * pq.V
        fg.amplitude = (1.5 * pq.V, fg.VoltageMode.dBm)


def test_agilent33220a_frequency():
    with expected_protocol(
        ik.agilent.Agilent33220a,
        [
            "FREQ?",
            "FREQ 1.005000e+02"
        ], [
            "+1.234000E+03"
        ]
    ) as fg:
        assert fg.frequency == 1234 * pq.Hz
        fg.frequency = 100.5 * pq.Hz


def test_agilent33220a_function():
    with expected_protocol(
        ik.agilent.Agilent33220a,
        [
            "FUNC?",
            "FUNC:SQU"
        ], [
            "SIN"
        ]
    ) as fg:
        assert fg.function == fg.Function.sinusoid
        fg.function = fg.Function.square


def test_agilent33220a_offset():
    with expected_protocol(
        ik.agilent.Agilent33220a,
        [
            "VOLT:OFFS?",
            "VOLT:OFFS 4.321000e-01"
        ], [
            "+1.234000E+01",
        ]
    ) as fg:
        assert fg.offset == 12.34 * pq.V
        fg.offset = 0.4321 * pq.V


def test_agilent33220a_duty_cycle():
    with expected_protocol(
        ik.agilent.Agilent33220a,
        [
            "FUNC:SQU:DCYC?",
            "FUNC:SQU:DCYC 75"
        ], [
            "53",
        ]
    ) as fg:
        assert fg.duty_cycle == 53
        fg.duty_cycle = 75


def test_agilent33220a_ramp_symmetry():
    with expected_protocol(
        ik.agilent.Agilent33220a,
        [
            "FUNC:RAMP:SYMM?",
            "FUNC:RAMP:SYMM 75"
        ], [
            "53",
        ]
    ) as fg:
        assert fg.ramp_symmetry == 53
        fg.ramp_symmetry = 75


def test_agilent33220a_output():
    with expected_protocol(
        ik.agilent.Agilent33220a,
        [
            "OUTP?",
            "OUTP OFF"
        ], [
            "ON",
        ]
    ) as fg:
        assert fg.output is True
        fg.output = False


def test_agilent33220a_output_sync():
    with expected_protocol(
        ik.agilent.Agilent33220a,
        [
            "OUTP:SYNC?",
            "OUTP:SYNC OFF"
        ], [
            "ON",
        ]
    ) as fg:
        assert fg.output_sync is True
        fg.output_sync = False


def test_agilent33220a_output_polarity():
    with expected_protocol(
        ik.agilent.Agilent33220a,
        [
            "OUTP:POL?",
            "OUTP:POL NORM"
        ], [
            "INV",
        ]
    ) as fg:
        assert fg.output_polarity == fg.OutputPolarity.inverted
        fg.output_polarity = fg.OutputPolarity.normal


def test_agilent33220a_load_resistance():
    with expected_protocol(
        ik.agilent.Agilent33220a,
        [
            "OUTP:LOAD?",
            "OUTP:LOAD?",
            "OUTP:LOAD 100.0",
            "OUTP:LOAD MAX"
        ], [
            "50",
            "INF"
        ]
    ) as fg:
        assert fg.load_resistance == 50 * pq.Ohm
        assert fg.load_resistance == fg.LoadResistance.high_impedance
        fg.load_resistance = 100 * pq.Ohm
        fg.load_resistance = fg.LoadResistance.maximum
