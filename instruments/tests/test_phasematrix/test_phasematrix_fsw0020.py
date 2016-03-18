#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for the Phasematrix FSW0020
"""

# IMPORTS #####################################################################

from __future__ import absolute_import

import quantities as pq

import instruments as ik
from instruments.tests import expected_protocol
from instruments.units import mHz, dBm, cBm

# TESTS #######################################################################


def test_reset():
    with expected_protocol(
        ik.phasematrix.PhaseMatrixFSW0020,
        [
            "0E."
        ],
        []
    ) as inst:
        inst.reset()


def test_frequency():
    with expected_protocol(
        ik.phasematrix.PhaseMatrixFSW0020,
        [
            "04.",
            "0C{:012X}.".format(int((10 * pq.GHz).rescale(mHz).magnitude))
        ],
        [
            "00E8D4A51000"
        ]
    ) as inst:
        assert inst.frequency == 1 * pq.GHz
        inst.frequency = 10 * pq.GHz


def test_power():
    with expected_protocol(
        ik.phasematrix.PhaseMatrixFSW0020,
        [
            "0D.",
            "03{:04X}.".format(int((10 * dBm).rescale(cBm).magnitude))
        ],
        [
            "-064"
        ]
    ) as inst:
        assert inst.power == -10 * dBm
        inst.power = 10 * dBm


def test_blanking():
    with expected_protocol(
        ik.phasematrix.PhaseMatrixFSW0020,
        [
            "05{:02X}.".format(1),
            "05{:02X}.".format(0)
        ],
        []
    ) as inst:
        inst.blanking = True
        inst.blanking = False


def test_ref_output():
    with expected_protocol(
        ik.phasematrix.PhaseMatrixFSW0020,
        [
            "08{:02X}.".format(1),
            "08{:02X}.".format(0)
        ],
        []
    ) as inst:
        inst.ref_output = True
        inst.ref_output = False


def test_output():
    with expected_protocol(
        ik.phasematrix.PhaseMatrixFSW0020,
        [
            "0F{:02X}.".format(1),
            "0F{:02X}.".format(0)
        ],
        []
    ) as inst:
        inst.output = True
        inst.output = False


def test_pulse_modulation():
    with expected_protocol(
        ik.phasematrix.PhaseMatrixFSW0020,
        [
            "09{:02X}.".format(1),
            "09{:02X}.".format(0)
        ],
        []
    ) as inst:
        inst.pulse_modulation = True
        inst.pulse_modulation = False


def test_am_modulation():
    with expected_protocol(
        ik.phasematrix.PhaseMatrixFSW0020,
        [
            "0A{:02X}.".format(1),
            "0A{:02X}.".format(0)
        ],
        []
    ) as inst:
        inst.am_modulation = True
        inst.am_modulation = False
