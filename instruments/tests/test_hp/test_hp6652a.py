#!/usr/bin/env python
"""
Unit tests for the HP 6652a single output power supply
"""

# IMPORTS #####################################################################

import pytest

import instruments as ik
from instruments.tests import expected_protocol

# TESTS #######################################################################


def test_name():
    with expected_protocol(
        ik.hp.HP6652a, ["*IDN?"], ["FOO,BAR,AAA,BBBB"], sep="\n"
    ) as hp:
        assert hp.name == "FOO BAR"


def test_mode():
    """Raise NotImplementedError when called."""
    with expected_protocol(ik.hp.HP6652a, [], [], sep="\n") as hp:
        with pytest.raises(NotImplementedError):
            _ = hp.mode
        with pytest.raises(NotImplementedError):
            hp.mode = 42


def test_reset():
    with expected_protocol(ik.hp.HP6652a, ["OUTP:PROT:CLE"], [], sep="\n") as hp:
        hp.reset()


def test_display_text():
    with expected_protocol(
        ik.hp.HP6652a, ['DISP:TEXT "TEST"', 'DISP:TEXT "TEST AAAAAAAAAA"'], []
    ) as psu:
        assert psu.display_text("TEST") == "TEST"
        assert psu.display_text("TEST AAAAAAAAAAAAAAAA") == "TEST AAAAAAAAAA"


def test_channel():
    with expected_protocol(ik.hp.HP6652a, [], [], sep="\n") as hp:
        assert hp.channel[0] == hp
        assert len(hp.channel) == 1
