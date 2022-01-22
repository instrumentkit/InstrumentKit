#!/usr/bin/env python
"""
Module containing tests for the Thorlabs TC200
"""

# IMPORTS ####################################################################


from enum import IntEnum
import pytest
from instruments.units import ureg as u

import instruments as ik
from instruments.tests import expected_protocol

# TESTS ######################################################################


def test_tc200_name():
    with expected_protocol(
        ik.thorlabs.TC200, ["*idn?"], ["*idn?", "bloopbloop", "> "], sep="\r"
    ) as tc:
        assert tc.name() == "bloopbloop"


def test_tc200_mode():
    with expected_protocol(
        ik.thorlabs.TC200,
        ["stat?", "stat?", "mode=cycle"],
        ["stat?", "0 > stat?", "2 >  mode=cycle", "> "],
        sep="\r",
    ) as tc:
        assert tc.mode == tc.Mode.normal
        assert tc.mode == tc.Mode.cycle
        tc.mode = ik.thorlabs.TC200.Mode.cycle


def test_tc200_mode_2():
    with expected_protocol(
        ik.thorlabs.TC200,
        ["mode=normal"],
        ["mode=normal", "Command error CMD_ARG_RANGE_ERR\n", "> "],
        sep="\r",
    ) as tc:
        tc.mode = ik.thorlabs.TC200.Mode.normal


def test_tc200_mode_error():
    with pytest.raises(TypeError), expected_protocol(
        ik.thorlabs.TC200, [], [], sep="\r"
    ) as tc:
        tc.mode = "blo"


def test_tc200_mode_error2():
    with pytest.raises(TypeError), expected_protocol(
        ik.thorlabs.TC200, [], [], sep="\r"
    ) as tc:

        class TestEnum(IntEnum):
            blo = 1
            beep = 2

        tc.mode = TestEnum.blo


def test_tc200_enable():
    with expected_protocol(
        ik.thorlabs.TC200,
        ["stat?", "stat?", "ens", "stat?", "ens"],
        ["stat?", "54 > stat?", "54 > ens", "> stat?", "55 > ens", "> "],
        sep="\r",
    ) as tc:
        assert tc.enable == 0
        tc.enable = True
        tc.enable = False


def test_tc200_enable_type():
    with pytest.raises(TypeError), expected_protocol(
        ik.thorlabs.TC200, [], [], sep="\r"
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
            "> ",
        ],
        sep="\r",
    ) as tc:
        assert tc.temperature == u.Quantity(30.0, u.degC)


def test_tc200_temperature_set():
    with expected_protocol(
        ik.thorlabs.TC200,
        ["tset?", "tmax?", "tset=40"],
        ["tset?", "30 C", "> tmax?", "250", "> tset=40", "> "],
        sep="\r",
    ) as tc:
        assert tc.temperature_set == u.Quantity(30.0, u.degC)
        tc.temperature_set = u.Quantity(40, u.degC)


def test_tc200_temperature_range():
    with pytest.raises(ValueError), expected_protocol(
        ik.thorlabs.TC200, ["tmax?"], ["tmax?", "40", "> "], sep="\r"
    ) as tc:
        tc.temperature_set = u.Quantity(50, u.degC)


def test_tc200_pid():
    with expected_protocol(
        ik.thorlabs.TC200,
        ["pid?", "pgain=2"],
        ["pid?", "2 0 220", "> pgain=2", "> "],
        sep="\r",
    ) as tc:
        assert tc.p == 2
        tc.p = 2

    with expected_protocol(
        ik.thorlabs.TC200,
        ["pid?", "igain=0"],
        ["pid?", "2 0 220", "> igain=0", "> "],
        sep="\r",
    ) as tc:
        assert tc.i == 0
        tc.i = 0

    with expected_protocol(
        ik.thorlabs.TC200,
        ["pid?", "dgain=220"],
        ["pid?", "2 0 220", "> dgain=220", "> "],
        sep="\r",
    ) as tc:
        assert tc.d == 220
        tc.d = 220

    with expected_protocol(
        ik.thorlabs.TC200,
        ["pid?", "pgain=2", "igain=0", "dgain=220"],
        ["pid?", "2 0 220", "> pgain=2", "> igain=0", "> dgain=220", "> "],
        sep="\r",
    ) as tc:
        assert tc.pid == [2, 0, 220]
        tc.pid = (2, 0, 220)


def test_tc200_pid_invalid_type():
    with pytest.raises(TypeError), expected_protocol(
        ik.thorlabs.TC200, [], [], sep="\r"
    ) as tc:
        tc.pid = "foo"


def test_tc200_pmin():
    with pytest.raises(ValueError), expected_protocol(
        ik.thorlabs.TC200, ["pgain=-1"], ["pgain=-1", "> "], sep="\r"
    ) as tc:
        tc.p = -1


def test_tc200_pmax():
    with pytest.raises(ValueError), expected_protocol(
        ik.thorlabs.TC200, ["pgain=260"], ["pgain=260", "> "], sep="\r"
    ) as tc:
        tc.p = 260


def test_tc200_imin():
    with pytest.raises(ValueError), expected_protocol(
        ik.thorlabs.TC200, ["igain=-1"], ["igain=-1", "> "], sep="\r"
    ) as tc:
        tc.i = -1


def test_tc200_imax():
    with pytest.raises(ValueError), expected_protocol(
        ik.thorlabs.TC200, ["igain=260"], ["igain=260", "> "], sep="\r"
    ) as tc:
        tc.i = 260


def test_tc200_dmin():
    with pytest.raises(ValueError), expected_protocol(
        ik.thorlabs.TC200, ["dgain=-1"], ["dgain=-1", "> "], sep="\r"
    ) as tc:
        tc.d = -1


def test_tc200_dmax():
    with pytest.raises(ValueError), expected_protocol(
        ik.thorlabs.TC200, ["dgain=260"], ["dgain=260", "> "], sep="\r"
    ) as tc:
        tc.d = 260


def test_tc200_degrees():
    with expected_protocol(
        ik.thorlabs.TC200,
        ["stat?", "stat?", "stat?", "unit=c", "unit=f", "unit=k"],
        [
            "stat?",
            "44 > stat?",
            "54 > stat?",
            "0 >  unit=c",
            "> unit=f",
            "> unit=k",
            "> ",
        ],
        sep="\r",
    ) as tc:
        assert tc.degrees == u.degK
        assert tc.degrees == u.degC
        assert tc.degrees == u.degF

        tc.degrees = u.degC
        tc.degrees = u.degF
        tc.degrees = u.degK


def test_tc200_degrees_invalid():
    with pytest.raises(TypeError), expected_protocol(
        ik.thorlabs.TC200, [], [], sep="\r"
    ) as tc:
        tc.degrees = "blo"


def test_tc200_sensor():
    with expected_protocol(
        ik.thorlabs.TC200,
        ["sns?", "sns=ptc100"],
        ["sns?", "Sensor = NTC10K, Beta = 5600", "> sns=ptc100", "> "],
        sep="\r",
    ) as tc:
        assert tc.sensor == tc.Sensor.ntc10k
        tc.sensor = tc.Sensor.ptc100


def test_tc200_sensor_error():
    with pytest.raises(ValueError), expected_protocol(ik.thorlabs.TC200, [], []) as tc:
        tc.sensor = "blo"


def test_tc200_sensor_error2():
    with pytest.raises(ValueError), expected_protocol(ik.thorlabs.TC200, [], []) as tc:

        class TestEnum(IntEnum):
            blo = 1
            beep = 2

        tc.sensor = TestEnum.blo


def test_tc200_beta():
    with expected_protocol(
        ik.thorlabs.TC200,
        ["beta?", "beta=2000"],
        ["beta?", "5600", "> beta=2000", "> "],
        sep="\r",
    ) as tc:
        assert tc.beta == 5600
        tc.beta = 2000


def test_tc200_beta_min():
    with pytest.raises(ValueError), expected_protocol(
        ik.thorlabs.TC200, ["beta=200"], ["beta=200", "> "], sep="\r"
    ) as tc:
        tc.beta = 200


def test_tc200_beta_max():
    with pytest.raises(ValueError), expected_protocol(
        ik.thorlabs.TC200, ["beta=20000"], ["beta=20000", "> "], sep="\r"
    ) as tc:
        tc.beta = 20000


def test_tc200_max_power():
    with expected_protocol(
        ik.thorlabs.TC200,
        ["pmax?", "pmax=12.0"],
        ["pmax?", "15.0", "> pmax=12.0", "> "],
        sep="\r",
    ) as tc:
        assert tc.max_power == 15.0 * u.W
        tc.max_power = 12 * u.W


def test_tc200_power_min():
    with pytest.raises(ValueError), expected_protocol(
        ik.thorlabs.TC200, ["PMAX=-2"], ["PMAX=-2", "> "], sep="\r"
    ) as tc:
        tc.max_power = -1


def test_tc200_power_max():
    with pytest.raises(ValueError), expected_protocol(
        ik.thorlabs.TC200, ["PMAX=20000"], ["PMAX=20000", "> "], sep="\r"
    ) as tc:
        tc.max_power = 20000


def test_tc200_max_temperature():
    with expected_protocol(
        ik.thorlabs.TC200,
        ["tmax?", "tmax=180.0"],
        ["tmax?", "200.0", "> tmax=180.0", "> "],
        sep="\r",
    ) as tc:
        assert tc.max_temperature == u.Quantity(200.0, u.degC)
        tc.max_temperature = u.Quantity(180, u.degC)


def test_tc200_temp_min():
    with pytest.raises(ValueError), expected_protocol(
        ik.thorlabs.TC200, ["TMAX=-2"], ["TMAX=-2", ">"], sep="\r"
    ) as tc:
        tc.max_temperature = -1


def test_tc200_temp_max():
    with pytest.raises(ValueError), expected_protocol(
        ik.thorlabs.TC200, ["TMAX=20000"], ["TMAX=20000", ">"], sep="\r"
    ) as tc:
        tc.max_temperature = 20000
