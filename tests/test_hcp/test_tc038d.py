#!/usr/bin/env python
"""
Unit tests for the HCP TC038D
"""

# IMPORTS #####################################################################


from tests import (
    expected_protocol,
    unit_eq,
    pytest
)

from instruments.units import ureg as u


from instruments.hcp import TC038D


def test_write_multiple():
    # Communication from manual.
    with expected_protocol(
            TC038D,
            [b"\x01\x10\x01\x0A\x00\x04\x08\x00\x00\x03\xE8\xFF\xFF\xFC\x18\x8D\xE9"],
            [b"\x01\x10\x01\x0A\x00\x04\xE0\x34"],
            sep="") as inst:
        inst.writeMultiple(0x010A, [1000, -1000])


def test_write_multiple_CRC_error():
    with expected_protocol(
            TC038D,
            [b"\x01\x10\x01\x06\x00\x02\x04\x00\x00\x01A\xbf\xb5"],
            [b"\x01\x10\x01\x06\x00\x02\x01\x02"],
            sep="") as inst:
        with pytest.raises(ConnectionError):
            inst.setpoint = u.Quantity(32.1, u.degC)


def test_read_CRC_error():
    with expected_protocol(TC038D, [b"\x01\x03\x00\x00\x00\x02\xC4\x0B"],
                           [b"\x01\x03\x04\x00\x00\x03\xE8\x01\x02"],
                           sep="") as inst:
        with pytest.raises(ConnectionError):
            inst.temperature


def test_setpoint():
    with expected_protocol(TC038D, [b"\x01\x03\x01\x06\x00\x02\x25\xf6"],
                           [b"\x01\x03\x04\x00\x00\x00\x99:Y"],
                           sep="") as inst:
        value = inst.setpoint
        unit_eq(value, u.Quantity(15.3, u.degC))


def test_setpoint_setter():
    with expected_protocol(
            TC038D,
            [b"\x01\x10\x01\x06\x00\x02\x04\x00\x00\x01A\xbf\xb5"],
            [b"\x01\x10\x01\x06\x00\x02\xa0\x35"],
            sep="") as inst:
        inst.setpoint = u.Quantity(32.1, u.degC)


def test_temperature():
    # Communication from manual.
    # Tests readRegister as well.
    with expected_protocol(TC038D, [b"\x01\x03\x00\x00\x00\x02\xC4\x0B"],
                           [b"\x01\x03\x04\x00\x00\x03\xE8\xFA\x8D"],
                           sep="") as inst:
        value = inst.temperature
        unit_eq(value, u.Quantity(100, u.degC))
