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
from instruments.tests import expected_protocol, unit_eq


# TESTS ######################################################################


def test_cc1_count():
    with expected_protocol(
        ik.qubitekk.CC1,
        [
            ":ACKN OF",
            "FIRM?",
            "COUN:C1?"
        ],
        [
            "",
            "Firmware v2.010",
            "20"
        ],
        sep="\n"
    ) as cc:
        assert cc.channel[0].count == 20.0


def test_cc1_window():
    with expected_protocol(
        ik.qubitekk.CC1,
        [
            ":ACKN OF",
            "FIRM?",
            "WIND?",
            ":WIND 7"
        ],
        [
            "",
            "Firmware v2.010",
            "2",
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
            ":ACKN OF",
            "FIRM?",
            ":WIND 10"
        ],
        [
            "",
            "Firmware v2.010"
        ],
        sep="\n"
    ) as cc:
        cc.window = 10


def test_cc1_delay():
    with expected_protocol(
        ik.qubitekk.CC1,
        [
            ":ACKN OF",
            "FIRM?",
            "DELA?",
            ":DELA 2"
        ],
        [
            "",
            "Firmware v2.010",
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
            ":ACKN OF",
            "FIRM?",
            ":DELA -1"
        ],
        [
            "",
            "Firmware v2.010"
        ],
        sep="\n"
    ) as cc:
        cc.delay = -1


@raises(ValueError)
def test_cc1_delay_error2():
    with expected_protocol(
        ik.qubitekk.CC1,
        [
            ":ACKN OF",
            "FIRM?",
            ":DELA 1"
        ],
        [
            "",
            "Firmware v2.010"
        ],
        sep="\n"
    ) as cc:
        cc.delay = 1


def test_cc1_dwell_old_firmware():
    with expected_protocol(
        ik.qubitekk.CC1,
        [
            ":ACKN OF",
            "FIRM?",
            "DWEL?",
            ":DWEL 2"
        ],
        [
            "Unknown Command",
            "Firmware v2.001",
            "8000",
            ""
        ],
        sep="\n"
    ) as cc:
        unit_eq(cc.dwell_time, pq.Quantity(8, "s"))
        cc.dwell_time = 2


def test_cc1_dwell_new_firmware():
    with expected_protocol(
        ik.qubitekk.CC1,
        [
            ":ACKN OF",
            "FIRM?",
            "DWEL?",
            ":DWEL 2"
        ],
        [
            "",
            "Firmware v2.010",
            "8"
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
            ":ACKN OF",
            "FIRM?",
            ":DWEL -1"
        ],
        [
            "",
            "Firmware v2.010"
        ],
        sep="\n"
    ) as cc:
        cc.dwell_time = -1


def test_cc1_firmware():
    with expected_protocol(
        ik.qubitekk.CC1,
        [
            ":ACKN OF",
            "FIRM?"
        ],
        [
            "",
            "Firmware v2.010"
        ],
        sep="\n"
    ) as cc:
        assert cc.firmware == (2, 10, 0)


def test_cc1_firmware_2():
    with expected_protocol(
        ik.qubitekk.CC1,
        [
            ":ACKN OF",
            "FIRM?"
        ],
        [
            "Unknown Command",
            "Firmware v2"
        ],
        sep="\n"
    ) as cc:
        assert cc.firmware == (2, 0, 0)


def test_cc1_firmware_3():
    with expected_protocol(
        ik.qubitekk.CC1,
        [
            ":ACKN OF",
            "FIRM?"
        ],
        [
            "Unknown Command",
            "Firmware v2.010.1"
        ],
        sep="\n"
    ) as cc:
        assert cc.firmware == (2, 10, 1)


def test_cc1_firmware_repeat_query():
    with expected_protocol(
        ik.qubitekk.CC1,
        [
            ":ACKN OF",
            "FIRM?",
            "FIRM?"
        ],
        [
            "Unknown Command",
            "Unknown",
            "Firmware v2.010"
        ],
        sep="\n"
    ) as cc:
        assert cc.firmware == (2, 10, 0)


def test_cc1_gate_new_firmware():
    with expected_protocol(
        ik.qubitekk.CC1,
        [
            ":ACKN OF",
            "FIRM?",
            "GATE?",
            ":GATE:ON",
            ":GATE:OFF"

        ],
        [
            "",
            "Firmware v2.010",
            "ON"
        ],
    ) as cc:
        assert cc.gate is True
        cc.gate = True
        cc.gate = False


def test_cc1_gate_old_firmware():
    with expected_protocol(
        ik.qubitekk.CC1,
        [
            ":ACKN OF",
            "FIRM?",
            "GATE?",
            ":GATE 1",
            ":GATE 0"

        ],
        [
            "Unknown Command",
            "Firmware v2.001",
            "1",
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
            ":ACKN OF",
            "FIRM?",
            ":GATE blo"
        ],
        [
            "",
            "Firmware v2.010"
        ],
        sep="\n"
    ) as cc:
        cc.gate = "blo"


def test_cc1_subtract_new_firmware():
    with expected_protocol(
        ik.qubitekk.CC1,
        [
            ":ACKN OF",
            "FIRM?",
            "SUBT?",
            ":SUBT:ON",
            ":SUBT:OFF"

        ],
        [
            "",
            "Firmware v2.010",
            "ON",
            ":SUBT:OFF"
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
            ":ACKN OF",
            "FIRM?",
            ":SUBT blo"

        ],
        [
            "",
            "Firmware v2.010"
        ],
        sep="\n"
    ) as cc:
        cc.subtract = "blo"


def test_cc1_trigger_mode():  # pylint: disable=redefined-variable-type
    with expected_protocol(
        ik.qubitekk.CC1,
        [
            ":ACKN OF",
            "FIRM?",
            "TRIG?",
            ":TRIG:MODE CONT",
            ":TRIG:MODE STOP"
        ],
        [
            "",
            "Firmware v2.010",
            "MODE STOP"
        ],
        sep="\n"
    ) as cc:
        assert cc.trigger_mode is cc.TriggerMode.start_stop
        cc.trigger_mode = cc.TriggerMode.continuous
        cc.trigger_mode = cc.TriggerMode.start_stop


def test_cc1_trigger_mode_old_firmware():  # pylint: disable=redefined-variable-type
    with expected_protocol(
        ik.qubitekk.CC1,
        [
            ":ACKN OF",
            "FIRM?",
            "TRIG?",
            ":TRIG 0",
            ":TRIG 1"
        ],
        [
            "Unknown Command",
            "Firmware v2.001",
            "1",
            "",
            ""
        ],
        sep="\n"
    ) as cc:
        assert cc.trigger_mode == cc.TriggerMode.start_stop
        cc.trigger_mode = cc.TriggerMode.continuous
        cc.trigger_mode = cc.TriggerMode.start_stop


@raises(ValueError)
def test_cc1_trigger_mode_error():
    with expected_protocol(
        ik.qubitekk.CC1,
        [
            ":ACKN OF",
            "FIRM?"
        ],
        [
            "",
            "Firmware v2.010"
        ],
        sep="\n"
    ) as cc:
        cc.trigger_mode = "blo"


def test_cc1_clear():
    with expected_protocol(
        ik.qubitekk.CC1,
        [
            ":ACKN OF",
            "FIRM?",
            "CLEA"
        ],
        [
            "",
            "Firmware v2.010"
        ],
        sep="\n"
    ) as cc:
        cc.clear_counts()


def test_acknowledge():
    with expected_protocol(
        ik.qubitekk.CC1,
        [
            ":ACKN OF",
            "FIRM?",
            ":ACKN ON",
            "CLEA",
            ":ACKN OF",
            "CLEA"
        ],
        [
            "",
            "Firmware v2.010",
            "CLEA",
            ":ACKN OF"

        ],
        sep="\n"
    ) as cc:
        assert not cc.acknowledge
        cc.acknowledge = True
        assert cc.acknowledge
        cc.clear_counts()
        cc.acknowledge = False
        assert not cc.acknowledge
        cc.clear_counts()


@raises(NotImplementedError)
def test_acknowledge_notimplementederror():
    with expected_protocol(
        ik.qubitekk.CC1,
        [
            ":ACKN OF",
            "FIRM?"
        ],
        [
            "Unknown Command",
            "Firmware v2.001"

        ],
        sep="\n"
    ) as cc:
        cc.acknowledge = True


@raises(NotImplementedError)
def test_acknowledge_not_implemented_error():  # pylint: disable=protected-access
    with expected_protocol(
        ik.qubitekk.CC1,
        [
            ":ACKN OF",
            "FIRM?"
        ],
        [
            "Unknown Command",
            "Firmware v2.001"

        ],
        sep="\n"
    ) as cc:
        cc.acknowledge = True
