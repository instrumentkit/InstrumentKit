#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing tests for the Qubitekk CC1
"""

# IMPORTS ####################################################################

from __future__ import absolute_import

from nose.tools import raises
import quantities as pq

import instruments as ik
from instruments.tests import expected_protocol, make_name_test, unit_eq

# TESTS ######################################################################


def test_cc1_count():
    with expected_protocol(
        ik.qubitekk.CC1,
        [
            "COUN:C1?"
        ],
        [
            "20"
        ],
        sep="\n"
    ) as cc:
        assert cc.channel[0].count == 20.0


def test_cc1_window():
    with expected_protocol(
        ik.qubitekk.CC1,
        [
            "WIND?",
            ":WIND 7"
        ],
        [
            "2",
            ""
        ],
        sep="\n"
    ) as cc:
        unit_eq(cc.window, pq.Quantity(2, "ns"))
        cc.window = 7


@raises(ValueError)
def test_cc1_window_error():
    with expected_protocol(
        ik.qubitekk.CC1,
        [
            ":WIND 10"
        ],
        [
            ""
        ],
        sep="\n"
    ) as cc:
        cc.window = 10


def test_cc1_delay():
    with expected_protocol(
        ik.qubitekk.CC1,
        [
            "DELA?",
            ":DELA 2"
        ],
        [
            "8",
            ""
        ],
        sep="\n"
    ) as cc:
        unit_eq(cc.delay, pq.Quantity(8, "ns"))
        cc.delay = 2


@raises(ValueError)
def test_cc1_delay_error1():
    with expected_protocol(
        ik.qubitekk.CC1,
        [
            ":DELA -1"
        ],
        [
            ""
        ],
        sep="\n"
    ) as cc:
        cc.delay = -1


@raises(ValueError)
def test_cc1_delay_error2():
    with expected_protocol(
        ik.qubitekk.CC1,
        [
            ":DELA 1"
        ],
        [
            ""
        ],
        sep="\n"
    ) as cc:
        cc.delay = 1


def test_cc1_dwell():
    with expected_protocol(
        ik.qubitekk.CC1,
        [
            "DWEL?",
            "FIRM?",
            ":DWEL 2"
        ],
        [
            "8",
            "v2.01"
            ""
        ],
        sep="\n"
    ) as cc:
        unit_eq(cc.dwell_time, pq.Quantity(8, "s"))
        cc.dwell_time = 2


@raises(ValueError)
def test_cc1_dwell_time_error():
    with expected_protocol(
        ik.qubitekk.CC1,
        [
            ":DWEL -1"
        ],
        [
            ""
        ],
        sep="\n"
    ) as cc:
        cc.dwell_time = -1


def test_cc1_firmware():
    with expected_protocol(
        ik.qubitekk.CC1,
        [
            "FIRM?"
        ],
        [
            "blo"
        ],
        sep="\n"
    ) as cc:
        assert cc.firmware == "blo"


def test_cc1_gate_new_firmware():
    with expected_protocol(
        ik.qubitekk.CC1,
        [
            "GATE?",
            ":GATE:ON",
            ":GATE:OFF"

        ],
        [
            "ON",
            "v2.10",
            "",
            ""
        ],
        sep="\n"
    ) as cc:
        assert cc.gate is True
        cc.gate = True
        cc.gate = False


def test_cc1_gate_old_firmware():
    with expected_protocol(
        ik.qubitekk.CC1v2001,
        [
            "GATE?",
            ":GATE 1",
            ":GATE 0"

        ],
        [
            "1",
            "v2.001",
            "",
            ""
        ],
        sep="\n"
    ) as cc:
        assert cc.gate is True
        cc.gate = True
        cc.gate = False



@raises(TypeError)
def test_cc1_gate_error():
    with expected_protocol(
        ik.qubitekk.CC1,
        [
            ":GATE blo"
        ],
        [
            ""
        ],
        sep="\n"
    ) as cc:
        cc.gate = "blo"


def test_cc1_subtract_new_firmware():
    with expected_protocol(
        ik.qubitekk.CC1,
        [
            "SUBT?",
            ":SUBT:ON",
            ":SUBT:OFF"

        ],
        [
            "ON",
            "v2.010",
            "",
            ""
        ],
        sep="\n"
    ) as cc:
        assert cc.subtract is True
        cc.subtract = True
        cc.subtract = False


@raises(TypeError)
def test_cc1_subtract_error():
    with expected_protocol(
        ik.qubitekk.CC1,
        [
            ":SUBT blo"

        ],
        [
            ""
        ],
        sep="\n"
    ) as cc:
        cc.subtract = "blo"


def test_cc1_trigger():
    with expected_protocol(
        ik.qubitekk.CC1,
        [
            "TRIG?",
            ":TRIG:MODE CONT",
            ":TRIG:MODE STOP"
        ],
        [
            "MODE STOP",
            "",
            ""
        ],
        sep="\n"
    ) as cc:
        assert cc.trigger is ik.qubitekk.TriggerMode.start_stop
        cc.trigger = ik.qubitekk.TriggerMode.continuous
        cc.trigger = ik.qubitekk.TriggerMode.start_stop


@raises(ValueError)
def test_cc1_trigger_error():
    with expected_protocol(
        ik.qubitekk.CC1,
        [
            ":TRIG blo"

        ],
        [
            ""
        ],
        sep="\n"
    ) as cc:
        cc.trigger = "blo"


def test_cc1_clear():
    with expected_protocol(
        ik.qubitekk.CC1,
        [
            "CLEA"

        ],
        [
            ""
        ],
        sep="\n"
    ) as cc:
        cc.clear_counts()