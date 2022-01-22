#!/usr/bin/env python
"""
Module containing tests for the Lakeshore 340
"""

# IMPORTS ####################################################################

import instruments as ik
from instruments.units import ureg as u
from instruments.tests import expected_protocol

# TESTS ######################################################################

# pylint: disable=protected-access

# TEST SENSOR CLASS #


def test_lakeshore340_sensor_init():
    """
    Test initialization of sensor class.
    """
    with expected_protocol(
        ik.lakeshore.Lakeshore340,
        [],
        [],
    ) as cryo:
        sensor = cryo.sensor[0]
        assert sensor._parent is cryo
        assert sensor._idx == 1


def test_lakeshore340_sensor_temperature():
    """
    Receive a unitful temperature from a sensor.
    """
    with expected_protocol(
        ik.lakeshore.Lakeshore340,
        ["KRDG?1"],
        ["77"],
    ) as cryo:
        assert cryo.sensor[0].temperature == u.Quantity(77, u.K)
