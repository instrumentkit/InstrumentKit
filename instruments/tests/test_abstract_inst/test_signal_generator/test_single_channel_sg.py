#!/usr/bin/env python
"""
Module containing tests for the abstract signal generator class
"""

# IMPORTS ####################################################################


import pytest

import instruments as ik
from instruments.tests import expected_protocol


# TESTS ######################################################################


@pytest.fixture
def scsg(monkeypatch):
    """Patch and return signal generator for direct access of metaclass."""
    inst = ik.abstract_instruments.signal_generator.SingleChannelSG
    monkeypatch.setattr(inst, "__abstractmethods__", set())
    return inst


def test_signal_generator_channel(scsg):
    """Get channel: Ensure existence."""
    with expected_protocol(scsg, [], []) as inst:
        assert inst.channel[0] == inst
