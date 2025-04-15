#!/usr/bin/env python
"""
Module containing tests for the TPG 36x gauge controller
"""

# IMPORTS ####################################################################

import pytest

import instruments as ik
from instruments.units import ureg as u
from tests import expected_protocol, unit_eq

# TESTS ######################################################################

# pylint: disable=no-member,protected-access

SEP = "\r\n"
ENQ = chr(5)
ACK = chr(6)
NAK = chr(21)

# CHANNELS #


def test_tpg36x_channel_init():
    """Ensure an error is raised when not coming from correct class."""
    with pytest.raises(TypeError):
        ik.pfeiffer.TPG36x.Channel(42, 0)


def test_tpg36x_channel_pressure():
    """Get the pressure from the device."""
    with expected_protocol(
        ik.pfeiffer.TPG36x,
        ["PR1", SEP, ENQ, "UNI", SEP, ENQ],
        [ACK, SEP, "0,2.0000E-2", SEP, ACK, SEP, "0", SEP],
        sep="",
    ) as tpg:
        ch = tpg.channel[0]
        assert ch.pressure == 0.02 * u.mbar


@pytest.mark.parametrize(
    "status",
    [
        [1, "Underrange"],
        [2, "Overrange"],
        [3, "Sensor error"],
        [4, "Sensor off"],
        [5, "No sensor"],
        [6, "Identification error"],
        [42, "Unknown error"],
    ],
)
def test_tpg36x_channel_pressure_error(status):
    """Raise correct error if statos is not zero."""
    err_code, err_meaning = status
    with expected_protocol(
        ik.pfeiffer.TPG36x,
        ["PR1", SEP, ENQ],
        [ACK, SEP, f"{err_code},2.0000E-2", SEP],
        sep="",
    ) as tpg:
        ch = tpg.channel[0]
        with pytest.raises(OSError) as err:
            ch.pressure
            assert err.value.args[0].contains(err_meaning)


def test_tpg36x_channel_status():
    """Set/get the status of a channel."""
    with expected_protocol(
        ik.pfeiffer.TPG36x,
        ["SEN", SEP, ENQ, "SEN,0,2", SEP, "SEN", SEP, ENQ],
        [ACK, SEP, "0,1", SEP, ACK, SEP, ACK, SEP, "0,2", SEP],
        sep="",
    ) as tpg:
        ch0 = tpg.channel[0]
        assert ch0.status == ch0.SensorStatus.CANNOT_TURN_ON_OFF
        ch1 = tpg.channel[1]
        ch1.status = ch1.SensorStatus.ON
        assert ch1.status == ch1.SensorStatus.ON


def test_tpg36x_channel_status_error():
    """Raise ValueErrors if bad statuses are given."""
    with expected_protocol(
        ik.pfeiffer.TPG36x,
        [],
        [],
        sep="",
    ) as tpg:
        ch = tpg.channel[0]
        with pytest.raises(ValueError):
            ch.status = 42
        with pytest.raises(ValueError):
            ch.status = ch.SensorStatus.CANNOT_TURN_ON_OFF


# TPG36x #1


def test_tpg36x_ethernet_configuration_static():
    """Set/get the ethernet configuration."""
    ip = "192.168.1.10"
    subnet = "255.255.255.0"
    gateway = "192.168.1.1"
    with expected_protocol(
        ik.pfeiffer.TPG36x,
        [f"ETH,0,{ip},{subnet},{gateway}", SEP, "ETH", SEP, ENQ],
        [ACK, SEP, ACK, SEP, f"0,{ip},{subnet},{gateway}", SEP],
        sep="",
    ) as tpg:
        tpg.ethernet_configuration = [
            tpg.EthernetMode.STATIC,
            "192.168.1.10",
            "255.255.255.0",
            "192.168.1.1",
        ]
        mode, ip_rec, subnet_rec, gateway_rec = tpg.ethernet_configuration
        assert mode == tpg.EthernetMode.STATIC
        assert ip == ip_rec
        assert subnet == subnet_rec
        assert gateway == gateway_rec


def test_tpg36x_ethernet_configuration_dhcp():
    """Set/get the ethernet configuration (static)."""
    zero_address = "0.0.0.0"
    with expected_protocol(
        ik.pfeiffer.TPG36x,
        [f"ETH,1,{zero_address},{zero_address},{zero_address}", SEP],
        [ACK, SEP],
        sep="",
    ) as tpg:
        tpg.ethernet_configuration = tpg.EthernetMode.DHCP


def test_tpg36x_ethernet_configuration_errors():
    """Raise appropriate errors for bad settings."""
    good_addr = "192.168.1.1"
    with expected_protocol(
        ik.pfeiffer.TPG36x,
        [],
        [],
        sep="",
    ) as tpg:
        with pytest.raises(ValueError):  # invalid list
            tpg.ethernet_configuration = [tpg.EthernetMode.STATIC, 42]
        with pytest.raises(ValueError):  # ip address is a number
            tpg.ethernet_configuration = [
                tpg.EthernetMode.STATIC,
                42,
                good_addr,
                good_addr,
            ]
        with pytest.raises(ValueError):  # incorrect subnet
            tpg.ethernet_configuration = [
                tpg.EthernetMode.STATIC,
                good_addr,
                "192.169",
                good_addr,
            ]

        with pytest.raises(ValueError):  # incorrect gateway
            tpg.ethernet_configuration = [
                tpg.EthernetMode.STATIC,
                good_addr,
                good_addr,
                "192.168.1.256",
            ]
        with pytest.raises(ValueError):  # first value not an EthernetMode
            tpg.ethernet_configuration = [42, good_addr, good_addr, good_addr]


def test_tpg36x_language():
    """Set/get the language of the TPG36x."""
    with expected_protocol(
        ik.pfeiffer.TPG36x,
        ["LNG,0", SEP, "LNG", SEP, ENQ],
        [ACK, SEP, ACK, SEP, "0", SEP],
        sep="",
    ) as tpg:
        tpg.language = tpg.Language.ENGLISH
        assert tpg.language == tpg.Language.ENGLISH


def test_tpg36x_mac_address():
    """Get the MAC address of the TPG36x."""
    with expected_protocol(
        ik.pfeiffer.TPG36x,
        ["MAC", SEP, ENQ],
        [ACK, SEP, "00:00:00:00:00:00", SEP],
        sep="",
    ) as tpg:
        assert tpg.mac_address == "00:00:00:00:00:00"


def test_tpg36x_mac_address_name():
    """Get the name from the TPG36x."""
    with expected_protocol(
        ik.pfeiffer.TPG36x,
        ["AYT", SEP, ENQ],
        [ACK, SEP, "TPG 362,PTG28290,44990000,010100,010100", SEP],
        sep="",
    ) as tpg:
        assert tpg.name == "TPG 362"


def test_tpg36x_number_channels():
    """Set/get the number of channels."""
    with expected_protocol(
        ik.pfeiffer.TPG36x,
        [],
        [],
        sep="",
    ) as tpg:
        tpg.number_channels = 2
        assert tpg.number_channels == 2

    with expected_protocol(
        ik.pfeiffer.TPG36x,
        [],
        [],
        sep="",
    ) as tpg:
        tpg.number_channels = 1
        assert tpg.number_channels == 1


@pytest.mark.parametrize("bad_num", [3, 0])
def test_tpg36x_number_channels_error(bad_num):
    """Raise ValueErrors if bad number of channels are given."""
    with expected_protocol(
        ik.pfeiffer.TPG36x,
        [],
        [],
        sep="",
    ) as tpg:
        with pytest.raises(ValueError):
            tpg.number_channels = bad_num


def test_tpg36x_pressure():
    """Get the pressure from a one-channel device."""
    with expected_protocol(
        ik.pfeiffer.TPG36x,
        ["PR1", SEP, ENQ, "UNI", SEP, ENQ],
        [ACK, SEP, "0,2.0000E-2", SEP, ACK, SEP, "0", SEP],
        sep="",
    ) as tpg:
        assert tpg.pressure == 0.02 * u.mbar


@pytest.mark.parametrize("ret_val", [0, 1, 2, 3, 4, 5])
def test_tpg36x_unit(ret_val):
    """Get the unit from the device."""
    with expected_protocol(
        ik.pfeiffer.TPG36x,
        ["UNI", SEP, ENQ],
        [ACK, SEP, f"{int(ret_val)}", SEP],
        sep="",
    ) as tpg:
        assert tpg.unit == tpg.Unit(ret_val)


def test_tpg36x_unit_string():
    """Set a unit from a string."""
    with expected_protocol(
        ik.pfeiffer.TPG36x,
        ["UNI,0", SEP, "UNI", SEP, ENQ],
        [ACK, SEP, ACK, SEP, "0", SEP],
        sep="",
    ) as tpg:
        tpg.unit = "mbar"
        assert tpg.unit == tpg.Unit.MBAR
