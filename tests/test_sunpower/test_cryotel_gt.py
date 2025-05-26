#!/usr/bin/env python
"""
Module containing tests for the Sunpower CryoTel GT
"""

# IMPORTS ####################################################################

import pytest

import instruments as ik
from instruments.abstract_instruments.comm import GPIBCommunicator
from instruments.units import ureg as u
from tests import expected_protocol, make_name_test, unit_eq

# TESTS ######################################################################

# PROPERTIES #


def test_at_temperature_band():
    """Set/ get the at_temperature_band property of the CryoTel GT."""
    with expected_protocol(
        ik.sunpower.CryoTelGT,
        ["SET TBAND", "SET TBAND=0.07", "SET TBAND"],
        ["SET TBAND", "0.500", "SET TBAND=0.07", "0.07", "SET TBAND", "0.07"],
        sep="\r",
    ) as ct:
        assert ct.at_temperature_band == 0.5 * u.K
        ct.at_temperature_band = 0.07 * u.K
        assert ct.at_temperature_band == 0.07 * u.K


def test_control_mode():
    """Set/ get the control_mode property of the CryoTel GT."""
    with expected_protocol(
        ik.sunpower.CryoTelGT,
        ["SET PID", "SET PID=0", "SET PID"],
        ["SET PID", "2", "SET PID=0", "0", "SET PID", "0"],
        sep="\r",
    ) as ct:
        assert ct.control_mode == ct.ControlMode.TEMPERATURE
        ct.control_mode = ct.ControlMode.POWER
        assert ct.control_mode == ct.ControlMode.POWER

        with pytest.raises(ValueError):
            ct.control_mode = "invalid_mode"


def test_errors():
    """Get the error codes of the CryoTel GT and return error strings."""
    with expected_protocol(
        ik.sunpower.CryoTelGT,
        ["ERROR"],  # , "ERROR", "ERROR"],
        # ["ERROR", "100000", "ERROR", "000000", "ERROR", "011001"],
        ["ERROR", "011001"],
        sep="\r",
    ) as ct:
        # assert ct.errors == ["Temperature Sensor Error"]
        # assert ct.errors == []
        assert ct.errors == [
            "Over Current",
            "Non-volatile Memory Error",
            "Watchdog Error",
        ]


def test_ki():
    """Set/get the ki property of the CryoTel GT."""
    with expected_protocol(
        ik.sunpower.CryoTelGT,
        ["SET KI", "SET KI=0.10", "SET KI"],
        ["SET KI", "5.0", "SET KI=0.10", "0.1", "SET KI", "0.1"],
        sep="\r",
    ) as ct:
        assert ct.ki == 5.0
        ct.ki = 0.1
        assert ct.ki == 0.1


def test_kp():
    """Set/get the kp property of the CryoTel GT."""
    with expected_protocol(
        ik.sunpower.CryoTelGT,
        ["SET KP", "SET KP=0.10", "SET KP"],
        ["SET KP", "0.5", "SET KP=0.10", "0.10", "SET KP", "0.10"],
        sep="\r",
    ) as ct:
        assert ct.kp == 0.5
        ct.kp = 0.1
        assert ct.kp == 0.1


def test_power():
    """Get the current power of the CryoTel GT."""
    with expected_protocol(
        ik.sunpower.CryoTelGT,
        ["P", "P"],
        ["P", "0.00", "P", "500.0"],
        sep="\r",
    ) as ct:
        assert ct.power == 0.0 * u.W
        assert ct.power == 500 * u.W


def test_power_current_and_limits():
    """Get the current power and power limits of the CryoTel GT."""
    with expected_protocol(
        ik.sunpower.CryoTelGT,
        ["E"],
        ["P", "0.00", "500.00", "1000.00"],
        sep="\r",
    ) as ct:
        assert ct.power_current_and_limits == (0.0 * u.W, 500 * u.W, 1000 * u.W)


def test_power_max():
    """Get/set the maximum user power."""
    with expected_protocol(
        ik.sunpower.CryoTelGT,
        ["SET MAX", "SET MAX=100.00", "SET MAX"],
        ["SET MAX", "10.0", "SET MAX=100.00", "100.0", "SET MAX", "100.0"],
        sep="\r",
    ) as ct:
        assert ct.power_max == 10 * u.W
        ct.power_max = 100 * u.W
        assert ct.power_max == 100 * u.W

        with pytest.raises(ValueError):
            ct.power_max = 1000 * u.W
        with pytest.raises(ValueError):
            ct.power_max = -10 * u.W


def test_power_min():
    """Get/set the minimum user power."""
    with expected_protocol(
        ik.sunpower.CryoTelGT,
        ["SET MIN", "SET MIN=10.00", "SET MIN"],
        ["SET MIN", "0.0", "SET MIN=10.00", "10.0", "SET MIN", "10.0"],
        sep="\r",
    ) as ct:
        assert ct.power_min == 0 * u.W
        ct.power_min = 10 * u.W
        assert ct.power_min == 10 * u.W

        with pytest.raises(ValueError):
            ct.power_min = 1000 * u.W
        with pytest.raises(ValueError):
            ct.power_min = -10 * u.W


def test_power_set():
    """Get/set the power setpoint of the CryoTel GT."""
    with expected_protocol(
        ik.sunpower.CryoTelGT,
        ["SET PWOUT", "SET PWOUT=100.00", "SET PWOUT"],
        ["SET PWOUT", "0.00", "SET PWOUT=100.00", "100.00", "SET PWOUT", "100.00"],
        sep="\r",
    ) as ct:
        assert ct.power_set == 0 * u.W
        ct.power_set = 100 * u.W
        assert ct.power_set == 100 * u.W

        with pytest.raises(ValueError):
            ct.power_set = 1000 * u.W
        with pytest.raises(ValueError):
            ct.power_set = -10 * u.W


def test_serial_number():
    """Get the serial number of the CryoTel GT."""
    with expected_protocol(
        ik.sunpower.CryoTelGT,
        ["SERIAL"],
        ["SERIAL", "serial", "revision"],
        sep="\r",
    ) as ct:
        assert ct.serial_number == ["serial", "revision"]


def test_state():
    """Get the state of the CryoTel GT."""
    STATE_EXAMPLE = [
        "MODE = 002.00",
        "TSTATM = 000.00",
        "TSTAT = 000.00",
        "SSTOPM = 000.00",
        "SSTOP = 000.00",
        "PID = 002.00",
        "LOCK = 000.00",
        "MAX = 300.00",
        "MIN = 000.00",
        "PWOUT = 000.00",
        "TTARGET = 000.00",
        "TBAND = 000.50",
        "KI = 000.50",
        "KP = 050.00000",
    ]
    with expected_protocol(
        ik.sunpower.CryoTelGT,
        ["STATE"],
        ["STATE"] + STATE_EXAMPLE,
        sep="\r",
    ) as ct:
        assert ct.state == STATE_EXAMPLE


def test_temperature():
    """Get the temperature of the CryoTel GT."""
    with expected_protocol(
        ik.sunpower.CryoTelGT,
        ["TC", "TC"],
        ["TC", "77.00", "TC", "72.89"],
        sep="\r",
    ) as ct:
        assert ct.temperature == 77.0 * u.K
        assert ct.temperature == 72.89 * u.K


def test_temperature_set():
    """Get/set the temperature setpoint of the CryoTel GT."""
    with expected_protocol(
        ik.sunpower.CryoTelGT,
        ["SET TTARGET", "SET TTARGET=100.00", "SET TTARGET"],
        [
            "SET TTARGET",
            "0.00",
            "SET TTARGET=100.00",
            "100.00",
            "SET TTARGET",
            "100.00",
        ],
        sep="\r",
    ) as ct:
        assert ct.temperature_set == 0 * u.K
        ct.temperature_set = 100 * u.K
        assert ct.temperature_set == 100 * u.K


def test_thermostat():
    """Get/set the thermostat property of the CryoTel GT."""
    with expected_protocol(
        ik.sunpower.CryoTelGT,
        ["SET TSTATM", "SET TSTATM=1", "SET TSTATM"],
        ["SET TSTATM", "0", "SET TSTATM=1", "1", "SET TSTATM", "1"],
        sep="\r",
    ) as ct:
        assert ct.thermostat is False
        ct.thermostat = True
        assert ct.thermostat is True

        with pytest.raises(ValueError):
            ct.thermostat = "invalid_value"


def test_thermostat_status():
    """Get the thermostat status of the CryoTel GT."""
    with expected_protocol(
        ik.sunpower.CryoTelGT,
        ["TSTAT", "TSTAT"],
        ["TSTAT", "0.00", "TSTAT", "1.00"],
        sep="\r",
    ) as ct:
        assert ct.thermostat_status == ct.ThermostatStatus.OFF
        assert ct.thermostat_status == ct.ThermostatStatus.ON


def test_stop():
    """Get/set the soft stop property of the CryoTel GT to turn it off."""
    with expected_protocol(
        ik.sunpower.CryoTelGT,
        ["SET SSTOP", "SET SSTOP=1", "SET SSTOP"],
        ["SET SSTOP", "0", "SET SSTOP=1", "1", "SET SSTOP", "1"],
        sep="\r",
    ) as ct:
        assert ct.stop is False
        ct.stop = True
        assert ct.stop is True

        with pytest.raises(ValueError):
            ct.stop = "invalid_value"


def test_stop_mode():
    """Get/set the stop mode of the CryoTel GT."""
    with expected_protocol(
        ik.sunpower.CryoTelGT,
        ["SET SSTOPM", "SET SSTOPM=1", "SET SSTOPM"],
        ["SET SSTOPM", "0", "SET SSTOPM=1", "1", "SET SSTOPM", "1"],
        sep="\r",
    ) as ct:
        assert ct.stop_mode == ct.StopMode.HOST
        ct.stop_mode = ct.StopMode.DIGIO
        assert ct.stop_mode == ct.StopMode.DIGIO

        with pytest.raises(ValueError):
            ct.stop_mode = "invalid_mode"


# METHODS #


def test_reset():
    """Reset the CryoTel GT."""
    with expected_protocol(
        ik.sunpower.CryoTelGT,
        ["RESET=F"],
        ["RESET=F", "RESETTING TO FACTORY DEFAULT...", "FACTORY RESET COMPLETE!"],
        sep="\r",
    ) as ct:
        ct.reset()


def test_save_control_mode():
    """Save the current control mode of the CryoTel GT."""
    with expected_protocol(
        ik.sunpower.CryoTelGT,
        ["SAVE PID"],
        ["SAVE PID"],
        sep="\r",
    ) as ct:
        ct.save_control_mode()


def test_query_warning():
    """Raise a warning if a value was not set because not accepted."""
    with expected_protocol(
        ik.sunpower.CryoTelGT,
        ["SET TTARGET=0.00"],
        ["SET TTARGET=0.00", "77.00"],
        sep="\r",
    ) as ct:
        with pytest.warns(UserWarning) as warn:
            ct.temperature_set = 0 * u.K
            assert "Set value 0" in warn[0].message.args[0]
            assert "returned value 77" in warn[0].message.args[0]
