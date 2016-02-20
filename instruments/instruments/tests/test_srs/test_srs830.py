#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for the SRS 830 lock-in amplifier
"""

# IMPORTS #####################################################################

from __future__ import absolute_import

import quantities as pq
import numpy as np
from nose.tools import raises

import instruments as ik
from instruments.tests import expected_protocol, make_name_test, unit_eq

# TESTS #######################################################################


def test_frequency_source():
    with expected_protocol(
        ik.srs.SRS830,
        [
            "FMOD?",
            "FMOD 0"
        ],
        [
            "1",
        ]
    ) as inst:
        assert inst.frequency_source == inst.FreqSource.internal
        inst.frequency_source = inst.FreqSource.external


def test_frequency():
    with expected_protocol(
        ik.srs.SRS830,
        [
            "FREQ?",
            "FREQ {:e}".format(1000)
        ],
        [
            "12.34",
        ]
    ) as inst:
        assert inst.frequency == 12.34 * pq.Hz
        inst.frequency = 1 * pq.kHz


def test_phase():
    with expected_protocol(
        ik.srs.SRS830,
        [
            "PHAS?",
            "PHAS {:e}".format(10)
        ],
        [
            "-45",
        ]
    ) as inst:
        assert inst.phase == -45 * pq.degrees
        inst.phase = 10 * pq.degrees


def test_amplitude():
    with expected_protocol(
        ik.srs.SRS830,
        [
            "SLVL?",
            "SLVL {:e}".format(1)
        ],
        [
            "0.1",
        ]
    ) as inst:
        assert inst.amplitude == 0.1 * pq.V
        inst.amplitude = 1 * pq.V


def test_input_shield_ground():
    with expected_protocol(
        ik.srs.SRS830,
        [
            "IGND?",
            "IGND 1"
        ],
        [
            "0",
        ]
    ) as inst:
        assert inst.input_shield_ground is False
        inst.input_shield_ground = True


def test_coupling():
    with expected_protocol(
        ik.srs.SRS830,
        [
            "ICPL?",
            "ICPL 0"
        ],
        [
            "1",
        ]
    ) as inst:
        assert inst.coupling == inst.Coupling.dc
        inst.coupling = inst.Coupling.ac


def test_sample_rate():  # sends index of VALID_SAMPLE_RATES
    with expected_protocol(
        ik.srs.SRS830,
        [
            "SRAT?",
            "SRAT?",
            "SRAT {:d}".format(5)
        ],
        [
            "8",
            "14"
        ]
    ) as inst:
        assert inst.sample_rate == 16 * pq.Hz
        assert inst.sample_rate == "trigger"
        inst.sample_rate = 2


def test_buffer_mode():
    with expected_protocol(
        ik.srs.SRS830,
        [
            "SEND?",
            "SEND 1"
        ],
        [
            "0",
        ]
    ) as inst:
        assert inst.buffer_mode == inst.BufferMode.one_shot
        inst.buffer_mode = inst.BufferMode.loop


def test_num_data_points():
    with expected_protocol(
        ik.srs.SRS830,
        [
            "SPTS?"
        ],
        [
            "5",
        ]
    ) as inst:
        assert inst.num_data_points == 5


def test_data_transfer():
    with expected_protocol(
        ik.srs.SRS830,
        [
            "FAST?",
            "FAST 2"
        ],
        [
            "0",
        ]
    ) as inst:
        assert inst.data_transfer is False
        inst.data_transfer = True

