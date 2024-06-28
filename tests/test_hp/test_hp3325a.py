#!/usr/bin/env python
"""
Unit tests for the HP 3325a function generator
"""

# IMPORTS #####################################################################

import time

import pytest
from instruments.units import ureg as u
import instruments as ik
from tests import expected_protocol


# TESTS #######################################################################

# pylint: disable=protected-access


@pytest.fixture(autouse=True)
def time_mock(mocker):
    """Mock out time to speed up."""
    return mocker.patch.object(time, "sleep", return_value=None)


def test_hp3325a_high_voltage():
    with expected_protocol(
        ik.hp.hp3325a.HP3325a,
        [
            "IHV",
        ],
        ["HV0"],
        sep="\r\n",
    ) as fcngen:
        assert not fcngen.high_voltage

    with expected_protocol(
        ik.hp.hp3325a.HP3325a,
        [
            "IHV",
        ],
        ["HV1"],
        sep="\r\n",
    ) as fcngen:
        assert fcngen.high_voltage


def test_hp3325a_phase():
    with expected_protocol(
        ik.hp.hp3325a.HP3325a,
        [
            "IPH",
        ],
        ["PH10DE"],
        sep="\r\n",
    ) as fcngen:
        assert fcngen.phase == u.Quantity(10, "deg")


def test_hp3325a_amplitude():
    with expected_protocol(
        ik.hp.hp3325a.HP3325a,
        [
            "IAM",
        ],
        ["AM1.2VO"],
        sep="\r\n",
    ) as fcngen:
        assert fcngen.amplitude == u.Quantity(1.2, "V")


def test_hp3325a_frequency():
    with expected_protocol(
        ik.hp.hp3325a.HP3325a,
        [
            "IFR",
        ],
        ["FR1000.0HZ"],
        sep="\r\n",
    ) as fcngen:
        assert fcngen.frequency == u.Quantity(1000, "Hz")


def test_hp3325a_offset():
    with expected_protocol(
        ik.hp.hp3325a.HP3325a,
        [
            "IOF",
        ],
        ["OF0.123VO"],
        sep="\r\n",
    ) as fcngen:
        assert fcngen.offset == u.Quantity(0.123, "V")


def test_hp3325a_commands():
    with expected_protocol(
        ik.hp.hp3325a.HP3325a,
        [
            "AC", "AP", "IER"
        ],
        ["ER0"],
        sep="\r\n",
    ) as fcngen:
        fcngen.amplitude_calibration()
        fcngen.assign_zero_phase()
        fcngen.query_error()
