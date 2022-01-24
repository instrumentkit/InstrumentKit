#!/usr/bin/env python
"""
Module containing tests for the abstract optical spectrum analyzer class
"""

# IMPORTS ####################################################################


import pytest

import instruments as ik
from instruments.tests import expected_protocol


# TESTS ######################################################################


@pytest.fixture
def osa(monkeypatch):
    """Patch and return Optical Spectrum Analyzer class for access."""
    inst = ik.abstract_instruments.OpticalSpectrumAnalyzer
    monkeypatch.setattr(inst, "__abstractmethods__", set())
    return inst


@pytest.fixture
def osc(monkeypatch):
    """Patch and return OSAChannel class for access."""
    inst = ik.abstract_instruments.OpticalSpectrumAnalyzer.Channel
    monkeypatch.setattr(inst, "__abstractmethods__", set())
    return inst


# OPTICAL SPECTRUM ANALYZER CLASS #


def test_osa_channel(osa):
    """Get channel: ensure existence."""
    with expected_protocol(osa, [], []) as inst:
        with pytest.raises(NotImplementedError):
            _ = inst.channel


def test_osa_start_wl(osa):
    """Get / set start wavelength: ensure existence."""
    with expected_protocol(osa, [], []) as inst:
        with pytest.raises(NotImplementedError):
            _ = inst.start_wl
        with pytest.raises(NotImplementedError):
            inst.start_wl = 42


def test_osa_stop_wl(osa):
    """Get / set stop wavelength: ensure existence."""
    with expected_protocol(osa, [], []) as inst:
        with pytest.raises(NotImplementedError):
            _ = inst.stop_wl
        with pytest.raises(NotImplementedError):
            inst.stop_wl = 42


def test_osa_bandwidth(osa):
    """Get / set bandwidth: ensure existence."""
    with expected_protocol(osa, [], []) as inst:
        with pytest.raises(NotImplementedError):
            _ = inst.bandwidth
        with pytest.raises(NotImplementedError):
            inst.bandwidth = 42


def test_osa_start_sweep(osa):
    """Start sweep: ensure existence."""
    with expected_protocol(osa, [], []) as inst:
        with pytest.raises(NotImplementedError):
            inst.start_sweep()


# OSAChannel #


def test_osa_channel_wavelength(osc):
    """Channel wavelength method: ensure existence."""
    inst = osc()
    with pytest.raises(NotImplementedError):
        inst.wavelength()


def test_osa_channel_data(osc):
    """Channel data method: ensure existence."""
    inst = osc()
    with pytest.raises(NotImplementedError):
        inst.data()
