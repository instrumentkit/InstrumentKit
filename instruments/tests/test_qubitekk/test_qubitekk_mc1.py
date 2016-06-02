#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing tests for the Qubitekk MC1
"""

# IMPORTS ####################################################################

from __future__ import absolute_import

from nose.tools import raises

import instruments as ik
from instruments.tests import expected_protocol


# TESTS ######################################################################


def test_mc1_setting():
    with expected_protocol(
        ik.qubitekk.MC1,
        [
            "OUTP?",
            ":OUTP 0"
        ],
        [
            "1"
        ],
        sep="\r"
    ) as mc:
        assert mc.setting == 1
        mc.setting = 0


def test_mc1_position():
    with expected_protocol(
        ik.qubitekk.MC1,
        [
            "POSI?"
        ],
        [
            "-100"
        ],
        sep="\r"
    ) as mc:
        assert mc.position == -100


def test_mc1_direction():
    with expected_protocol(
        ik.qubitekk.MC1,
        [
            "DIRE?"
        ],
        [
            "-100"
        ],
        sep="\r"
    ) as mc:
        assert mc.direction == -100


def test_mc1_firmware():
    with expected_protocol(
        ik.qubitekk.MC1,
        [
            "FIRM?"
        ],
        [
            "1.0.1"
        ],
        sep="\r"
    ) as mc:
        assert mc.firmware == (1, 0, 1)


def test_mc1_motor():
    with expected_protocol(
        ik.qubitekk.MC1,
        [
            "MOTO?"
        ],
        [
            "Radio"
        ],
        sep="\r"
    ) as mc:
        assert mc.controller == mc.MotorType.radio


def test_mc1_move_timeout():
    with expected_protocol(
        ik.qubitekk.MC1,
        [
            "TAME?"
        ],
        [
            "200"
        ],
        sep="\r"
    ) as mc:
        assert mc.move_timeout == 200


def test_mc1_range():
    with expected_protocol(
        ik.qubitekk.MC1,
        [],
        [],
        sep="\r"
    ) as mc:
        mc.upper_limit = 200
        mc.lower_limit = 0
        mc.increment = 10
        assert mc.range == range(0, 200, 10)


def test_mc1_is_centering():
    with expected_protocol(
        ik.qubitekk.MC1,
        ["CENT?"],
        ["1"],
        sep="\r"
    ) as mc:
        assert mc.is_centering()


def test_mc1_center():
    with expected_protocol(
        ik.qubitekk.MC1,
        [":CENT"],
        [""],
        sep="\r"
    ) as mc:
        mc.center()


def test_mc1_reset():
    with expected_protocol(
        ik.qubitekk.MC1,
        [":RESE"],
        [""],
        sep="\r"
    ) as mc:
        mc.reset()


def test_mc1_move():
    with expected_protocol(
        ik.qubitekk.MC1,
        [":MOVE 0"],
        [""],
        sep="\r"
    ) as mc:
        mc.move(0)


@raises(ValueError)
def test_mc1_move_value_error():
    with expected_protocol(
        ik.qubitekk.MC1,
        [":MOVE -1000"],
        [""],
        sep="\r"
    ) as mc:
        mc.move(-1000)
