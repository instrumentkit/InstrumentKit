#!/usr/bin/env python
"""
Module containing tests for the Lakeshore 370
"""

# IMPORTS ####################################################################

import pytest

import instruments as ik
from instruments.units import ureg as u
from instruments.tests import expected_protocol

# TESTS ######################################################################

# pylint: disable=redefined-outer-name,protected-access

# PYTEST FIXTURES FOR INITIALIZATION #


@pytest.fixture
def init():
    """Returns the command the instrument sends at initaliation."""
    return "IEEE 3,0"


# TEST SENSOR CLASS #


def test_lakeshore370_channel_init(init):
    """
    Test initialization of channel class.
    """
    with expected_protocol(
        ik.lakeshore.Lakeshore370,
        [init],
        [],
    ) as lsh:
        channel = lsh.channel[7]
        assert channel._parent is lsh
        assert channel._idx == 8


def test_lakeshore370_channel_resistance(init):
    """
    Receive a unitful resistance from a channel.
    """
    with expected_protocol(
        ik.lakeshore.Lakeshore370,
        [init, "RDGR? 1"],
        ["100."],
    ) as lsh:
        assert lsh.channel[0].resistance == u.Quantity(100, u.ohm)
