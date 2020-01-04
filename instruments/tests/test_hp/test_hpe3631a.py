#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing tests for the HP E3631A power supply
"""

# IMPORTS #####################################################################

from __future__ import absolute_import

import quantities as pq

import instruments as ik
from instruments.tests import expected_protocol


# TESTS #######################################################################

def test_channel():
    with expected_protocol(
        ik.hp.HPe3631a,
        [
            "SYST:REM",
            "INST:NSEL?",
            "INST:NSEL?",
            "INST:NSEL 2",
            "INST:NSEL?"
        ],
        [
            "1",
            "1",
            "2"
        ]
    ) as inst:
        assert inst.channelid == 1
        assert inst.channel[2] == inst
        assert inst.channelid == 2


def test_channelid():
    with expected_protocol(
        ik.hp.HPe3631a,
        [
            "SYST:REM",  # 0
            "INST:NSEL?",   # 1
            "INST:NSEL 2",  # 2
            "INST:NSEL?"    # 3
        ],
        [
            "1",    # 1
            "2"     # 3
        ]
    ) as inst:
        assert inst.channelid == 1
        inst.channelid = 2
        assert inst.channelid == 2


def test_voltage():
    with expected_protocol(
        ik.hp.HPe3631a,
        [
            "SYST:REM",  # 0
            "SOUR:VOLT? MAX",   # 1
            "SOUR:VOLT? MAX",   # 2
            "SOUR:VOLT? MAX",   # 3.1
            "SOUR:VOLT 3.000000e+00",   # 3.2
            "SOUR:VOLT?",   # 4
            "SOUR:VOLT? MAX",   # 5
            "SOUR:VOLT? MAX"    # 6
        ],
        [
            "6.0",  # 1
            "6.0",  # 2
            "6.0",  # 3.1
            "3.0",  # 4
            "6.0",  # 5
            "6.0"   # 6
        ]
    ) as inst:
        assert inst.voltage_min == 0.0 * pq.volt
        assert inst.voltage_max == 6.0 * pq.volt
        inst.voltage = 3.0 * pq.volt
        assert inst.voltage == 3.0 * pq.volt
        try:
            inst.voltage = -1.0 * pq.volt
        except ValueError:
            pass
        try:
            inst.voltage = 7.0 * pq.volt
        except ValueError:
            pass


def test_current():
    with expected_protocol(
        ik.hp.HPe3631a,
        [
            "SYST:REM",  # 0
            "SOUR:CURR? MIN",   # 1.1
            "SOUR:CURR? MAX",   # 1.2
            "SOUR:CURR? MIN",   # 2.1
            "SOUR:CURR? MAX",   # 2.2
            "SOUR:CURR 2.000000e+00",   # 3
            "SOUR:CURR?",   # 4
            "SOUR:CURR? MIN",   # 5
            "SOUR:CURR? MIN",   # 6.1
            "SOUR:CURR? MAX"    # 6.2
        ],
        [
            "0.0",  # 1.1
            "5.0",  # 1.2
            "0.0",  # 2.1
            "5.0",  # 2.2
            "2.0",  # 4
            "0.0",  # 5
            "0.0",  # 6.1
            "5.0"   # 6.2
        ]
    ) as inst:
        assert inst.current_min == 0.0 * pq.amp
        assert inst.current_max == 5.0 * pq.amp
        inst.current = 2.0 * pq.amp
        assert inst.current == 2.0 * pq.amp
        try:
            inst.current = -1.0 * pq.amp
        except ValueError:
            pass
        try:
            inst.current = 6.0 * pq.amp
        except ValueError:
            pass


def test_voltage_sense():
    with expected_protocol(
        ik.hp.HPe3631a,
        [
            "SYST:REM",  # 0
            "MEAS:VOLT?"   # 1
        ],
        [
            "1.234"  # 1
        ]
    ) as inst:
        assert inst.voltage_sense == 1.234 * pq.volt


def test_current_sense():
    with expected_protocol(
        ik.hp.HPe3631a,
        [
            "SYST:REM",  # 0
            "MEAS:CURR?"   # 1
        ],
        [
            "1.234"  # 1
        ]
    ) as inst:
        assert inst.current_sense == 1.234 * pq.amp
