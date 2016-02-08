#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for the Keithley 2182 nano-voltmeter
"""

# IMPORTS #####################################################################

from __future__ import absolute_import

import quantities as pq
import numpy as np
from nose.tools import raises

import instruments as ik
from instruments.tests import expected_protocol, make_name_test, unit_eq

# TESTS #######################################################################


def test_channel():
    inst = ik.keithley.Keithley2182.open_test()
    assert isinstance(inst.channel[0], inst.Channel) is True


def test_channel_mode():
    with expected_protocol(
        ik.keithley.Keithley2182,
        [
            "SENS:FUNC?",
        ],
        [
            "VOLT",
        ]
    ) as inst:
        channel = inst.channel[0]
        assert channel.mode == inst.Mode.voltage_dc

def test_channel_measure_voltage():
    with expected_protocol(
        ik.keithley.Keithley2182,
        [
            "SENS:CHAN 1",
            "SENS:DATA:FRES?",
            "SENS:FUNC?"
        ],
        [
            "1.234",
            "VOLT",
        ]
    ) as inst:
        channel = inst.channel[0]
        assert channel.measure() == 1.234 * pq.volt


def test_channel_measure_temperature():
    with expected_protocol(
        ik.keithley.Keithley2182,
        [
            "SENS:CHAN 1",
            "SENS:DATA:FRES?",
            "SENS:FUNC?",
            "UNIT:TEMP?"
        ],
        [
            "1.234",
            "TEMP",
            "C"
        ]
    ) as inst:
        channel = inst.channel[0]
        assert channel.measure() == 1.234 * pq.celsius


@raises(ValueError)
def test_channel_measure_unknown_temperature_units():
    with expected_protocol(
        ik.keithley.Keithley2182,
        [
            "SENS:CHAN 1",
            "SENS:DATA:FRES?",
            "SENS:FUNC?",
            "UNIT:TEMP?"
        ],
        [
            "1.234",
            "TEMP",
            "Z"
        ]
    ) as inst:
        inst.channel[0].measure()


def test_units():
    with expected_protocol(
        ik.keithley.Keithley2182,
        [
            "SENS:FUNC?",
            "UNIT:TEMP?",

            "SENS:FUNC?",
            "UNIT:TEMP?",

            "SENS:FUNC?",
            "UNIT:TEMP?",

            "SENS:FUNC?"
        ],
        [
            "TEMP",
            "C",

            "TEMP",
            "F",

            "TEMP",
            "K",

            "VOLT"
        ]
    ) as inst:
        units = str(inst.units.units).split()[1]
        assert units == "degC"

        units = str(inst.units.units).split()[1]
        assert units == "degF"

        units = str(inst.units.units).split()[1]
        assert units == "K"

        assert inst.units == pq.volt


def test_fetch():
    with expected_protocol(
        ik.keithley.Keithley2182,
        [
            "FETC?",
            "SENS:FUNC?"
        ],
        [
            "1.234,1,5.678",
            "VOLT",
        ]
    ) as inst:
        np.testing.assert_array_equal(
            inst.fetch(), [1.234, 1, 5.678] * pq.volt
        )


def test_measure():
    with expected_protocol(
        ik.keithley.Keithley2182,
        [
            "SENS:FUNC?",
            "MEAS:VOLT?",
            "SENS:FUNC?",
        ],
        [
            "VOLT",
            "1.234",
            "VOLT"
        ]
    ) as inst:
        assert inst.measure() == 1.234 * pq.volt
