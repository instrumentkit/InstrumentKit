#!/usr/bin/env python
"""
Module containing tests for the Thorlabs PM100USB
"""

# IMPORTS ####################################################################


from hypothesis import (
    given,
    strategies as st,
)
import pytest

import instruments as ik
from instruments.tests import expected_protocol


# TESTS ######################################################################


# pylint: disable=protected-access,redefined-outer-name


# FIXTURES #


@pytest.fixture
def init_sensor():
    """Initialize a sensor - return initialized sensor class."""

    class Sensor:
        """Initialize a sensor class"""

        NAME = "SENSOR"
        SERIAL_NUMBER = "123456"
        CALIBRATION_MESSAGE = "OK"
        SENSOR_TYPE = "TEMPERATURE"
        SENSOR_SUBTYPE = "KDP"
        FLAGS = "256"

        def sendmsg(self):
            return "SYST:SENSOR:IDN?"

        def message(self):
            return ",".join(
                [
                    self.NAME,
                    self.SERIAL_NUMBER,
                    self.CALIBRATION_MESSAGE,
                    self.SENSOR_TYPE,
                    self.SENSOR_SUBTYPE,
                    self.FLAGS,
                ]
            )

    return Sensor()


# SENSOR CLASS #


def test_sensor_init(init_sensor):
    """Initialize a sensor object from the parent class."""
    with expected_protocol(
        ik.thorlabs.PM100USB, [init_sensor.sendmsg()], [init_sensor.message()]
    ) as inst:
        assert inst.sensor._parent is inst


def test_sensor_name(init_sensor):
    """Get name of the sensor."""
    with expected_protocol(
        ik.thorlabs.PM100USB, [init_sensor.sendmsg()], [init_sensor.message()]
    ) as inst:
        assert inst.sensor.name == init_sensor.NAME


def test_sensor_serial_number(init_sensor):
    """Get serial number of the sensor."""
    with expected_protocol(
        ik.thorlabs.PM100USB, [init_sensor.sendmsg()], [init_sensor.message()]
    ) as inst:
        assert inst.sensor.serial_number == init_sensor.SERIAL_NUMBER


def test_sensor_calibration_message(init_sensor):
    """Get calibration message of the sensor."""
    with expected_protocol(
        ik.thorlabs.PM100USB, [init_sensor.sendmsg()], [init_sensor.message()]
    ) as inst:
        assert inst.sensor.calibration_message == init_sensor.CALIBRATION_MESSAGE


def test_sensor_type(init_sensor):
    """Get type of the sensor."""
    with expected_protocol(
        ik.thorlabs.PM100USB, [init_sensor.sendmsg()], [init_sensor.message()]
    ) as inst:
        assert inst.sensor.type == (init_sensor.SENSOR_TYPE, init_sensor.SENSOR_SUBTYPE)


def test_sensor_flags(init_sensor):
    """Get flags of the sensor."""
    flag_read = init_sensor.FLAGS
    flags = ik.thorlabs.PM100USB._SensorFlags(
        **{e.name: bool(e & int(flag_read)) for e in ik.thorlabs.PM100USB.SensorFlags}
    )
    with expected_protocol(
        ik.thorlabs.PM100USB, [init_sensor.sendmsg()], [init_sensor.message()]
    ) as inst:
        assert inst.sensor.flags == flags


# INSTRUMENT #


def test_cache_units():
    """Get, set cache units bool."""
    msr_conf = ik.thorlabs.PM100USB.MeasurementConfiguration.current
    with expected_protocol(
        ik.thorlabs.PM100USB,
        ["CONF?"],
        [f"{msr_conf.value}"],  # measurement configuration temperature
    ) as inst:
        inst.cache_units = True
        assert inst._cache_units == inst._READ_UNITS[msr_conf]
        inst.cache_units = False
        assert not inst.cache_units


@pytest.mark.parametrize("msr_conf", ik.thorlabs.PM100USB.MeasurementConfiguration)
def test_measurement_configuration(msr_conf):
    """Get / set measurement configuration."""
    with expected_protocol(
        ik.thorlabs.PM100USB,
        [f"CONF {msr_conf.value}", "CONF?"],
        [f"{msr_conf.value}"],  # measurement configuration temperature
    ) as inst:
        inst.measurement_configuration = msr_conf
        assert inst.measurement_configuration == msr_conf


@given(value=st.integers(min_value=1))
def test_averaging_count(value):
    """Get / set averaging count."""
    with expected_protocol(
        ik.thorlabs.PM100USB,
        [f"SENS:AVER:COUN {value}", "SENS:AVER:COUN?"],
        [f"{value}"],  # measurement configuration temperature
    ) as inst:
        inst.averaging_count = value
        assert inst.averaging_count == value


@given(value=st.integers(max_value=0))
def test_averaging_count_value_error(value):
    """Raise a ValueError if the averaging count is wrong."""
    with expected_protocol(ik.thorlabs.PM100USB, [], []) as inst:
        with pytest.raises(ValueError) as err_info:
            inst.averaging_count = value
        err_msg = err_info.value.args[0]
        assert err_msg == "Must count at least one time."


@given(value=st.floats(min_value=0))
def test_read(value):
    """Read instrument and grab the units."""
    msr_conf = ik.thorlabs.PM100USB.MeasurementConfiguration.current
    with expected_protocol(
        ik.thorlabs.PM100USB,
        ["CONF?", "READ?"],
        [f"{msr_conf.value}", f"{value}"],  # measurement configuration temperature
    ) as inst:
        units = inst._READ_UNITS[msr_conf]  # cache units is False at init
        assert inst.read() == value * units


def test_read_cached_units():
    """Read instrument and grab the units."""
    msr_conf = ik.thorlabs.PM100USB.MeasurementConfiguration.current
    value = 42
    with expected_protocol(
        ik.thorlabs.PM100USB,
        ["CONF?", "READ?"],
        [f"{msr_conf.value}", f"{value}"],  # measurement configuration temperature
    ) as inst:
        units = inst._READ_UNITS[msr_conf]  # cache units is False at init
        inst.cache_units = True
        assert inst.read() == value * units
