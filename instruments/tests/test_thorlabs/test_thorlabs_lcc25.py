#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing tests for the Thorlabs LCC25
"""

# IMPORTS ####################################################################

from __future__ import absolute_import

from nose.tools import raises
import quantities as pq

import instruments as ik
from instruments.tests import expected_protocol, unit_eq

# TESTS ######################################################################


def test_lcc25_name():
    with expected_protocol(
        ik.thorlabs.LCC25,
        [
            "*idn?"
        ],
        [
            "*idn?",
            "bloopbloop",
            ">"
        ],
        sep="\r"
    ) as lcc:
        name = lcc.name
        assert name == "bloopbloop", "got {} expected bloopbloop".format(name)


def test_lcc25_frequency():
    with expected_protocol(
        ik.thorlabs.LCC25,
        [
            "freq?",
            "freq=10.0"
        ],
        [
            "freq?",
            "20",
            ">freq=10.0",
            ">"
        ],
        sep="\r"
    ) as lcc:
        unit_eq(lcc.frequency, pq.Quantity(20, "Hz"))
        lcc.frequency = 10.0


@raises(ValueError)
def test_lcc25_frequency_lowlimit():
    with expected_protocol(
        ik.thorlabs.LCC25,
        [
            "freq=0.0"
        ],
        [
            "freq=0.0",
            ">"
        ],
        sep="\r"
    ) as lcc:
        lcc.frequency = 0.0


@raises(ValueError)
def test_lcc25_frequency_highlimit():
    with expected_protocol(
        ik.thorlabs.LCC25,
        [
            "freq=160.0"
        ],
        [
            "freq=160.0",
            ">"
        ],
        sep="\r"
    ) as lcc:
        lcc.frequency = 160.0


def test_lcc25_mode():
    with expected_protocol(
        ik.thorlabs.LCC25,
        [
            "mode?",
            "mode=1"
        ],
        [
            "mode?",
            "2",
            ">mode=1",
            ">"
        ],
        sep="\r"
    ) as lcc:
        assert lcc.mode == ik.thorlabs.LCC25.Mode.voltage2
        lcc.mode = ik.thorlabs.LCC25.Mode.voltage1


@raises(ValueError)
def test_lcc25_mode_invalid():
    with expected_protocol(
        ik.thorlabs.LCC25,
        [],
        []
    ) as lcc:
        lcc.mode = "blo"


def test_lcc25_enable():
    with expected_protocol(
        ik.thorlabs.LCC25,
        [
            "enable?",
            "enable=1"
        ],
        [
            "enable?",
            "0",
            ">enable=1",
            ">"
        ],
        sep="\r"
    ) as lcc:
        assert lcc.enable is False
        lcc.enable = True


@raises(TypeError)
def test_lcc25_enable_invalid_type():
    with expected_protocol(
        ik.thorlabs.LCC25,
        [],
        []
    ) as lcc:
        lcc.enable = "blo"


def test_lcc25_extern():
    with expected_protocol(
        ik.thorlabs.LCC25,
        [
            "extern?",
            "extern=1"
        ],
        [
            "extern?",
            "0",
            ">extern=1",
            ">"
        ],
        sep="\r"
    ) as lcc:
        assert lcc.extern is False
        lcc.extern = True


@raises(TypeError)
def test_tc200_extern_invalid_type():
    with expected_protocol(
        ik.thorlabs.LCC25,
        [],
        []
    ) as tc:
        tc.extern = "blo"


def test_lcc25_remote():
    with expected_protocol(
        ik.thorlabs.LCC25,
        [
            "remote?",
            "remote=1"
        ],
        [
            "remote?",
            "0",
            ">remote=1",
            ">"
        ],
        sep="\r"
    ) as lcc:
        assert lcc.remote is False
        lcc.remote = True


@raises(TypeError)
def test_tc200_remote_invalid_type():
    with expected_protocol(
        ik.thorlabs.LCC25,
        [],
        []
    ) as tc:
        tc.remote = "blo"


def test_lcc25_voltage1():
    with expected_protocol(
        ik.thorlabs.LCC25,
        [
            "volt1?",
            "volt1=10.0"
        ],
        [
            "volt1?",
            "20",
            ">volt1=10.0",
            ">"
        ],
        sep="\r"
    ) as lcc:
        unit_eq(lcc.voltage1, pq.Quantity(20, "V"))
        lcc.voltage1 = 10.0


def test_check_cmd():
    assert ik.thorlabs.thorlabs_utils.check_cmd("blo") == 1
    assert ik.thorlabs.thorlabs_utils.check_cmd("CMD_NOT_DEFINED") == 0
    assert ik.thorlabs.thorlabs_utils.check_cmd("CMD_ARG_INVALID") == 0


def test_lcc25_voltage2():
    with expected_protocol(
        ik.thorlabs.LCC25,
        [
            "volt2?",
            "volt2=10.0",
        ],
        [
            "volt2?",
            "20",
            ">volt2=10.0",
            ">"
        ],
        sep="\r"
    ) as lcc:
        unit_eq(lcc.voltage2, pq.Quantity(20, "V"))
        lcc.voltage2 = 10.0


def test_lcc25_minvoltage():
    with expected_protocol(
        ik.thorlabs.LCC25,
        [
            "min?",
            "min=10.0"
        ],
        [
            "min?",
            "20",
            ">min=10.0",
            ">"
        ],
        sep="\r"
    ) as lcc:
        unit_eq(lcc.min_voltage, pq.Quantity(20, "V"))
        lcc.min_voltage = 10.0


def test_lcc25_maxvoltage():
    with expected_protocol(
        ik.thorlabs.LCC25,
        [
            "max?",
            "max=10.0"
        ],
        [
            "max?",
            "20",
            ">max=10.0",
            ">"
        ],
        sep="\r"
    ) as lcc:
        unit_eq(lcc.max_voltage, pq.Quantity(20, "V"))
        lcc.max_voltage = 10.0


def test_lcc25_dwell():
    with expected_protocol(
        ik.thorlabs.LCC25,
        [
            "dwell?",
            "dwell=10"
        ],
        [
            "dwell?",
            "20",
            ">dwell=10",
            ">"
        ],
        sep="\r"
    ) as lcc:
        unit_eq(lcc.dwell, pq.Quantity(20, "ms"))
        lcc.dwell = 10


@raises(ValueError)
def test_lcc25_dwell_positive():
    with expected_protocol(
        ik.thorlabs.LCC25,
        [
            "dwell=-10"
        ],
        [
            "dwell=-10",
            ">"
        ],
        sep="\r"
    ) as lcc:
        lcc.dwell = -10


def test_lcc25_increment():
    with expected_protocol(
        ik.thorlabs.LCC25,
        [
            "increment?",
            "increment=10.0"
        ],
        [
            "increment?",
            "20",
            ">increment=10.0",
            ">"
        ],
        sep="\r"
    ) as lcc:
        unit_eq(lcc.increment, pq.Quantity(20, "V"))
        lcc.increment = 10.0


@raises(ValueError)
def test_lcc25_increment_positive():
    with expected_protocol(
        ik.thorlabs.LCC25,
        [
            "increment=-10"
        ],
        [
            "increment=-10",
            ">"
        ],
        sep="\r"
    ) as lcc:
        lcc.increment = -10


def test_lcc25_default():
    with expected_protocol(
        ik.thorlabs.LCC25,
        [
            "default"
        ],
        [
            "default",
            "1",
            ">"
        ],
        sep="\r"
    ) as lcc:
        lcc.default()


def test_lcc25_save():
    with expected_protocol(
        ik.thorlabs.LCC25,
        [
            "save"
        ],
        [
            "save",
            "1",
            ">"
        ],
        sep="\r"
    ) as lcc:
        lcc.save()


def test_lcc25_set_settings():
    with expected_protocol(
        ik.thorlabs.LCC25,
        [
            "set=2"
        ],
        [
            "set=2",
            "1",
            ">"
        ],
        sep="\r"
    ) as lcc:
        lcc.set_settings(2)


@raises(ValueError)
def test_lcc25_set_settings_invalid():
    with expected_protocol(
        ik.thorlabs.LCC25,
        [],
        [],
        sep="\r"
    ) as lcc:
        lcc.set_settings(5)


def test_lcc25_get_settings():
    with expected_protocol(
        ik.thorlabs.LCC25,
        [
            "get=2"
        ],
        [
            "get=2",
            "1",
            ">"
        ],
        sep="\r"
    ) as lcc:
        lcc.get_settings(2)


@raises(ValueError)
def test_lcc25_get_settings_invalid():
    with expected_protocol(
        ik.thorlabs.LCC25,
        [],
        [],
        sep="\r"
    ) as lcc:
        lcc.get_settings(5)


def test_lcc25_test_mode():
    with expected_protocol(
        ik.thorlabs.LCC25,
        [
            "test"
        ],
        [
            "test",
            "1",
            ">"
        ],
        sep="\r"
    ) as lcc:
        lcc.test_mode()


@raises(TypeError)
def test_lcc25_remote_invalid_type():
    with expected_protocol(
        ik.thorlabs.LCC25,
        [],
        []
    ) as lcc:
        lcc.remote = "blo"


@raises(TypeError)
def test_lcc25_extern_invalid_type():
    with expected_protocol(
        ik.thorlabs.LCC25,
        [],
        []
    ) as lcc:
        lcc.extern = "blo"
