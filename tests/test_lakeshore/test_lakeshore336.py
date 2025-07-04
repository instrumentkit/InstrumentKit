#!/usr/bin/env python
"""
Module containing tests for the Lakeshore 336
"""

# IMPORTS ####################################################################

import pytest

import instruments as ik
from instruments.units import ureg as u
from tests import expected_protocol

# TESTS ######################################################################

# pylint: disable=protected-access

# TEST SENSOR CLASS #


def test_lakeshore336_sensor_init():
    """
    Test initialization of sensor class.
    """
    with expected_protocol(
        ik.lakeshore.Lakeshore336,
        [],
        [],
    ) as cryo:
        sensor = cryo.sensor[0]
        assert sensor._parent is cryo
        assert sensor._idx == "A"


@pytest.mark.parametrize("idx_ch", [(0, "A"), (1, "B"), (2, "C"), (3, "D")])
def test_lakeshore336_sensor_temperature(idx_ch):
    """
    Receive a unitful temperature from a sensor.
    """
    idx, ch = idx_ch
    with expected_protocol(
        ik.lakeshore.Lakeshore336,
        [f"KRDG?{ch}"],
        ["77"],
    ) as cryo:
        assert cryo.sensor[idx].temperature == u.Quantity(77, u.K)
