#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# __init__.py: Tests for Thorlabs-brand instruments.
#
# © 2014-2016 Steven Casagrande (scasagrande@galvant.ca).
#
# This file is a part of the InstrumentKit project.
# Licensed under the AGPL version 3.
#
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
#

# IMPORTS ####################################################################

import instruments as ik
from instruments.tests import expected_protocol, make_name_test, unit_eq
from nose.tools import raises
from flufl.enum import IntEnum
import quantities as pq

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
            ">",
            "freq=10.0",
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
            ">",
            "mode=1",
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


@raises(ValueError)
def test_lcc25_mode_invalid2():
    with expected_protocol(
        ik.thorlabs.LCC25,
        [],
        []
    ) as lcc:
        blo = IntEnum("blo", "beep boop bop")
        lcc.mode = blo[0]


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
            ">",
            "enable=1",
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
            ">",
            "extern=1",
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
            ">",
            "remote=1",
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
            ">",
            "volt1=10.0",
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
            ">",
            "volt2=10.0",
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
            ">",
            "min=10.0",
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
            ">",
            "max=10.0",
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
            ">",
            "dwell=10",
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
            ">",
            "increment=10.0",
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


def test_sc10_name():
    with expected_protocol(
        ik.thorlabs.SC10,
        [
            "id?"
        ],
        [
            "id?",
            "bloopbloop",
            ">"
        ],
        sep="\r"
    ) as sc:
        assert sc.name == "bloopbloop"


def test_sc10_enable():
    with expected_protocol(
        ik.thorlabs.SC10,
        [
            "ens?",
            "ens=1"
        ],
        [
            "ens?",
            "0",
            ">",
            "ens=1",
            ">"
        ],
        sep="\r"
    ) as sc:
        assert sc.enable == False
        sc.enable = True


@raises(TypeError)
def test_sc10_enable_invalid():
    with expected_protocol(
        ik.thorlabs.SC10,
        [],
        [],
        sep="\r"
    ) as sc:
        sc.enable = 10


def test_sc10_repeat():
    with expected_protocol(
        ik.thorlabs.SC10,
        [
            "rep?",
            "rep=10"
        ],
        [
            "rep?",
            "20",
            ">",
            "rep=10",
            ">"
        ],
        sep="\r"
    ) as sc:
        assert sc.repeat == 20
        sc.repeat = 10


@raises(ValueError)
def test_sc10_repeat_invalid():
    with expected_protocol(
        ik.thorlabs.SC10,
        [],
        [],
        sep="\r"
    ) as sc:
        sc.repeat = -1


def test_sc10_mode():
    with expected_protocol(
        ik.thorlabs.SC10,
        [
            "mode?",
            "mode=2"
        ],
        [
            "mode?",
            "1",
            ">",
            "mode=2",
            ">"
        ],
        sep="\r"
    ) as sc:
        assert sc.mode == ik.thorlabs.SC10.Mode.manual
        sc.mode = ik.thorlabs.SC10.Mode.auto


@raises(ValueError)
def test_sc10_mode_invalid():
    with expected_protocol(
        ik.thorlabs.SC10,
        [],
        [],
        sep="\r"
    ) as sc:
        sc.mode = "blo"


@raises(ValueError)
def test_sc10_mode_invalid2():
    with expected_protocol(
        ik.thorlabs.SC10,
        [],
        [],
        sep="\r"
    ) as sc:
        blo = IntEnum("blo", "beep boop bop")
        sc.mode = blo[0]


def test_sc10_trigger():
    with expected_protocol(
        ik.thorlabs.SC10,
        [
            "trig?",
            "trig=1"
        ],
        [
            "trig?",
            "0",
            ">",
            "trig=1",
            ">"
        ],
        sep="\r"
    ) as sc:
        assert sc.trigger == 0
        sc.trigger = 1


def test_sc10_out_trigger():
    with expected_protocol(
        ik.thorlabs.SC10,
        [
            "xto?",
            "xto=1"
        ],
        [
            "xto?",
            "0",
            ">",
            "xto=1",
            ">"
        ],
        sep="\r"
    ) as sc:
        assert sc.out_trigger == 0
        sc.out_trigger = 1


def test_sc10_open_time():
    with expected_protocol(
        ik.thorlabs.SC10,
        [
            "open?",
            "open=10"
        ],
        [
            "open?",
            "20",
            ">",
            "open=10",
            ">"
        ],
        sep="\r"
    ) as sc:
        unit_eq(sc.open_time, pq.Quantity(20, "ms"))
        sc.open_time = 10


def test_sc10_shut_time():
    with expected_protocol(
        ik.thorlabs.SC10,
        [
            "shut?",
            "shut=10"
        ],
        [
            "shut?",
            "20",
            ">",
            "shut=10",
            ">"
        ],
        sep="\r"
    ) as sc:
        unit_eq(sc.shut_time, pq.Quantity(20, "ms"))
        sc.shut_time = 10.0


def test_sc10_baud_rate():
    with expected_protocol(
        ik.thorlabs.SC10,
        [
            "baud?",
            "baud=1"
        ],
        [
            "baud?",
            "0",
            ">",
            "baud=1",
            ">"
        ],
        sep="\r"
    ) as sc:
        assert sc.baud_rate == 9600
        sc.baud_rate = 115200


@raises(ValueError)
def test_sc10_baud_rate_error():
    with expected_protocol(
        ik.thorlabs.SC10,
        [],
        [],
        sep="\r"
    ) as sc:
        sc.baud_rate = 115201


def test_sc10_closed():
    with expected_protocol(
        ik.thorlabs.SC10,
        [
            "closed?"
        ],
        [
            "closed?",
            "1",
            ">"
        ],
        sep="\r"
    ) as sc:
        assert sc.closed


def test_sc10_interlock():
    with expected_protocol(
        ik.thorlabs.SC10,
        [
            "interlock?"
        ],
        [
            "interlock?",
            "1",
            ">"
        ],
        sep="\r"
    ) as sc:
        assert sc.interlock


def test_sc10_default():
    with expected_protocol(
        ik.thorlabs.SC10,
        [
            "default"
        ],
        [
            "default",
            "1",
            ">"
        ],
        sep="\r"
    ) as sc:
        assert sc.default()


def test_sc10_save():
    with expected_protocol(
        ik.thorlabs.SC10,
        [
            "savp"
        ],
        [
            "savp",
            "1",
            ">"
        ],
        sep="\r"
    ) as sc:
        assert sc.save()


def test_sc10_save_mode():
    with expected_protocol(
        ik.thorlabs.SC10,
        [
            "save"
        ],
        [
            "save",
            "1",
            ">"
        ],
        sep="\r"
    ) as sc:
        assert sc.save_mode()


def test_sc10_restore():
    with expected_protocol(
        ik.thorlabs.SC10,
        [
            "resp"
        ],
        [
            "resp",
            "1",
            ">"
        ],
        sep="\r"
    ) as sc:
        assert sc.restore()


def test_tc200_name():
    with expected_protocol(
        ik.thorlabs.TC200,
        [
            "*idn?"
        ],
        [
            "*idn?",
            "bloopbloop",
            ">"
        ],
        sep="\r"
    ) as tc:
        assert tc.name() == "bloopbloop"


def test_tc200_mode():
    with expected_protocol(
        ik.thorlabs.TC200,
        [
            "stat?",
            "stat?",
            "mode=cycle"
        ],
        [
            "stat?",
            "0",
            ">",
            "stat?",
            "2",
            ">",
            "mode=cycle",
            ">"
        ],
        sep="\r"
    ) as tc:
        assert tc.mode == tc.Mode.normal
        assert tc.mode == tc.Mode.cycle
        tc.mode = ik.thorlabs.TC200.Mode.cycle


@raises(TypeError)
def test_tc200_mode_error():
    with expected_protocol(
        ik.thorlabs.TC200,
        [],
        [],
        sep="\r"
    ) as tc:
        tc.mode = "blo"


@raises(TypeError)
def test_tc200_mode_error2():
    with expected_protocol(
        ik.thorlabs.TC200,
        [],
        [],
        sep="\r"
    ) as tc:
        blo = IntEnum("blo", "beep boop bop")
        tc.mode = blo.beep


def test_tc200_enable():
    with expected_protocol(
        ik.thorlabs.TC200,
        [
            "stat?",
            "stat?",
            "ens",
            "stat?",
            "ens"
        ],
        [
            "stat?",
            "54",
            ">",

            "stat?",
            "54",
            ">",
            "ens",
            ">",

            "stat?",
            "55",
            ">",
            "ens",
            ">"
        ],
        sep="\r"
    ) as tc:
        assert tc.enable == 0
        tc.enable = True
        tc.enable = False


@raises(TypeError)
def test_tc200_enable_type():
    with expected_protocol(
        ik.thorlabs.TC200,
        [],
        [],
        sep="\r"
    ) as tc:
        tc.enable = "blo"


def test_tc200_temperature():
    with expected_protocol(
        ik.thorlabs.TC200,
        [
            "tact?",
        ],
        [
            "tact?",
            "30 C",
            ">",
        ],
        sep="\r"
    ) as tc:
        assert tc.temperature == 30.0 * pq.degC


def test_tc200_temperature_set():
    with expected_protocol(
        ik.thorlabs.TC200,
        [
            "tset?",
            "tmax?",
            "tset=40.0"
        ],
        [
            "tset?",
            "30 C",
            ">",
            "tmax?",
            "250",
            ">",
            "tset=40.0",
            ">"
        ],
        sep="\r"
    ) as tc:
        assert tc.temperature_set == 30.0 * pq.degC
        tc.temperature_set = 40 * pq.degC


@raises(ValueError)
def test_tc200_temperature_range():
    with expected_protocol(
        ik.thorlabs.TC200,
        [
            "tmax?"
        ],
        [
            "tmax?",
            "40",
            ">"
        ],
        sep="\r"
    ) as tc:
        tc.temperature_set = 50 * pq.degC


def test_tc200_pid():
    with expected_protocol(
        ik.thorlabs.TC200,
        [
            "pid?",
            "pgain=2"
        ],
        [
            "pid?",
            "2 0 220",
            ">",
            "pgain=2",
            ">"
        ],
        sep="\r"
    ) as tc:
        assert tc.p == 2
        tc.p = 2

    with expected_protocol(
        ik.thorlabs.TC200,
        [
            "pid?",
            "igain=0"
        ],
        [
            "pid?",
            "2 0 220",
            ">",
            "igain=0",
            ">"
        ],
        sep="\r"
    ) as tc:
        assert tc.i == 0
        tc.i = 0

    with expected_protocol(
        ik.thorlabs.TC200,
        [
            "pid?",
            "dgain=220"
        ],
        [
            "pid?",
            "2 0 220",
            ">",
            "dgain=220",
            ">"
        ],
        sep="\r"
    ) as tc:
        assert tc.d == 220
        tc.d = 220

    with expected_protocol(
        ik.thorlabs.TC200,
        [
            "pid?",
            "pgain=2",
            "igain=0",
            "dgain=220"
        ],
        [
            "pid?",
            "2 0 220",
            ">",
            "pgain=2",
            ">",
            "igain=0",
            ">",
            "dgain=220",
            ">"
        ],
        sep="\r"
    ) as tc:
        assert tc.pid == [2, 0, 220]
        tc.pid = (2, 0, 220)


@raises(ValueError)
def test_tc200_pmin():
    with expected_protocol(
        ik.thorlabs.TC200,
        [
            "pgain=-1"
        ],
        [
            "pgain=-1",
            ">"
        ],
        sep="\r"
    ) as tc:
        tc.p = -1


@raises(ValueError)
def test_tc200_pmax():
    with expected_protocol(
        ik.thorlabs.TC200,
        [
            "pgain=260"
        ],
        [
            "pgain=260",
            ">"
        ],
        sep="\r"
    ) as tc:
        tc.p = 260


@raises(ValueError)
def test_tc200_imin():
    with expected_protocol(
        ik.thorlabs.TC200,
        [
            "igain=-1"
        ],
        [
            "igain=-1",
            ">"
        ],
        sep="\r"
    ) as tc:
        tc.i = -1


@raises(ValueError)
def test_tc200_imax():
    with expected_protocol(
        ik.thorlabs.TC200,
        [
            "igain=260"
        ],
        [
            "igain=260",
            ">"
        ],
        sep="\r"
    ) as tc:
        tc.i = 260


@raises(ValueError)
def test_tc200_dmin():
    with expected_protocol(
        ik.thorlabs.TC200,
        [
            "dgain=-1"
        ],
        [
            "dgain=-1",
            ">"
        ],
        sep="\r"
    ) as tc:
        tc.d = -1


@raises(ValueError)
def test_tc200_dmax():
    with expected_protocol(
        ik.thorlabs.TC200,
        [
            "dgain=260"
        ],
        [
            "dgain=260",
            ">"
        ],
        sep="\r"
    ) as tc:
        tc.d = 260


def test_tc200_degrees():
    with expected_protocol(
        ik.thorlabs.TC200,
        [
            "stat?",
            "stat?",
            "stat?",
            "unit=c",
            "unit=f",
            "unit=k"
        ],
        [
            "stat?",
            "44",
            ">",
            "stat?",
            "54",
            ">",
            "stat?",
            "0",
            ">",
            "unit=c",
            ">",
            "unit=f",
            ">",
            "unit=k",
            ">"
        ],
        sep="\r"
    ) as tc:
        assert str(tc.degrees).split(" ")[1] == "K"
        assert str(tc.degrees).split(" ")[1] == "degC"
        assert tc.degrees == pq.degF

        tc.degrees = pq.degC
        tc.degrees = pq.degF
        tc.degrees = pq.degK


@raises(TypeError)
def test_tc200_degrees_invalid():

    with expected_protocol(
        ik.thorlabs.TC200,
        [],
        [],
        sep="\r"
    ) as tc:
        tc.degrees = "blo"


def test_tc200_sensor():
    with expected_protocol(
        ik.thorlabs.TC200,
        [
            "sns?",
            "sns=ptc100"
        ],
        [
            "sns?",
            "Sensor = NTC10K, Beta = 5600",
            ">",
            "sns=ptc100",
            ">"
        ],
        sep="\r"
    ) as tc:
        assert tc.sensor == tc.Sensor.ntc10k
        tc.sensor = tc.Sensor.ptc100


@raises(ValueError)
def test_tc200_sensor_error():
    with expected_protocol(
        ik.thorlabs.TC200,
        [],
        []
    ) as tc:
        tc.sensor = "blo"


@raises(ValueError)
def test_tc200_sensor_error2():
    with expected_protocol(
        ik.thorlabs.TC200,
            [],
            []
    ) as tc:
        blo = IntEnum("blo", "beep boop bop")
        tc.sensor = blo.beep


def test_tc200_beta():
    with expected_protocol(
        ik.thorlabs.TC200,
        [
            "beta?",
            "beta=2000"
        ],
        [
            "beta?",
            "5600",
            ">",
            "beta=2000",
            ">"
        ],
        sep="\r"
    ) as tc:
        assert tc.beta == 5600
        tc.beta = 2000


@raises(ValueError)
def test_tc200_beta_min():
    with expected_protocol(
        ik.thorlabs.TC200,
        [
            "beta=200"
        ],
        [
            "beta=200",
            ">"
        ],
        sep="\r"
    ) as tc:
        tc.beta = 200


@raises(ValueError)
def test_tc200_beta_max():
    with expected_protocol(
        ik.thorlabs.TC200,
        [
            "beta=20000"
        ],
        [
            "beta=20000",
            ">"
        ],
        sep="\r"
    ) as tc:
        tc.beta = 20000


def test_tc200_max_power():
    with expected_protocol(
        ik.thorlabs.TC200,
        [
            "pmax?",
            "pmax=12.0"
        ],
        [
            "pmax?",
            "15.0",
            ">",
            "pmax=12.0",
            ">"
        ],
        sep="\r"
    ) as tc:
        assert tc.max_power == 15.0 * pq.W
        tc.max_power = 12 * pq.W


@raises(ValueError)
def test_tc200_power_min():
    with expected_protocol(
        ik.thorlabs.TC200,
        [
            "PMAX=-2"
        ],
        [
            "PMAX=-2",
            ">"
        ],
        sep="\r"
    ) as tc:
        tc.max_power = -1


@raises(ValueError)
def test_tc200_power_max():
    with expected_protocol(
        ik.thorlabs.TC200,
        [
            "PMAX=20000"
        ],
        [
            "PMAX=20000",
            ">"
        ],
        sep="\r"
    ) as tc:
        tc.max_power = 20000


def test_tc200_max_temperature():
    with expected_protocol(
        ik.thorlabs.TC200,
        [
            "tmax?",
            "tmax=180.0"
        ],
        [
            "tmax?",
            "200.0",
            ">",
            "tmax=180.0",
            ">"
        ],
        sep="\r"
    ) as tc:
        assert tc.max_temperature == 200.0 * pq.degC
        tc.max_temperature = 180 * pq.degC


@raises(ValueError)
def test_tc200_temp_min():
    with expected_protocol(
        ik.thorlabs.TC200,
        [
            "TMAX=-2"
        ],
        [
            "TMAX=-2",
            ">"
        ],
        sep="\r"
    ) as tc:
        tc.max_temperature = -1


@raises(ValueError)
def test_tc200_temp_max():
    with expected_protocol(
        ik.thorlabs.TC200,
        [
            "TMAX=20000"
        ],
        [
            "TMAX=20000",
            ">"
        ],
        sep="\r"
    ) as tc:
        tc.max_temperature = 20000
