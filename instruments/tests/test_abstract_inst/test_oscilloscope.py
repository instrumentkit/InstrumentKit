#!/usr/bin/env python
"""
Module containing tests for the abstract oscilloscope class
"""

# IMPORTS ####################################################################


import pytest

import instruments as ik
from instruments.tests import expected_protocol


# TESTS ######################################################################


@pytest.fixture
def osc(monkeypatch):
    """Patch and return Oscilloscope class for access."""
    inst = ik.abstract_instruments.Oscilloscope
    monkeypatch.setattr(inst, "__abstractmethods__", set())
    return inst


@pytest.fixture
def osc_ch(monkeypatch):
    """Patch and return OscilloscopeChannel class for access."""
    inst = ik.abstract_instruments.Oscilloscope.Channel
    monkeypatch.setattr(inst, "__abstractmethods__", set())
    return inst


@pytest.fixture
def osc_ds(monkeypatch):
    """Patch and return OscilloscopeDataSource class for access."""
    inst = ik.abstract_instruments.Oscilloscope.DataSource
    monkeypatch.setattr(inst, "__abstractmethods__", set())
    return inst


# OSCILLOSCOPE #


def test_oscilloscope_channel(osc):
    """Get channel: ensure existence."""
    with expected_protocol(osc, [], []) as inst:
        with pytest.raises(NotImplementedError):
            _ = inst.channel


def test_oscilloscope_ref(osc):
    """Get ref: ensure existence."""
    with expected_protocol(osc, [], []) as inst:
        with pytest.raises(NotImplementedError):
            _ = inst.ref


def test_oscilloscope_math(osc):
    """Get math: ensure existence."""
    with expected_protocol(osc, [], []) as inst:
        with pytest.raises(NotImplementedError):
            _ = inst.math


def test_oscilloscope_force_trigger(osc):
    """Force a trigger: ensure existence."""
    with expected_protocol(osc, [], []) as inst:
        with pytest.raises(NotImplementedError):
            inst.force_trigger()


# OSCILLOSCOPE CHANNEL #


def test_oscilloscope_channel_coupling(osc_ch):
    """Get / set channel coupling: ensure existence."""
    inst = osc_ch()
    with pytest.raises(NotImplementedError):
        _ = inst.coupling
    with pytest.raises(NotImplementedError):
        inst.coupling = 42


# OSCILLOSCOPE DATA SOURCE #


def test_oscilloscope_data_source_init(osc_ds):
    """Initialize Oscilloscope Data Source."""
    parent = "parent"
    name = "name"
    inst = osc_ds(parent, name)
    assert inst._parent == parent
    assert inst._name == name
    assert inst._old_dsrc is None


def test_oscilloscope_data_source_name(osc_ds):
    """Get data source name: ensure existence."""
    parent = "parent"
    name = "name"
    inst = osc_ds(parent, name)
    with pytest.raises(NotImplementedError):
        _ = inst.name


def test_oscilloscope_data_source_read_waveform(osc_ds):
    """Read data source waveform: ensure existence."""
    parent = "parent"
    name = "name"
    inst = osc_ds(parent, name)
    with pytest.raises(NotImplementedError):
        inst.read_waveform()
