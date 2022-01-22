#!/usr/bin/env python
"""
Module containing tests for the abstract electrometer class
"""

# IMPORTS ####################################################################


import pytest

import instruments as ik
from instruments.tests import expected_protocol


# TESTS ######################################################################


@pytest.fixture
def em(monkeypatch):
    """Patch and return electrometer class for direct access of metaclass."""
    inst = ik.abstract_instruments.Electrometer
    monkeypatch.setattr(inst, "__abstractmethods__", set())
    return inst


def test_electrometer_mode(em):
    """Get / set mode to ensure the abstract property exists."""
    with expected_protocol(em, [], []) as inst:
        _ = inst.mode
        inst.mode = 42


def test_electrometer_unit(em):
    """Get unit to ensure the abstract property exists."""
    with expected_protocol(em, [], []) as inst:
        _ = inst.unit


def test_electrometer_trigger_mode(em):
    """Get / set trigger mode to ensure the abstract property exists."""
    with expected_protocol(em, [], []) as inst:
        _ = inst.trigger_mode
        inst.trigger_mode = 42


def test_electrometer_input_range(em):
    """Get / set input range to ensure the abstract property exists."""
    with expected_protocol(em, [], []) as inst:
        _ = inst.input_range
        inst.input_range = 42


def test_electrometer_zero_check(em):
    """Get / set zero check to ensure the abstract property exists."""
    with expected_protocol(em, [], []) as inst:
        _ = inst.zero_check
        inst.zero_check = 42


def test_electrometer_zero_correct(em):
    """Get / set zero correct to ensure the abstract property exists."""
    with expected_protocol(em, [], []) as inst:
        _ = inst.zero_correct
        inst.zero_correct = 42


def test_electrometer_fetch(em):
    """Raise NotImplementedError for fetch method."""
    with expected_protocol(em, [], []) as inst:
        with pytest.raises(NotImplementedError):
            inst.fetch()


def test_electrometer_read_measurements(em):
    """Raise NotImplementedError for read_measurements method."""
    with expected_protocol(em, [], []) as inst:
        with pytest.raises(NotImplementedError):
            inst.read_measurements()
