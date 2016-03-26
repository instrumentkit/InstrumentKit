#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing tests for Agilent 34410a
"""

# IMPORTS ####################################################################

from __future__ import absolute_import
from builtins import bytes

import quantities as pq
import numpy as np

import instruments as ik
from instruments.tests import expected_protocol, make_name_test, unit_eq

# TESTS ######################################################################

test_agilent_34410a_name = make_name_test(ik.agilent.Agilent34410a)


def test_agilent34410a_read():
    with expected_protocol(
        ik.agilent.Agilent34410a,
        [
            "CONF?",
            "READ?"
        ], [
            "VOLT +1.000000E+01,+3.000000E-06",
            "+1.86850000E-03"
        ]
    ) as dmm:
        unit_eq(dmm.read_meter(), +1.86850000E-03 * pq.volt)


def test_agilent34410a_data_point_count():
    with expected_protocol(
        ik.agilent.Agilent34410a,
        [
            "DATA:POIN?",
        ], [
            "+215",
        ]
    ) as dmm:
        assert dmm.data_point_count == 215


def test_agilent34410a_r():
    with expected_protocol(
        ik.agilent.Agilent34410a,
        [
            "CONF?",
            "FORM:DATA REAL,64",
            "R? 1"
        ], [
            "VOLT +1.000000E+01,+3.000000E-06",
            # pylint: disable=no-member
            b"#18" + bytes.fromhex("3FF0000000000000")
        ]
    ) as dmm:
        unit_eq(dmm.r(1), np.array([1]) * pq.volt)


def test_agilent34410a_fetch():
    with expected_protocol(
        ik.agilent.Agilent34410a,
        [
            "CONF?",
            "FETC?"
        ], [
            "VOLT +1.000000E+01,+3.000000E-06",
            "+4.27150000E-03,5.27150000E-03"
        ]
    ) as dmm:
        data = dmm.fetch()
        unit_eq(data[0], 4.27150000E-03 * pq.volt)
        unit_eq(data[1], 5.27150000E-03 * pq.volt)


def test_agilent34410a_read_data():
    with expected_protocol(
        ik.agilent.Agilent34410a,
        [
            "CONF?",
            "FORM:DATA ASC",
            "DATA:REM? 2"
        ], [
            "VOLT +1.000000E+01,+3.000000E-06",
            "+4.27150000E-03,5.27150000E-03"
        ]
    ) as dmm:
        data = dmm.read_data(2)
        unit_eq(data[0], 4.27150000E-03 * pq.volt)
        unit_eq(data[1], 5.27150000E-03 * pq.volt)


def test_agilent34410a_read_data_nvmem():
    with expected_protocol(
        ik.agilent.Agilent34410a,
        [
            "CONF?",
            "DATA:DATA? NVMEM",
        ], [
            "VOLT +1.000000E+01,+3.000000E-06",
            "+4.27150000E-03,5.27150000E-03"
        ]
    ) as dmm:
        data = dmm.read_data_nvmem()
        unit_eq(data[0], 4.27150000E-03 * pq.volt)
        unit_eq(data[1], 5.27150000E-03 * pq.volt)


def test_agilent34410a_read_last_data():
    with expected_protocol(
        ik.agilent.Agilent34410a,
        [
            "DATA:LAST?",
        ], [
            "+1.73730000E-03 VDC",
        ]
    ) as dmm:
        unit_eq(dmm.read_last_data(), 1.73730000E-03 * pq.volt)
