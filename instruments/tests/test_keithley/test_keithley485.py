#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing tests for the Keithley 485 picoammeter
"""

# IMPORTS ####################################################################

from __future__ import absolute_import

import quantities as pq

import instruments as ik
from instruments.tests import expected_protocol


# TESTS ######################################################################

def test_zero_check():
    with expected_protocol(
        ik.keithley.Keithley485,
        [
            "C0X",
            "C1X",
            "U0X"
        ], [
            "4851000000000:"
        ]
    ) as inst:
        inst.zero_check = False
        inst.zero_check = True
        assert inst.zero_check


def test_log():
    with expected_protocol(
        ik.keithley.Keithley485,
        [
            "D0X",
            "D1X",
            "U0X"
        ], [
            "4850100000000:"
        ]
    ) as inst:
        inst.log = False
        inst.log = True
        assert inst.log


def test_input_range():
    with expected_protocol(
        ik.keithley.Keithley485,
        [
            "R0X",
            "R7X",
            "U0X"
        ], [
            "4850070000000:"
        ]
    ) as inst:
        inst.input_range = "auto"
        inst.input_range = 2e-3
        assert inst.input_range == 2. * pq.milliamp


def test_relative():
    with expected_protocol(
        ik.keithley.Keithley485,
        [
            "Z0X",
            "Z1X",
            "U0X"
        ], [
            "4850001000000:"
        ]
    ) as inst:
        inst.relative = False
        inst.relative = True
        assert inst.relative


def test_eoi_mode():
    with expected_protocol(
        ik.keithley.Keithley485,
        [
            "K0X",
            "K1X",
            "U0X"
        ], [
            "4850000100000:"
        ]
    ) as inst:
        inst.eoi_mode = True
        inst.eoi_mode = False
        assert not inst.eoi_mode


def test_trigger_mode():
    with expected_protocol(
        ik.keithley.Keithley485,
        [
            "T0X",
            "T5X",
            "U0X"
        ], [
            "4850000050000:"
        ]
    ) as inst:
        inst.trigger_mode = "continuous_ontalk"
        inst.trigger_mode = "oneshot_onx"
        assert inst.trigger_mode == "oneshot_onx"


def test_auto_range():
    with expected_protocol(
        ik.keithley.Keithley485,
        [
            "R0X",
            "U0X"
        ], [
            "4850000000000:"
        ]
    ) as inst:
        inst.auto_range()
        assert inst.input_range == "auto"


def test_get_status():
    with expected_protocol(
        ik.keithley.Keithley485,
        [
            "U0X"
        ], [
            "4850000000000:"
        ]
    ) as inst:
        inst.get_status()


def test_measure():
    with expected_protocol(
        ik.keithley.Keithley485,
        [
            "X",
            "X"
        ], [
            "NDCA+1.2345E-9",
            "NDCL-9.0000E+0"
        ]
    ) as inst:
        assert inst.measure() == 1.2345 * pq.nanoamp
        assert inst.measure() == 1. * pq.nanoamp
