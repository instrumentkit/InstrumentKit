#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# __init__.py: Tests for Qubitekk-brand instruments.
##
# © 2014 Steven Casagrande (scasagrande@galvant.ca).
#
# This file is a part of the InstrumentKit project.
# Licensed under the AGPL version 3.
##
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
##

## IMPORTS ####################################################################

import instruments as ik
from instruments.tests import expected_protocol, make_name_test, unit_eq

from cStringIO import StringIO
import quantities as pq

from nose.tools import raises


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
            ":DWEL 2"
        ],
        [
            "8",
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


def test_cc1_gate():
    with expected_protocol(
        ik.qubitekk.CC1,
        [
            "GATE?",
            ":GATE:ON",
            ":GATE:OFF",
            ":GATE:ON",
            ":GATE 1",
            ":GATE:OFF",
            ":GATE 0"

        ],
        [
            "1",
            "",
            "",
            "Unknown command",
            "Unknown command",
            ""
        ],
        sep="\n"
    ) as cc:
        assert cc.gate is True
        cc.gate = True
        cc.gate = False
        cc.gate = True
        cc.gate = False


@raises(ValueError)
def test_cc1_gate_error1():
    with expected_protocol(
        ik.qubitekk.CC1,
        [
            ":GATE 2"
        ],
        [
            ""
        ],
        sep="\n"
    ) as cc:
        cc.gate = 2


@raises(TypeError)
def test_cc1_gate_error2():
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