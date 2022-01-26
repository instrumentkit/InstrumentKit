#!/usr/bin/env python
"""
Module containing tests for the abstract power supply class
"""

# IMPORTS ####################################################################


import pytest

import instruments as ik
from instruments.tests import expected_protocol


# TESTS ######################################################################


@pytest.fixture
def ps(monkeypatch):
    """Patch and return Power Supply class for access."""
    inst = ik.abstract_instruments.PowerSupply
    monkeypatch.setattr(inst, "__abstractmethods__", set())
    return inst


@pytest.fixture
def ps_ch(monkeypatch):
    """Patch and return Power Supply Channel class for access."""
    inst = ik.abstract_instruments.PowerSupply.Channel
    monkeypatch.setattr(inst, "__abstractmethods__", set())
    return inst


# POWER SUPPLY #


def test_power_supply_channel(ps):
    """Get channel: ensure existence."""
    with expected_protocol(ps, [], []) as inst:
        with pytest.raises(NotImplementedError):
            _ = inst.channel


def test_power_supply_voltage(ps):
    """Get / set voltage: ensure existence."""
    with expected_protocol(ps, [], []) as inst:
        _ = inst.voltage
        inst.voltage = 42


def test_power_supply_current(ps):
    """Get / set current: ensure existence."""
    with expected_protocol(ps, [], []) as inst:
        _ = inst.current
        inst.current = 42


# POWER SUPPLY CHANNEL #


def test_power_supply_channel_mode(ps_ch):
    """Get / set channel mode: ensure existence."""
    inst = ps_ch()
    _ = inst.mode
    inst.mode = 42


def test_power_supply_channel_voltage(ps_ch):
    """Get / set channel voltage: ensure existence."""
    inst = ps_ch()
    _ = inst.voltage
    inst.voltage = 42


def test_power_supply_channel_current(ps_ch):
    """Get / set channel current: ensure existence."""
    inst = ps_ch()
    _ = inst.current
    inst.current = 42


def test_power_supply_channel_output(ps_ch):
    """Get / set channel output: ensure existence."""
    inst = ps_ch()
    _ = inst.output
    inst.output = 42
