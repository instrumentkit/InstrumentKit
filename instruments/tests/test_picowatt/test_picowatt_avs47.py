#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for the Picowatt AVS47
"""

# IMPORTS #####################################################################

from __future__ import absolute_import

import quantities as pq

import instruments as ik
from instruments.tests import expected_protocol

# TESTS #######################################################################


def test_sensor_is_sensor_class():
    inst = ik.picowatt.PicowattAVS47.open_test()
    assert isinstance(inst.sensor[0], inst.Sensor) is True


def test_init():
    with expected_protocol(
        ik.picowatt.PicowattAVS47,
        [
            "HDR 0"
        ],
        []
    ) as _:
        pass


def test_sensor_resistance_same_channel():
    with expected_protocol(
        ik.picowatt.PicowattAVS47,
        [
            "HDR 0",
            "MUX?",
            "ADC",
            "RES?"
        ],
        [
            "0",
            "123"
        ]
    ) as inst:
        assert inst.sensor[0].resistance == 123 * pq.ohm


def test_sensor_resistance_different_channel():
    with expected_protocol(
        ik.picowatt.PicowattAVS47,
        [
            "HDR 0",
            "MUX?",
            "INP 0",
            "MUX 0",
            "INP 1",
            "ADC",
            "RES?"
        ],
        [
            "1",
            "123"
        ]
    ) as inst:
        assert inst.sensor[0].resistance == 123 * pq.ohm


def test_remote():
    with expected_protocol(
        ik.picowatt.PicowattAVS47,
        [
            "HDR 0",
            "REM?",
            "REM?",
            "REM 1",
            "REM 0"
        ],
        [
            "0",
            "1"
        ]
    ) as inst:
        assert inst.remote is False
        assert inst.remote is True
        inst.remote = True
        inst.remote = False


def test_input_source():
    with expected_protocol(
        ik.picowatt.PicowattAVS47,
        [
            "HDR 0",
            "INP?",
            "INP 1"
        ],
        [
            "0",
        ]
    ) as inst:
        assert inst.input_source == inst.InputSource.ground
        inst.input_source = inst.InputSource.actual


def test_mux_channel():
    with expected_protocol(
        ik.picowatt.PicowattAVS47,
        [
            "HDR 0",
            "MUX?",
            "MUX 1"
        ],
        [
            "3",
        ]
    ) as inst:
        assert inst.mux_channel == 3
        inst.mux_channel = 1


def test_excitation():
    with expected_protocol(
        ik.picowatt.PicowattAVS47,
        [
            "HDR 0",
            "EXC?",
            "EXC 1"
        ],
        [
            "3",
        ]
    ) as inst:
        assert inst.excitation == 3
        inst.excitation = 1


def test_display():
    with expected_protocol(
        ik.picowatt.PicowattAVS47,
        [
            "HDR 0",
            "DIS?",
            "DIS 1"
        ],
        [
            "3",
        ]
    ) as inst:
        assert inst.display == 3
        inst.display = 1
