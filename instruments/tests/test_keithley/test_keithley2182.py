#!/usr/bin/env python
"""
Unit tests for the Keithley 2182 nano-voltmeter
"""

# IMPORTS #####################################################################


import pytest

import instruments as ik
from instruments.optional_dep_finder import numpy
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
        ],
    ) as inst:
        channel = inst.channel[0]
        assert channel.mode == inst.Mode.voltage_dc
        with pytest.raises(NotImplementedError):
            channel.mode = 42


def test_channel_trigger_mode():
    """Raise NotImplementedError when getting / setting trigger mode."""
    with expected_protocol(ik.keithley.Keithley2182, [], []) as inst:
        channel = inst.channel[0]
        with pytest.raises(NotImplementedError):
            _ = channel.trigger_mode
        with pytest.raises(NotImplementedError):
            channel.trigger_mode = 42


def test_channel_relative():
    """Raise NotImplementedError when getting / setting relative."""
    with expected_protocol(ik.keithley.Keithley2182, [], []) as inst:
        channel = inst.channel[0]
        with pytest.raises(NotImplementedError):
            _ = channel.relative
        with pytest.raises(NotImplementedError):
            channel.relative = 42


def test_channel_input_range():
    """Raise NotImplementedError when getting / setting input range."""
    with expected_protocol(ik.keithley.Keithley2182, [], []) as inst:
        channel = inst.channel[0]
        with pytest.raises(NotImplementedError):
            _ = channel.input_range
        with pytest.raises(NotImplementedError):
            channel.input_range = 42


def test_channel_measure_mode_not_none():
    """Raise NotImplementedError measuring with non-None mode."""
    with expected_protocol(ik.keithley.Keithley2182, [], []) as inst:
        channel = inst.channel[0]
        with pytest.raises(NotImplementedError):
            channel.measure(mode="Some Mode")


def test_channel_measure_voltage():
    with expected_protocol(
        ik.keithley.Keithley2182,
        ["SENS:CHAN 1", "SENS:DATA:FRES?", "SENS:FUNC?"],
        [
            "1.234",
            "VOLT",
        ],
    ) as inst:
        channel = inst.channel[0]
        assert channel.measure() == 1.234 * u.volt


def test_channel_measure_temperature():
    with expected_protocol(
        ik.keithley.Keithley2182,
        ["SENS:CHAN 1", "SENS:DATA:FRES?", "SENS:FUNC?", "UNIT:TEMP?"],
        ["1.234", "TEMP", "C"],
    ) as inst:
        channel = inst.channel[0]
        assert channel.measure() == u.Quantity(1.234, u.degC)


def test_channel_measure_unknown_temperature_units():
    with pytest.raises(ValueError), expected_protocol(
        ik.keithley.Keithley2182,
        ["SENS:CHAN 1", "SENS:DATA:FRES?", "SENS:FUNC?", "UNIT:TEMP?"],
        ["1.234", "TEMP", "Z"],
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
            "SENS:FUNC?",
        ],
        ["TEMP", "C", "TEMP", "F", "TEMP", "K", "VOLT"],
    ) as inst:
        assert inst.units == u.degC
        assert inst.units == u.degF
        assert inst.units == u.kelvin
        assert inst.units == u.volt


def test_fetch():
    with expected_protocol(
        ik.keithley.Keithley2182,
        ["FETC?", "SENS:FUNC?"],
        [
            "1.234,1,5.678",
            "VOLT",
        ],
    ) as inst:
        data = inst.fetch()
        vals = [1.234, 1, 5.678]
        expected_data = tuple(v * u.volt for v in vals)
        if numpy:
            expected_data = vals * u.volt
        iterable_eq(data, expected_data)


def test_measure():
    with expected_protocol(
        ik.keithley.Keithley2182,
        [
            "SENS:FUNC?",
            "MEAS:VOLT?",
            "SENS:FUNC?",
        ],
        ["VOLT", "1.234", "VOLT"],
    ) as inst:
        assert inst.measure() == 1.234 * u.volt


def test_measure_invalid_mode():
    with pytest.raises(TypeError), expected_protocol(
        ik.keithley.Keithley2182, [], []
    ) as inst:
        inst.measure("derp")


def test_relative_get():
    with expected_protocol(
        ik.keithley.Keithley2182,
        ["SENS:FUNC?", "SENS:VOLT:CHAN1:REF:STAT?"],
        ["VOLT", "ON"],
    ) as inst:
        assert inst.relative is True


def test_relative_set_already_enabled():
    with expected_protocol(
        ik.keithley.Keithley2182,
        [
            "SENS:FUNC?",
            "SENS:FUNC?",
            "SENS:VOLT:CHAN1:REF:STAT?",
            "SENS:VOLT:CHAN1:REF:ACQ",
        ],
        [
            "VOLT",
            "VOLT",
            "ON",
        ],
    ) as inst:
        inst.relative = True


def test_relative_set_start_disabled():
    with expected_protocol(
        ik.keithley.Keithley2182,
        [
            "SENS:FUNC?",
            "SENS:FUNC?",
            "SENS:VOLT:CHAN1:REF:STAT?",
            "SENS:VOLT:CHAN1:REF:STAT ON",
        ],
        [
            "VOLT",
            "VOLT",
            "OFF",
        ],
    ) as inst:
        inst.relative = True


def test_relative_set_wrong_type():
    with pytest.raises(TypeError), expected_protocol(
        ik.keithley.Keithley2182, [], []
    ) as inst:
        inst.relative = "derp"


def test_input_range():
    """Raise NotImplementedError when getting / setting input range."""
    with expected_protocol(ik.keithley.Keithley2182, [], []) as inst:
        with pytest.raises(NotImplementedError):
            _ = inst.input_range
        with pytest.raises(NotImplementedError):
            inst.input_range = 42
