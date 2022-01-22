#!/usr/bin/env python
"""
Module containing tests for the abstract multimeter class
"""

# IMPORTS ####################################################################


import pytest

import instruments as ik
from instruments.tests import expected_protocol


# TESTS ######################################################################


@pytest.fixture
def mul(monkeypatch):
    """Patch and return Multimeter class for access."""
    inst = ik.abstract_instruments.Multimeter
    monkeypatch.setattr(inst, "__abstractmethods__", set())
    return inst


def test_multimeter_mode(mul):
    """Get / set mode: ensure existence."""
    with expected_protocol(mul, [], []) as inst:
        _ = inst.mode
        inst.mode = 42


def test_multimeter_trigger_mode(mul):
    """Get / set trigger mode: ensure existence."""
    with expected_protocol(mul, [], []) as inst:
        _ = inst.trigger_mode
        inst.trigger_mode = 42


def test_multimeter_relative(mul):
    """Get / set relative: ensure existence."""
    with expected_protocol(mul, [], []) as inst:
        _ = inst.relative
        inst.relative = 42


def test_multimeter_input_range(mul):
    """Get / set input range: ensure existence."""
    with expected_protocol(mul, [], []) as inst:
        _ = inst.input_range
        inst.input_range = 42


def test_multimeter_measure(mul):
    """Measure: ensure existence."""
    with expected_protocol(mul, [], []) as inst:
        inst.measure("mode")
