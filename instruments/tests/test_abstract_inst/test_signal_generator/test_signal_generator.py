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
def sg(monkeypatch):
    """Patch and return signal generator for direct access of metaclass."""
    inst = ik.abstract_instruments.signal_generator.SignalGenerator
    monkeypatch.setattr(inst, "__abstractmethods__", set())
    return inst


def test_signal_generator_channel(sg):
    """Get channel: Ensure existence."""
    with expected_protocol(sg, [], []) as inst:
        with pytest.raises(NotImplementedError):
            _ = inst.channel
