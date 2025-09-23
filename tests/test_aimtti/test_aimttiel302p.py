#!/usr/bin/env python
"""
Unit tests for the Aim-TTI EL302P single output power supply
"""

# IMPORTS #####################################################################

import pytest

import instruments as ik
from instruments.units import ureg as u
from tests import expected_protocol, unit_eq

# TESTS #######################################################################


def test_channel():
    with expected_protocol(ik.aimtti.AimTTiEL302P, [], [], sep="\n") as psu:
        assert psu.channel[0] == psu
        assert len(psu.channel) == 1


def test_current():
    with expected_protocol(
        ik.aimtti.AimTTiEL302P, ["I 1.0", "I?"], ["I 1.00"], sep="\n"
    ) as psu:
        psu.current = 1.0 * u.amp
        assert psu.current == 1.0 * u.amp


def test_current_sense():
    with expected_protocol(
        ik.aimtti.AimTTiEL302P, ["IO?"], ["I 1.00"], sep="\n"
    ) as psu:
        assert psu.current_sense == 1.00 * u.amp


def test_error():
    with expected_protocol(
        ik.aimtti.AimTTiEL302P, ["ERR?"], ["ERR 0"], sep="\n"
    ) as psu:
        assert psu.error == ik.aimtti.AimTTiEL302P.Error.error_none


def test_mode():
    with expected_protocol(ik.aimtti.AimTTiEL302P, ["M?"], ["M CV"], sep="\n") as psu:
        assert psu.mode == ik.aimtti.AimTTiEL302P.Mode.voltage


def test_name():
    with expected_protocol(
        ik.aimtti.AimTTiEL302P, ["*IDN?"], ["Thurlby Thandar,EL302P,0,v2.00"], sep="\n"
    ) as psu:
        assert psu.name == "Thurlby Thandar EL302P"


def test_off():
    with expected_protocol(
        ik.aimtti.AimTTiEL302P, ["OFF", "OUT?"], ["OUT OFF"], sep="\n"
    ) as psu:
        psu.output = False
        assert not psu.output


def test_on():
    with expected_protocol(
        ik.aimtti.AimTTiEL302P, ["ON", "OUT?"], ["OUT ON"], sep="\n"
    ) as psu:
        psu.output = True
        assert psu.output


def test_reset():
    with expected_protocol(ik.aimtti.AimTTiEL302P, ["*RST"], [], sep="\n") as psu:
        psu.reset()


def test_voltage():
    with expected_protocol(
        ik.aimtti.AimTTiEL302P, ["V 10.0", "V?"], ["V 10.00"], sep="\n"
    ) as psu:
        psu.voltage = 10.0 * u.volt
        assert psu.voltage == 10.0 * u.volt


def test_voltage_sense():
    with expected_protocol(
        ik.aimtti.AimTTiEL302P, ["VO?"], ["V 24.00"], sep="\n"
    ) as psu:
        assert psu.voltage_sense == 24.00 * u.volt
