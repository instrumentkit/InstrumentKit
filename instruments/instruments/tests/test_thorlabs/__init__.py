#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# __init__.py: Tests for Thorlabs-brand instruments.
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

import cStringIO as StringIO
import quantities as pq

## TESTS ######################################################################

def test_lcc25_frequency():
    with expected_protocol(
        ik.thorlabs.LCC25,
        "freq?\rfreq=10.0\r",
        "\r>20\r"
    ) as lcc:
        unit_eq(lcc.frequency, pq.Quantity(20, "Hz"))
        lcc.frequency = 10.0

def test_lcc25_mode():
    with expected_protocol(
        ik.thorlabs.LCC25,
        "mode?\rmode=1\r",
        "\r>2\r"
    ) as lcc:
        assert lcc.mode == ik.thorlabs.LCC25.Mode.voltage2
        lcc.mode = ik.thorlabs.LCC25.Mode.voltage1

def test_lcc25_enable():
    with expected_protocol(
        ik.thorlabs.LCC25,
        "enable?\renable=1\r",
        ">\r>0\r"
    ) as lcc:
        assert lcc.enable == False
        lcc.enable = True

def test_lcc25_extern():
    with expected_protocol(
        ik.thorlabs.LCC25,
        "extern?\rextern=1\r",
        ">\r>0\r"
    ) as lcc:
        assert lcc.extern == False
        lcc.extern = True

def test_lcc25_remote():
    with expected_protocol(
        ik.thorlabs.LCC25,
        "remote?\rremote=1\r",
        ">\r>0\r"
    ) as lcc:
        assert lcc.remote == False
        lcc.remote = True

def test_lcc25_voltage1():
    with expected_protocol(
        ik.thorlabs.LCC25,
        "volt1?\rvolt1=10.0\r",
        "\r20\r"
    ) as lcc:
        unit_eq(lcc.voltage1, pq.Quantity(20, "V"))
        lcc.voltage1 = 10.0

def test_lcc25_voltage2():
    with expected_protocol(
        ik.thorlabs.LCC25,
        "volt2?\rvolt2=10.0\r",
        "\r20\r"
    ) as lcc:
        unit_eq(lcc.voltage2, pq.Quantity(20, "V"))
        lcc.voltage2 = 10.0

def test_lcc25_minvoltage():
    with expected_protocol(
        ik.thorlabs.LCC25,
        "min?\rmin=10.0\r",
        "\r>20\r"
    ) as lcc:
        unit_eq(lcc.min_voltage, pq.Quantity(20, "V"))
        lcc.min_voltage = 10.0

def test_lcc25_dwell():
    with expected_protocol(
        ik.thorlabs.LCC25,
        "dwell?\rdwell=10\r",
        "\r>20\r"
    ) as lcc:
        unit_eq(lcc.dwell, pq.Quantity(20, "ms"))
        lcc.dwell = 10

def test_lcc25_increment():
    with expected_protocol(
        ik.thorlabs.LCC25,
        "increment?\rincrement=10.0\r",
        "\r>20\r"
    ) as lcc:
        unit_eq(lcc.increment, pq.Quantity(20, "V"))
        lcc.increment = 10.0

def test_lcc25_default():
    with expected_protocol(
        ik.thorlabs.LCC25,
        "default\r",
        "\r>\r"
    ) as lcc:
        lcc.default()

def test_lcc25_save():
    with expected_protocol(
        ik.thorlabs.LCC25,
        "save\r",
        "\r>\r"
    ) as lcc:
        lcc.save()

def test_lcc25_save_settings():
    with expected_protocol(
        ik.thorlabs.LCC25,
        "set=2\r",
        "\r>\r"
    ) as lcc:
        lcc.set_settings(2)

def test_lcc25_get_settings():
    with expected_protocol(
        ik.thorlabs.LCC25,
        "get=2\r",
        "\r>\r"
    ) as lcc:
        lcc.get_settings(2)

def test_lcc25_test_mode():
    with expected_protocol(
        ik.thorlabs.LCC25,
        "test\r",
        "\r>\r"
    ) as lcc:
        lcc.test_mode()

def test_sc10_enable():
    with expected_protocol(
        ik.thorlabs.SC10,
        "ens?\rens=1\r",
        "\r>0\r>\r"
    ) as sc:
        assert sc.enable == 0
        sc.enable = 1

def test_sc10_repeat():
    with expected_protocol(
        ik.thorlabs.SC10,
        "rep?\rrep=10\r",
        "\r>20\r>\r"
    ) as sc:
        assert sc.repeat == 20
        sc.repeat = 10

def test_sc10_mode():
    with expected_protocol(
        ik.thorlabs.SC10,
        "mode?\rmode=2\r",
        "\r>1\r>\r"
    ) as sc:
        assert sc.mode == ik.thorlabs.SC10.Mode.manual
        sc.mode = ik.thorlabs.SC10.Mode.auto

def test_sc10_trigger():
    with expected_protocol(
        ik.thorlabs.SC10, 
        "trig?\rtrig=1\r",
        "\r>0\r>\r"
    ) as sc:
        assert sc.trigger == 0
        sc.trigger = 1

def test_sc10_out_trigger():
    with expected_protocol(
        ik.thorlabs.SC10,
        "xto?\rxto=1\r",
        "\r>0\r>\r"
    ) as sc:
        assert sc.out_trigger == 0
        sc.out_trigger = 1

def test_sc10_open_time():
    with expected_protocol(
        ik.thorlabs.SC10,
        "open?\ropen=10\r",
        "\r20\r>\r"
    ) as sc:
        unit_eq(sc.open_time, pq.Quantity(20, "ms"))
        sc.open_time = 10.0

def test_sc10_shut_time():
    with expected_protocol(
        ik.thorlabs.SC10,
        "shut?\rshut=10\r",
        "\r20\r>\r"
    ) as sc:
        unit_eq(sc.shut_time, pq.Quantity(20, "ms"))
        sc.shut_time = 10.0

'''
unit test for baud rate should be done very carefully, testing to change the 
baud rate to something other then the current baud rate will cause the 
connection to be unreadable.
def test_sc10_baud_rate():
    with expected_protocol(ik.thorlabs.SC10, "baud?\rbaud=1\r", "\r>0\r>\r") as sc:
        assert sc.baud_rate ==0
        sc.baud_rate = 1
'''

def test_sc10_closed():
    with expected_protocol(
        ik.thorlabs.SC10,
        "closed?\r",
        "\r1\r"
    ) as sc:
        assert sc.closed

def test_sc10_interlock():
    with expected_protocol(
        ik.thorlabs.SC10,
        "interlock?\r",
        "\r1\r"
    ) as sc:
        assert sc.interlock

def test_sc10_default():
    with expected_protocol(
        ik.thorlabs.SC10,
        "default\r",
        "\r1\r"
    ) as sc:
        assert sc.default()

def test_sc10_save():
    with expected_protocol(
        ik.thorlabs.SC10,
        "savp\r",
        "\r1\r"
    ) as sc:
        assert sc.save()

def test_sc10_save_mode():
    with expected_protocol(
        ik.thorlabs.SC10,
        "save\r",
        "\r1\r"
    ) as sc:
        assert sc.save_mode()

def test_sc10_restore():
    with expected_protocol(
        ik.thorlabs.SC10,
        "resp\r",
        "\r1\r"
    ) as sc:
        assert sc.restore()

