#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for the Keithley 6485 picoammeter
"""

# IMPORTS #####################################################################


import pytest

import instruments as ik
from instruments.tests import expected_protocol
from instruments.units import ureg as u

# TESTS #######################################################################

# pylint: disable=protected-access


init_sequence = [
    "*RST",
    "SYST:ZCH OFF"
]


def test_parse_measurement():
    with expected_protocol(
            ik.keithley.Keithley6485,
            init_sequence,
            []
    ) as inst:
        reading, timestamp, trigger_count = inst._parse_measurement("1.234E-3A,567,89")
        assert reading == 1.234 * u.milliamp
        assert timestamp == 567 * u.second
        assert trigger_count == 89


def test_zero_check():
    with expected_protocol(
            ik.keithley.Keithley6485,
            init_sequence+
            [
                "SYST:ZCH?",
                "SYST:ZCH ON"
            ],
            [
                "OFF"
            ]
    ) as inst:
        assert inst.zero_check is False
        inst.zero_check = True


def test_zero_correct():
    with expected_protocol(
            ik.keithley.Keithley6485,
            init_sequence+
            [
                "SYST:ZCOR?",
                "SYST:ZCOR ON"
            ],
            [
                "OFF"
            ]
    ) as inst:
        assert inst.zero_correct is False
        inst.zero_correct = True


def test_auto_range():
    with expected_protocol(
            ik.keithley.Keithley6485,
            init_sequence+
            [
                "RANG:AUTO?",
                "RANG:AUTO 1"
            ],
            [
                "0"
            ]
    ) as inst:
        assert inst.auto_range is False
        inst.auto_range = True


def test_input_range():
    with expected_protocol(
            ik.keithley.Keithley6485,
            init_sequence+
            [
                "RANG?",
                "RANG {:e}".format(2e-3)
            ],
            [
                "0.002"
            ]
    ) as inst:
        assert inst.input_range == 2 * u.milliamp
        inst.input_range = 2 * u.milliamp


def test_input_range_invalid():
    with pytest.raises(ValueError):
        with expected_protocol(
                ik.keithley.Keithley6485,
                init_sequence+
                [
                    "RANG {:e}".format(10)
                ],
                []
        ) as inst:
            inst.input_range = 10 * u.amp


def test_fetch():
    with expected_protocol(
            ik.keithley.Keithley6485,
            init_sequence+
            [
                "FETC?"
            ],
            [
                "1.234E-3A,567,89"
            ]
    ) as inst:
        reading, timestamp, trigger_count = inst.fetch()
        assert reading == 1.234 * u.milliamp
        assert timestamp == 567 * u.second
        assert trigger_count == 89


def test_read():
    with expected_protocol(
            ik.keithley.Keithley6485,
            init_sequence+
            [
                "READ?"
            ],
            [
                "1.234E-3A,567,89"
            ]
    ) as inst:
        reading, timestamp, trigger_count = inst.read_measurements()
        assert reading == 1.234 * u.milliamp
        assert timestamp == 567 * u.second
        assert trigger_count == 89
