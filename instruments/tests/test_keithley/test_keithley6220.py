#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for the Keithley 6220 constant current supply
"""

# IMPORTS #####################################################################

from __future__ import absolute_import

import quantities as pq

import instruments as ik
from instruments.tests import expected_protocol

# TESTS #######################################################################


def test_channel():
    inst = ik.keithley.Keithley6220.open_test()
    assert inst.channel[0] == inst


def test_current():
    with expected_protocol(
        ik.keithley.Keithley6220,
        [
            "SOUR:CURR?",
            "SOUR:CURR {:e}".format(0.05)
        ],
        [
            "0.1",
        ]
    ) as inst:
        assert inst.current == 100 * pq.milliamp
        assert inst.current_min == -105 * pq.milliamp
        assert inst.current_max == +105 * pq.milliamp
        inst.current = 50 * pq.milliamp


def test_disable():
    with expected_protocol(
        ik.keithley.Keithley6220,
        [
            "SOUR:CLE:IMM"
        ],
        []
    ) as inst:
        inst.disable()
