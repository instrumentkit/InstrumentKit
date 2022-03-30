#!/usr/bin/env python
"""
Module containing tests for the abstract signal generator channel class
"""

# IMPORTS ####################################################################


import pytest

import instruments as ik


# TESTS ######################################################################


@pytest.fixture
def sgc(monkeypatch):
    """Patch and return SGChannel for direct access of metaclass."""
    inst = ik.abstract_instruments.signal_generator.SGChannel
    monkeypatch.setattr(inst, "__abstractmethods__", set())
    return inst


def test_sg_channel_frequency(sgc):
    """Get / set frequency: Ensure existence."""
    inst = sgc()
    _ = inst.frequency
    inst.frequency = 42


def test_sg_channel_power(sgc):
    """Get / set power: Ensure existence."""
    inst = sgc()
    _ = inst.power
    inst.power = 42


def test_sg_channel_phase(sgc):
    """Get / set phase: Ensure existence."""
    inst = sgc()
    _ = inst.phase
    inst.phase = 42


def test_sg_channel_output(sgc):
    """Get / set output: Ensure existence."""
    inst = sgc()
    _ = inst.output
    inst.output = 4
