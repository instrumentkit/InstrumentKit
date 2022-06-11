#!/usr/bin/env python
"""
Unit tests for the HCP TC038
"""

# IMPORTS #####################################################################


from tests import expected_protocol, unit_eq, pytest
from instruments.units import ureg as u


from instruments.hcp import TC038


def test_sendcmd():
    with expected_protocol(TC038, ["\x0201010x\x03"], [], sep="\r") as inst:
        inst.sendcmd("x")


def test_query():
    with expected_protocol(TC038, ["\x0201010x\x03"], ["y"], sep="\r") as inst:
        assert inst.query("x") == "y"


def test_setpoint():
    with expected_protocol(
        TC038, ["\x0201010WRDD0120,01\x03"], ["\x020101OK00C8\x03"], sep="\r"
    ) as inst:
        value = inst.setpoint
        unit_eq(value, u.Quantity(20, u.degC))


def test_setpoint_setter():
    # Communication from manual.
    with expected_protocol(
        TC038, ["\x0201010WWRD0120,01,00C8\x03"], ["\x020101OK\x03"], sep="\r"
    ) as inst:
        inst.setpoint = 20


def test_temperature():
    # Communication from manual.
    with expected_protocol(
        TC038, ["\x0201010WRDD0002,01\x03"], ["\x020101OK00C8\x03"], sep="\r"
    ) as inst:
        value = inst.temperature
        unit_eq(value, u.Quantity(20, u.degC))


def test_monitored():
    # Communication from manual.
    with expected_protocol(
            TC038, ["\x0201010WRM\x03"], ["\x020101OK00C8\x03"], sep="\r"
    ) as inst:
        value = inst.monitored_value
        unit_eq(value, u.Quantity(20, u.degC))


def test_set_monitored():
    # Communication from manual.
    with expected_protocol(
        TC038, ["\x0201010WRS01D0002\x03"], ["\x020101OK\x03"], sep="\r"
    ) as inst:
        inst.monitored_quantity = "temperature"
        assert inst.monitored_quantity == "temperature"


def test_set_monitored_wrong_input():
    with expected_protocol(TC038, [], [], sep="\r") as inst:
        with pytest.raises(AssertionError):
            inst.monitored_quantity = "temper"


def test_information():
    # Communication from manual.
    with expected_protocol(
        TC038, ["\x0201010INF6\x03"],
        ["\x020101OKUT150333 V01.R001111222233334444\x03"], sep="\r"
    ) as inst:
        value = inst.information
        assert value == "UT150333 V01.R001111222233334444"
