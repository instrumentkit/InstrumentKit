#!/usr/bin/env python
"""
Module containing tests for the HP E3631A power supply
"""

# IMPORTS #####################################################################

import time

import pytest

from instruments.units import ureg as u

import instruments as ik
from instruments.tests import expected_protocol


# TESTS #######################################################################


@pytest.fixture(autouse=True)
def time_mock(mocker):
    """Mock out time such that the tests go faster."""
    return mocker.patch.object(time, "sleep", return_value=None)


def test_channel():
    with expected_protocol(
        ik.hp.HPe3631a,
        ["SYST:REM", "INST:NSEL?", "INST:NSEL?", "INST:NSEL 2", "INST:NSEL?"],
        ["1", "1", "2"],
    ) as inst:
        assert inst.channelid == 1
        assert inst.channel[2] == inst
        assert inst.channelid == 2
        assert inst.channel.__len__() == len([1, 2, 3])  # len of valild set


def test_channelid():
    with expected_protocol(
        ik.hp.HPe3631a,
        ["SYST:REM", "INST:NSEL?", "INST:NSEL 2", "INST:NSEL?"],  # 0  # 1  # 2  # 3
        ["1", "2"],  # 1  # 3
    ) as inst:
        assert inst.channelid == 1
        inst.channelid = 2
        assert inst.channelid == 2


def test_mode():
    """Raise AttributeError since instrument sets mode automatically."""
    with expected_protocol(ik.hp.HPe3631a, ["SYST:REM"], []) as inst:
        with pytest.raises(AttributeError) as err_info:
            _ = inst.mode()
        err_msg = err_info.value.args[0]
        assert err_msg == "The `HPe3631a` sets its mode automatically"


def test_voltage():
    with expected_protocol(
        ik.hp.HPe3631a,
        [
            "SYST:REM",  # 0
            "SOUR:VOLT? MAX",  # 1
            "SOUR:VOLT? MAX",  # 2
            "SOUR:VOLT? MAX",  # 3.1
            "SOUR:VOLT 3.000000e+00",  # 3.2
            "SOUR:VOLT?",  # 4
            "SOUR:VOLT? MAX",  # 5
            "SOUR:VOLT? MAX",  # 6
        ],
        ["6.0", "6.0", "6.0", "3.0", "6.0", "6.0"],  # 1  # 2  # 3.1  # 4  # 5  # 6
    ) as inst:
        assert inst.voltage_min == 0.0 * u.volt
        assert inst.voltage_max == 6.0 * u.volt
        inst.voltage = 3.0 * u.volt
        assert inst.voltage == 3.0 * u.volt
        with pytest.raises(ValueError) as err_info:
            newval = -1.0 * u.volt
            inst.voltage = newval
        err_msg = err_info.value.args[0]
        assert (
            err_msg == f"Voltage quantity is too low. Got {newval}, "
            f"minimum value is {0.}"
        )
        with pytest.raises(ValueError) as err_info:
            newval = 7.0 * u.volt
            inst.voltage = newval
        err_msg = err_info.value.args[0]
        assert (
            err_msg == f"Voltage quantity is too high. Got {newval}, "
            f"maximum value is {u.Quantity(6.0, u.V)}"
        )


def test_voltage_range_negative():
    """Get voltage max if negative."""
    max_volts = -6.0
    with expected_protocol(
        ik.hp.HPe3631a,
        ["SYST:REM", "SOUR:VOLT? MAX"],  # 0  # 1
        [
            f"{max_volts}",  # 1
        ],
    ) as inst:
        expected_value = u.Quantity(max_volts, u.V), 0.0
        received_value = inst.voltage_range
        assert expected_value == received_value


def test_current():
    with expected_protocol(
        ik.hp.HPe3631a,
        [
            "SYST:REM",  # 0
            "SOUR:CURR? MIN",  # 1.1
            "SOUR:CURR? MAX",  # 1.2
            "SOUR:CURR? MIN",  # 2.1
            "SOUR:CURR? MAX",  # 2.2
            "SOUR:CURR 2.000000e+00",  # 3
            "SOUR:CURR?",  # 4
            "SOUR:CURR? MIN",  # 5
            "SOUR:CURR? MIN",  # 6.1
            "SOUR:CURR? MAX",  # 6.2
        ],
        [
            "0.0",  # 1.1
            "5.0",  # 1.2
            "0.0",  # 2.1
            "5.0",  # 2.2
            "2.0",  # 4
            "0.0",  # 5
            "0.0",  # 6.1
            "5.0",  # 6.2
        ],
    ) as inst:
        assert inst.current_min == 0.0 * u.amp
        assert inst.current_max == 5.0 * u.amp
        inst.current = 2.0 * u.amp
        assert inst.current == 2.0 * u.amp
        try:
            inst.current = -1.0 * u.amp
        except ValueError:
            pass
        try:
            inst.current = 6.0 * u.amp
        except ValueError:
            pass


def test_voltage_sense():
    with expected_protocol(
        ik.hp.HPe3631a, ["SYST:REM", "MEAS:VOLT?"], ["1.234"]  # 0  # 1  # 1
    ) as inst:
        assert inst.voltage_sense == 1.234 * u.volt


def test_current_sense():
    with expected_protocol(
        ik.hp.HPe3631a, ["SYST:REM", "MEAS:CURR?"], ["1.234"]  # 0  # 1  # 1
    ) as inst:
        assert inst.current_sense == 1.234 * u.amp
