#!/usr/bin/env python
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
    with expected_protocol(ik.phasematrix.PhaseMatrixFSW0020, ["0E."], []) as inst:
        inst.reset()


def test_frequency():
    with expected_protocol(
        ik.phasematrix.PhaseMatrixFSW0020,
        ["04.", f"0C{int((10 * u.GHz).to(u.mHz).magnitude):012X}."],
        ["00E8D4A51000"],
    ) as inst:
        assert inst.frequency == 1.0000000000000002 * u.GHz
        inst.frequency = 10 * u.GHz


def test_power():
    with expected_protocol(
        ik.phasematrix.PhaseMatrixFSW0020,
        ["0D.", f"03{int(u.Quantity(10, u.dBm).to(u.cBm).magnitude):04X}."],
        ["-064"],
    ) as inst:
        assert inst.power == u.Quantity(-10, u.dBm)
        inst.power = u.Quantity(10, u.dBm)


def test_phase():
    """Raise NotImplementedError when phase is set / got."""
    with expected_protocol(ik.phasematrix.PhaseMatrixFSW0020, [], []) as inst:
        with pytest.raises(NotImplementedError):
            _ = inst.phase
        with pytest.raises(NotImplementedError):
            inst.phase = 42


def test_blanking():
    with expected_protocol(
        ik.phasematrix.PhaseMatrixFSW0020,
        [f"05{1:02X}.", f"05{0:02X}."],
        [],
    ) as inst:
        inst.blanking = True
        inst.blanking = False
        with pytest.raises(NotImplementedError):
            _ = inst.blanking


def test_ref_output():
    with expected_protocol(
        ik.phasematrix.PhaseMatrixFSW0020,
        [f"08{1:02X}.", f"08{0:02X}."],
        [],
    ) as inst:
        inst.ref_output = True
        inst.ref_output = False
        with pytest.raises(NotImplementedError):
            _ = inst.ref_output


def test_output():
    with expected_protocol(
        ik.phasematrix.PhaseMatrixFSW0020,
        [f"0F{1:02X}.", f"0F{0:02X}."],
        [],
    ) as inst:
        inst.output = True
        inst.output = False
        with pytest.raises(NotImplementedError):
            _ = inst.output


def test_pulse_modulation():
    with expected_protocol(
        ik.phasematrix.PhaseMatrixFSW0020,
        [f"09{1:02X}.", f"09{0:02X}."],
        [],
    ) as inst:
        inst.pulse_modulation = True
        inst.pulse_modulation = False
        with pytest.raises(NotImplementedError):
            _ = inst.pulse_modulation


def test_am_modulation():
    with expected_protocol(
        ik.phasematrix.PhaseMatrixFSW0020,
        [f"0A{1:02X}.", f"0A{0:02X}."],
        [],
    ) as inst:
        inst.am_modulation = True
        inst.am_modulation = False
        with pytest.raises(NotImplementedError):
            _ = inst.am_modulation
