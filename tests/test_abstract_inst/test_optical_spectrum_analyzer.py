#!/usr/bin/env python
"""
Module containing tests for the abstract optical spectrum analyzer class
"""

# IMPORTS ####################################################################


import pytest

import instruments as ik
from tests import expected_protocol

# TESTS ######################################################################


@pytest.fixture
def osa(monkeypatch):
    """Patch and return Optical Spectrum Analyzer class for access."""
    inst = ik.abstract_instruments.OpticalSpectrumAnalyzer
    chan = ik.abstract_instruments.OpticalSpectrumAnalyzer.Channel
    monkeypatch.setattr(inst, "__abstractmethods__", set())
    monkeypatch.setattr(chan, "__abstractmethods__", set())
    return inst


# OPTICAL SPECTRUM ANALYZER CLASS #


def test_osa_channel(osa):
    """Get channel: ensure existence."""
    with expected_protocol(osa, [], []) as inst:
        ch = inst.channel[0]
        assert isinstance(ch, ik.abstract_instruments.OpticalSpectrumAnalyzer.Channel)


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


@pytest.mark.parametrize("num_ch", [1, 5])
def test_osa_channel_wavelength(osa, num_ch):
    """Channel wavelength method: ensure existence."""
    with expected_protocol(osa, [], []) as inst:
        inst._channel_count = num_ch
        ch = inst.channel[0]
        with pytest.raises(NotImplementedError):
            ch.wavelength()
        with pytest.raises(NotImplementedError):
            inst.wavelength()  # single channel instrument


@pytest.mark.parametrize("num_ch", [1, 5])
def test_osa_channel_data(osa, num_ch):
    """Channel data method: ensure existence."""
    with expected_protocol(osa, [], []) as inst:
        inst._channel_count = num_ch
        ch = inst.channel[0]
        with pytest.raises(NotImplementedError):
            ch.data()
        with pytest.raises(NotImplementedError):
            inst.data()  # single channel instrument
