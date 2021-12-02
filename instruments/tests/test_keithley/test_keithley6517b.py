#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for the Keithley 6517b electrometer
"""

# IMPORTS #####################################################################

from __future__ import absolute_import

import quantities as pq
import pytest

import instruments as ik
from instruments.tests import expected_protocol

# TESTS #######################################################################

# pylint: disable=protected-access


def test_parse_measurement():
    with expected_protocol(
        ik.keithley.Keithley6517b,
        [
            "FUNCTION?",
            "CONF:VOLT:DC",
            "FUNCTION?",
        ],
        [
            "\"VOLT:DC\"",
            "\"VOLT:DC\""
        ]
    ) as inst:
        reading, timestamp, status = inst._parse_measurement("1.0N,1234s,5678R00000")
        assert reading == 1.0 * pq.volt
        assert timestamp == 1234
        assert status == 5678


def test_mode():
    with expected_protocol(
        ik.keithley.Keithley6517b,
        [
            "FUNCTION?",
            "CONF:VOLT:DC",
            "FUNCTION?",
            "FUNCTION \"VOLT:DC\""
        ],
        [
            "\"VOLT:DC\"",
            "\"VOLT:DC\""
        ]
    ) as inst:
        assert inst.mode == inst.Mode.voltage_dc
        inst.mode = inst.Mode.voltage_dc


def test_trigger_source():
    with expected_protocol(
        ik.keithley.Keithley6517b,
        [
            "FUNCTION?",
            "CONF:VOLT:DC",
            "TRIGGER:SOURCE?",
            "TRIGGER:SOURCE IMM"
        ],
        [
            "\"VOLT:DC\"",
            "TLINK"
        ]
    ) as inst:
        assert inst.trigger_mode == inst.TriggerMode.tlink
        inst.trigger_mode = inst.TriggerMode.immediate


def test_arm_source():
    with expected_protocol(
        ik.keithley.Keithley6517b,
        [
            "FUNCTION?",
            "CONF:VOLT:DC",
            "ARM:SOURCE?",
            "ARM:SOURCE IMM"
        ],
        [
            "\"VOLT:DC\"",
            "TIM"
        ]
    ) as inst:
        assert inst.arm_source == inst.ArmSource.timer
        inst.arm_source = inst.ArmSource.immediate


def test_zero_check():
    with expected_protocol(
        ik.keithley.Keithley6517b,
        [
            "FUNCTION?",
            "CONF:VOLT:DC",
            "SYST:ZCH?",
            "SYST:ZCH ON"
        ],
        [
            "\"VOLT:DC\"",
            "OFF"
        ]
    ) as inst:
        assert inst.zero_check is False
        inst.zero_check = True


def test_zero_correct():
    with expected_protocol(
        ik.keithley.Keithley6517b,
        [
            "FUNCTION?",
            "CONF:VOLT:DC",
            "SYST:ZCOR?",
            "SYST:ZCOR ON"
        ],
        [
            "\"VOLT:DC\"",
            "OFF"
        ]
    ) as inst:
        assert inst.zero_correct is False
        inst.zero_correct = True


def test_unit():
    with expected_protocol(
        ik.keithley.Keithley6517b,
        [
            "FUNCTION?",
            "CONF:VOLT:DC",
            "FUNCTION?",
        ],
        [
            "\"VOLT:DC\"",
            "\"VOLT:DC\""
        ]
    ) as inst:
        assert inst.unit == pq.volt


def test_auto_range():
    with expected_protocol(
        ik.keithley.Keithley6517b,
        [
            "FUNCTION?",
            "CONF:VOLT:DC",
            "FUNCTION?",
            "VOLT:DC:RANGE:AUTO?",
            "FUNCTION?",
            "VOLT:DC:RANGE:AUTO 1"
        ],
        [
            "\"VOLT:DC\"",
            "\"VOLT:DC\"",
            "0",
            "\"VOLT:DC\""
        ]
    ) as inst:
        assert inst.auto_range is False
        inst.auto_range = True


def test_input_range():
    with expected_protocol(
        ik.keithley.Keithley6517b,
        [
            "FUNCTION?",
            "CONF:VOLT:DC",
            "FUNCTION?",
            "VOLT:DC:RANGE:UPPER?",
            "FUNCTION?",
            "VOLT:DC:RANGE:UPPER {:e}".format(20)
        ],
        [
            "\"VOLT:DC\"",
            "\"VOLT:DC\"",
            "10",
            "\"VOLT:DC\""
        ]
    ) as inst:
        assert inst.input_range == 10 * pq.volt
        inst.input_range = 20 * pq.volt


def test_input_range_invalid():
    with pytest.raises(ValueError):
        with expected_protocol(
            ik.keithley.Keithley6517b,
            [
                "FUNCTION?",
                "CONF:VOLT:DC",
            ],
            [
                "\"VOLT:DC\""
            ]
        ) as inst:
            inst.input_range = 10 * pq.volt


def test_auto_config():
    with expected_protocol(
        ik.keithley.Keithley6517b,
        [
            "FUNCTION?",
            "CONF:VOLT:DC",
            "CONF:VOLT:DC"
        ],
        [
            "\"VOLT:DC\"",
            "\"VOLT:DC\""
        ]
    ) as inst:
        inst.auto_config(inst.Mode.voltage_dc)


def test_fetch():
    with expected_protocol(
        ik.keithley.Keithley6517b,
        [
            "FUNCTION?",
            "CONF:VOLT:DC",
            "FETC?",
            "FUNCTION?",
        ],
        [
            "\"VOLT:DC\"",
            "1.0N,1234s,5678R00000",
            "\"VOLT:DC\""
        ]
    ) as inst:
        reading, timestamp, trigger_count = inst.fetch()
        assert reading == 1.0 * pq.volt
        assert timestamp == 1234
        assert trigger_count == 5678


def test_read():
    with expected_protocol(
        ik.keithley.Keithley6517b,
        [
            "FUNCTION?",
            "CONF:VOLT:DC",
            "READ?",
            "FUNCTION?"
        ],
        [
            "\"VOLT:DC\"",
            "1.0N,1234s,5678R00000",
            "\"VOLT:DC\""
        ]
    ) as inst:
        reading, timestamp, trigger_count = inst.read_measurements()
        assert reading == 1.0 * pq.volt
        assert timestamp == 1234
        assert trigger_count == 5678
