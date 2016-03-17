#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for the SRS 345 function generator
"""

# IMPORTS #####################################################################

from __future__ import absolute_import

import quantities as pq
import numpy as np

import instruments as ik
from instruments.tests import expected_protocol

# TESTS #######################################################################


def test_amplitude():
    with expected_protocol(
        ik.srs.SRS345,
        [
            "AMPL?",
            "AMPL 0.1VP",
            "AMPL 0.1VR"
        ],
        [
            "1.234VP",
        ]
    ) as inst:
        np.testing.assert_array_equal(
            inst.amplitude, (1.234 * pq.V, inst.VoltageMode.peak_to_peak)
        )
        inst.amplitude = 0.1 * pq.V
        inst.amplitude = (0.1 * pq.V, inst.VoltageMode.rms)


def test_frequency():
    with expected_protocol(
        ik.srs.SRS345,
        [
            "FREQ?",
            "FREQ {:e}".format(0.1),
        ],
        [
            "1.234",
        ]
    ) as inst:
        assert inst.frequency == 1.234 * pq.Hz
        inst.frequency = 0.1 * pq.Hz


def test_function():
    with expected_protocol(
        ik.srs.SRS345,
        [
            "FUNC?",
            "FUNC 0"
        ],
        [
            "1",
        ]
    ) as inst:
        assert inst.function == inst.Function.square
        inst.function = inst.Function.sinusoid


def test_offset():
    with expected_protocol(
        ik.srs.SRS345,
        [
            "OFFS?",
            "OFFS {:e}".format(0.1),
        ],
        [
            "1.234",
        ]
    ) as inst:
        assert inst.offset == 1.234 * pq.V
        inst.offset = 0.1 * pq.V


def test_phase():
    with expected_protocol(
        ik.srs.SRS345,
        [
            "PHSE?",
            "PHSE {:e}".format(0.1),
        ],
        [
            "1.234",
        ]
    ) as inst:
        assert inst.phase == 1.234 * pq.degree
        inst.phase = 0.1 * pq.degree
