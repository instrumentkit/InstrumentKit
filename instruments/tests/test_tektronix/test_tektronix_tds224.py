#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing tests for the Tektronix TDS224
"""

# IMPORTS ####################################################################

from __future__ import absolute_import
from builtins import bytes

import numpy as np
from quantities import S, V, Hz

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
        assert tek.data_source == \
               ik.tektronix.tektds224._TekTDS224Channel(tek, 0)
        tek.data_source = tek.math


def test_tektds224_channel():
    with expected_protocol(
        ik.tektronix.TekTDS224,
        [],
        []
    ) as tek:
        assert tek.channel[0] == \
               ik.tektronix.tektds224._TekTDS224Channel(tek, 0)


def test_tektds224_cyclic_rms():
    with expected_protocol(
        ik.tektronix.TekTDS224,
        [
            "MEASU:IMM:SOU 1",
            "MEASU:IMM:TYP CRM",
            "MEASU:IMM:VAL?",
            "MEASU:IMM:SOU 2",
            "MEASU:IMM:TYP CRM",
            "MEASU:IMM:VAL?"
        ], [
            "10", "20"
        ]
    ) as tek:
        assert tek.channel[0].cyclic_rms() == 10.0 * V
        assert tek.channel[1].cyclic_rms() == 20.0 * V


def test_tektds224_fall_time():
    with expected_protocol(
        ik.tektronix.TekTDS224,
        [
            "MEASU:IMM:SOU 1",
            "MEASU:IMM:TYP FAL",
            "MEASU:IMM:VAL?",
            "MEASU:IMM:SOU 2",
            "MEASU:IMM:TYP FAL",
            "MEASU:IMM:VAL?"
        ], [
            "10", "20"
        ]
    ) as tek:
        assert tek.channel[0].fall_time() == 10.0 * S
        assert tek.channel[1].fall_time() == 20.0 * S


def test_tektds224_frequency():
    with expected_protocol(
        ik.tektronix.TekTDS224,
        [
            "MEASU:IMM:SOU 1",
            "MEASU:IMM:TYP FREQ",
            "MEASU:IMM:VAL?",
            "MEASU:IMM:SOU 2",
            "MEASU:IMM:TYP FREQ",
            "MEASU:IMM:VAL?"
        ], [
            "10", "20"
        ]
    ) as tek:
        assert tek.channel[0].frequency() == 10.0 * Hz
        assert tek.channel[1].frequency() == 20.0 * Hz


def test_tektds224_maximum():
    with expected_protocol(
        ik.tektronix.TekTDS224,
        [
            "MEASU:IMM:SOU 1",
            "MEASU:IMM:TYP MAXI",
            "MEASU:IMM:VAL?",
            "MEASU:IMM:SOU 2",
            "MEASU:IMM:TYP MAXI",
            "MEASU:IMM:VAL?"
        ], [
            "10", "20"
        ]
    ) as tek:
        assert tek.channel[0].maximum() == 10.0 * V
        assert tek.channel[1].maximum() == 20.0 * V


def test_tektds224_mean():
    with expected_protocol(
        ik.tektronix.TekTDS224,
        [
            "MEASU:IMM:SOU 1",
            "MEASU:IMM:TYP MEAN",
            "MEASU:IMM:VAL?",
            "MEASU:IMM:SOU 2",
            "MEASU:IMM:TYP MEAN",
            "MEASU:IMM:VAL?"
        ], [
            "10", "20"
        ]
    ) as tek:
        assert tek.channel[0].mean() == 10.0 * V
        assert tek.channel[1].mean() == 20.0 * V


def test_tektds224_minimum():
    with expected_protocol(
        ik.tektronix.TekTDS224,
        [
            "MEASU:IMM:SOU 1",
            "MEASU:IMM:TYP MINI",
            "MEASU:IMM:VAL?",
            "MEASU:IMM:SOU 2",
            "MEASU:IMM:TYP MINI",
            "MEASU:IMM:VAL?"
        ], [
            "10", "20"
        ]
    ) as tek:
        assert tek.channel[0].minimum() == 10.0 * V
        assert tek.channel[1].minimum() == 20.0 * V


def test_tektds224_negative_width():
    with expected_protocol(
        ik.tektronix.TekTDS224,
        [
            "MEASU:IMM:SOU 1",
            "MEASU:IMM:TYP NWI",
            "MEASU:IMM:VAL?",
            "MEASU:IMM:SOU 2",
            "MEASU:IMM:TYP NWI",
            "MEASU:IMM:VAL?"
        ], [
            "100", "200"
        ]
    ) as tek:
        assert tek.channel[0].negative_width() == 100.0 * S
        assert tek.channel[1].negative_width() == 200.0 * S


def test_tektds224_peak_peak():
    with expected_protocol(
        ik.tektronix.TekTDS224,
        [
            "MEASU:IMM:SOU 1",
            "MEASU:IMM:TYP PK2",
            "MEASU:IMM:VAL?",
            "MEASU:IMM:SOU 2",
            "MEASU:IMM:TYP PK2",
            "MEASU:IMM:VAL?"
        ], [
            "100", "200"
        ]
    ) as tek:
        assert tek.channel[0].peak_peak() == 100.0 * V
        assert tek.channel[1].peak_peak() == 200.0 * V


def test_tektds224_period():
    with expected_protocol(
        ik.tektronix.TekTDS224,
        [
            "MEASU:IMM:SOU 1",
            "MEASU:IMM:TYP PERI",
            "MEASU:IMM:VAL?",
            "MEASU:IMM:SOU 2",
            "MEASU:IMM:TYP PERI",
            "MEASU:IMM:VAL?"
        ], [
            "100", "200"
        ]
    ) as tek:
        assert tek.channel[0].period() == 100.0 * S
        assert tek.channel[1].period() == 200.0 * S


def test_tektds224_positive_width():
    with expected_protocol(
        ik.tektronix.TekTDS224,
        [
            "MEASU:IMM:SOU 1",
            "MEASU:IMM:TYP PWI",
            "MEASU:IMM:VAL?",
            "MEASU:IMM:SOU 2",
            "MEASU:IMM:TYP PWI",
            "MEASU:IMM:VAL?"
        ], [
            "100", "200"
        ]
    ) as tek:
        assert tek.channel[0].positive_width() == 100.0 * S
        assert tek.channel[1].positive_width() == 200.0 * S


def test_tektds224_rise_time():
    with expected_protocol(
        ik.tektronix.TekTDS224,
        [
            "MEASU:IMM:SOU 1",
            "MEASU:IMM:TYP RIS",
            "MEASU:IMM:VAL?",
            "MEASU:IMM:SOU 2",
            "MEASU:IMM:TYP RIS",
            "MEASU:IMM:VAL?"
        ], [
            "100", "200"
        ]
    ) as tek:
        assert tek.channel[0].rise_time() == 100.0 * S
        assert tek.channel[1].rise_time() == 200.0 * S


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
            "#210" + bytes.fromhex("00000001000200030004").decode("utf-8") +
            "0",
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
