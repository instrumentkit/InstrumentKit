#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for the Keithley 2182 nano-voltmeter
"""

# IMPORTS #####################################################################


import pytest

import instruments as ik
from instruments.tests import (
    expected_protocol,
    iterable_eq,
)
from instruments.units import ureg as u

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
        assert channel.measure() == 1.234 * u.volt


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
        assert channel.measure() == u.Quantity(1.234, u.degC)


def test_channel_measure_unknown_temperature_units():
    with pytest.raises(ValueError), expected_protocol(
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
        assert inst.units == u.degC
        assert inst.units == u.degF
        assert inst.units == u.kelvin
        assert inst.units == u.volt


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
        data = inst.fetch()
        iterable_eq(data, [1.234, 1, 5.678] * u.volt)


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
        assert inst.measure() == 1.234 * u.volt


def test_measure_invalid_mode():
    with pytest.raises(TypeError), expected_protocol(
            ik.keithley.Keithley2182,
            [],
            []
    ) as inst:
        inst.measure("derp")


def test_relative_get():
    with expected_protocol(
            ik.keithley.Keithley2182,
            [
                "SENS:FUNC?",
                "SENS:VOLT:CHAN1:REF:STAT?"
            ],
            [
                "VOLT",
                "ON"
            ]
    ) as inst:
        assert inst.relative is True


def test_relative_set_already_enabled():
    with expected_protocol(
            ik.keithley.Keithley2182,
            [
                "SENS:FUNC?",
                "SENS:FUNC?",
                "SENS:VOLT:CHAN1:REF:STAT?",
                "SENS:VOLT:CHAN1:REF:ACQ"
            ],
            [
                "VOLT",
                "VOLT",
                "ON",
            ]
    ) as inst:
        inst.relative = True


def test_relative_set_start_disabled():
    with expected_protocol(
            ik.keithley.Keithley2182,
            [
                "SENS:FUNC?",
                "SENS:FUNC?",
                "SENS:VOLT:CHAN1:REF:STAT?",
                "SENS:VOLT:CHAN1:REF:STAT ON"
            ],
            [
                "VOLT",
                "VOLT",
                "OFF",
            ]
    ) as inst:
        inst.relative = True


def test_relative_set_wrong_type():
    with pytest.raises(TypeError), expected_protocol(
            ik.keithley.Keithley2182,
            [],
            []
    ) as inst:
        inst.relative = "derp"
