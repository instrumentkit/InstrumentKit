#!/usr/bin/env python
"""
Tests for the Mettler Toledo Standard Interface Command Set (SICS).
"""

# IMPORTS #####################################################################

import instruments as ik
from tests import expected_protocol

from instruments.units import ureg as u


# TESTS #######################################################################


def test_reset():
    """Reset the balance."""
    with expected_protocol(
        ik.mettler_toledo.MTSICS, ["@"], ['@ A "123456789"'], "\r\n"
    ) as inst:
        inst.reset()


def test_zero():
    """Zero the balance."""
    with expected_protocol(ik.mettler_toledo.MTSICS, ["Z"], ["Z A"], "\r\n") as inst:
        inst.zero()


def test_zero_immidiately():
    """Zero the balance immediately."""
    with expected_protocol(ik.mettler_toledo.MTSICS, ["ZI"], ["ZI A"], "\r\n") as inst:
        inst.zero_immediately()


# PROPERTIES #


def test_mt_sics():
    """Get MT-SICS level and MT-SICS versions."""
    with expected_protocol(
        ik.mettler_toledo.MTSICS, ["I1"], ["I1 A 01 2.00 2.00 2.00 1.0"], "\r\n"
    ) as inst:
        assert inst.mt_sics == ["01", "2.00", "2.00", "2.00", "1.0"]


def test_serial_number():
    """Get the serial number of the instrument."""
    with expected_protocol(
        ik.mettler_toledo.MTSICS, ["I4"], ["I4 A 0123456789"], "\r\n"
    ) as inst:
        assert inst.serial_number == "0123456789"


def test_weight():
    """Get the stable weight."""
    with expected_protocol(
        ik.mettler_toledo.MTSICS, ["S"], ["S A 1.234 g"], "\r\n"
    ) as inst:
        assert inst.weight == u.Quantity(1.234, u.gram)


def test_weigth_immediately():
    """Get the immediate weight."""
    with expected_protocol(
        ik.mettler_toledo.MTSICS, ["SI"], ["S D 1.234 g"], "\r\n"
    ) as inst:
        assert inst.weight_immediately == u.Quantity(1.234, u.gram)
