#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for the Oxford ITC 503 temperature controller
"""

# IMPORTS #####################################################################

from __future__ import absolute_import

import quantities as pq

import instruments as ik
from instruments.tests import expected_protocol

# TESTS #######################################################################


def test_sensor_returns_sensor_class():
    with expected_protocol(
        ik.oxford.OxfordITC503,
        [
            "C3"
        ],
        [],
        sep="\r"
    ) as inst:
        sensor = inst.sensor[0]
        assert isinstance(sensor, inst.Sensor) is True


def test_sensor_temperature():
    with expected_protocol(
        ik.oxford.OxfordITC503,
        [
            "C3",
            "R1"
        ],
        [
            "R123"
        ],
        sep="\r"
    ) as inst:
        sensor = inst.sensor[0]
        assert sensor.temperature == 123 * pq.kelvin
