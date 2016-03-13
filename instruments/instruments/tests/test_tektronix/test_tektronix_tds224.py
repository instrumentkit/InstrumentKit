#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing tests for the Tektronix TDS224
"""

# IMPORTS ####################################################################

from __future__ import absolute_import
from builtins import bytes

import numpy as np

import instruments as ik
from instruments.tests import expected_protocol, make_name_test

# TESTS ######################################################################

# pylint: disable=protected-access

test_tektds224_name = make_name_test(ik.tektronix.TekTDS224)


def test_tektds224_data_width():
    with expected_protocol(
        ik.tektronix.TekTDS224,
        [
            "DATA:WIDTH?",
            "DATA:WIDTH 1"
        ], [
            "2"
        ]
    ) as tek:
        assert tek.data_width == 2
        tek.data_width = 1


def test_tektds224_data_source():
    with expected_protocol(
        ik.tektronix.TekTDS224,
        [
            "DAT:SOU?",
            "DAT:SOU MATH"
        ], [
            "CH1"
        ]
    ) as tek:
        assert tek.data_source == ik.tektronix.tektds224._TekTDS224Channel(tek, 0)
        tek.data_source = tek.math


def test_tektds224_channel():
    with expected_protocol(
        ik.tektronix.TekTDS224,
        [],
        []
    ) as tek:
        assert tek.channel[
            0] == ik.tektronix.tektds224._TekTDS224Channel(tek, 0)


def test_tektds224_channel_coupling():
    with expected_protocol(
        ik.tektronix.TekTDS224,
        [
            "CH1:COUPL?",
            "CH2:COUPL AC"
        ], [
            "DC"
        ]
    ) as tek:
        assert tek.channel[0].coupling == tek.Coupling.dc
        tek.channel[1].coupling = tek.Coupling.ac


def test_tektds224_data_source_read_waveform():
    with expected_protocol(
        ik.tektronix.TekTDS224,
        [
            "DAT:SOU?",
            "DAT:SOU CH2",
            "DAT:ENC RIB",
            "DATA:WIDTH?",
            "CURVE?",
            "WFMP:CH2:YOF?",
            "WFMP:CH2:YMU?",
            "WFMP:CH2:YZE?",
            "WFMP:XZE?",
            "WFMP:XIN?",
            "WFMP:CH2:NR_P?",
            "DAT:SOU CH1"
        ], [
            "CH1",
            "2",
            # pylint: disable=no-member
            "#210" + bytes.fromhex("00000001000200030004").decode("utf-8") + "0",
            "1",
            "0",
            "0",
            "1",
            "5"
        ]
    ) as tek:
        data = np.array([0, 1, 2, 3, 4])
        (x, y) = tek.channel[1].read_waveform()
        assert (x == data).all()
        assert (y == data).all()
