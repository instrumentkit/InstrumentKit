#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for the Phasematrix FSW0020
"""

# IMPORTS #####################################################################


import pytest

from instruments.units import ureg as u

import instruments as ik
from instruments.tests import expected_protocol

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
                "0C{:012X}.".format(int((10 * u.GHz).to(u.mHz).magnitude))
            ],
            [
                "00E8D4A51000"
            ]
    ) as inst:
        assert inst.frequency == 1.0000000000000002 * u.GHz
        inst.frequency = 10 * u.GHz


def test_power():
    with expected_protocol(
            ik.phasematrix.PhaseMatrixFSW0020,
            [
                "0D.",
                "03{:04X}.".format(int(u.Quantity(10, u.dBm).to(u.cBm).magnitude))
            ],
            [
                "-064"
            ]
    ) as inst:
        assert inst.power == u.Quantity(-10, u.dBm)
        inst.power = u.Quantity(10, u.dBm)


def test_phase():
    """Raise NotImplementedError when phase is set / got."""
    with expected_protocol(
            ik.phasematrix.PhaseMatrixFSW0020,
            [
            ],
            [
            ]
    ) as inst:
        with pytest.raises(NotImplementedError):
            _ = inst.phase
        with pytest.raises(NotImplementedError):
            inst.phase = 42


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
        with pytest.raises(NotImplementedError):
            _ = inst.blanking


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
        with pytest.raises(NotImplementedError):
            _ = inst.ref_output


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
        with pytest.raises(NotImplementedError):
            _ = inst.output


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
        with pytest.raises(NotImplementedError):
            _ = inst.pulse_modulation


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
        with pytest.raises(NotImplementedError):
            _ = inst.am_modulation
