#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for the Keithley 6514 electrometer
"""

# IMPORTS #####################################################################

from __future__ import absolute_import

import quantities as pq
from nose.tools import raises

import instruments as ik
from instruments.tests import expected_protocol

# TESTS #######################################################################

# pylint: disable=protected-access


def test_valid_range():
    inst = ik.keithley.Keithley6514.open_test()
    assert inst._valid_range(inst.Mode.voltage) == inst.ValidRange.voltage
    assert inst._valid_range(inst.Mode.current) == inst.ValidRange.current
    assert inst._valid_range(
        inst.Mode.resistance) == inst.ValidRange.resistance
    assert inst._valid_range(inst.Mode.charge) == inst.ValidRange.charge


@raises(ValueError)
def test_valid_range_invalid():
    inst = ik.keithley.Keithley6514.open_test()
    inst._valid_range(inst.TriggerMode.immediate)


def test_parse_measurement():
    with expected_protocol(
        ik.keithley.Keithley6514,
        [
            "FUNCTION?",
        ],
        [
            '"VOLT:DC"'
        ]
    ) as inst:
        reading, timestamp, status = inst._parse_measurement("1.0,1234,5678")
        assert reading == 1.0 * pq.volt
        assert timestamp == 1234
        assert status == 5678


def test_mode():
    with expected_protocol(
        ik.keithley.Keithley6514,
        [
            "FUNCTION?",
            'FUNCTION "VOLT:DC"'
        ],
        [
            '"VOLT:DC"'
        ]
    ) as inst:
        assert inst.mode == inst.Mode.voltage
        inst.mode = inst.Mode.voltage


def test_trigger_source():
    with expected_protocol(
        ik.keithley.Keithley6514,
        [
            "TRIGGER:SOURCE?",
            "TRIGGER:SOURCE IMM"
        ],
        [
            "TLINK"
        ]
    ) as inst:
        assert inst.trigger_mode == inst.TriggerMode.tlink
        inst.trigger_mode = inst.TriggerMode.immediate


def test_arm_source():
    with expected_protocol(
        ik.keithley.Keithley6514,
        [
            "ARM:SOURCE?",
            "ARM:SOURCE IMM"
        ],
        [
            "TIM"
        ]
    ) as inst:
        assert inst.arm_source == inst.ArmSource.timer
        inst.arm_source = inst.ArmSource.immediate


def test_zero_check():
    with expected_protocol(
        ik.keithley.Keithley6514,
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
        ik.keithley.Keithley6514,
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


def test_unit():
    with expected_protocol(
        ik.keithley.Keithley6514,
        [
            "FUNCTION?",
        ],
        [
            '"VOLT:DC"'
        ]
    ) as inst:
        assert inst.unit == pq.volt


def test_auto_range():
    with expected_protocol(
        ik.keithley.Keithley6514,
        [
            "FUNCTION?",
            "VOLT:DC:RANGE:AUTO?",
            "FUNCTION?",
            "VOLT:DC:RANGE:AUTO 1"
        ],
        [
            '"VOLT:DC"',
            "0",
            '"VOLT:DC"'
        ]
    ) as inst:
        assert inst.auto_range is False
        inst.auto_range = True


def test_input_range():
    with expected_protocol(
        ik.keithley.Keithley6514,
        [
            "FUNCTION?",
            "VOLT:DC:RANGE:UPPER?",
            "FUNCTION?",
            "VOLT:DC:RANGE:UPPER {:e}".format(20)
        ],
        [
            '"VOLT:DC"',
            "10",
            '"VOLT:DC"'
        ]
    ) as inst:
        assert inst.input_range == 10 * pq.volt
        inst.input_range = 20 * pq.volt


@raises(ValueError)
def test_input_range_invalid():
    with expected_protocol(
        ik.keithley.Keithley6514,
        [
            "FUNCTION?"
        ],
        [
            '"VOLT:DC"'
        ]
    ) as inst:
        inst.input_range = 10 * pq.volt


def test_auto_config():
    with expected_protocol(
        ik.keithley.Keithley6514,
        [
            "CONF:VOLT:DC",
        ],
        []
    ) as inst:
        inst.auto_config(inst.Mode.voltage)


def test_fetch():
    with expected_protocol(
        ik.keithley.Keithley6514,
        [
            "FETC?",
            "FUNCTION?",
        ],
        [
            "1.0,1234,5678",
            '"VOLT:DC"'
        ]
    ) as inst:
        reading, timestamp = inst.fetch()
        assert reading == 1.0 * pq.volt
        assert timestamp == 1234


def test_read():
    with expected_protocol(
        ik.keithley.Keithley6514,
        [
            "READ?",
            "FUNCTION?",
        ],
        [
            "1.0,1234,5678",
            '"VOLT:DC"'
        ]
    ) as inst:
        reading, timestamp = inst.read_measurements()
        assert reading == 1.0 * pq.volt
        assert timestamp == 1234
