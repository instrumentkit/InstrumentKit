#!/usr/bin/env python
"""
Module containing tests for the MingHe MHS52000a
"""

# IMPORTS ####################################################################


import pytest
from instruments.units import ureg as u

import instruments as ik
from instruments.tests import expected_protocol


# TESTS ######################################################################


def test_mhs_amplitude():
    with expected_protocol(
        ik.minghe.MHS5200,
        [":r1a", ":r2a", ":s1a660", ":s2a800"],
        [":r1a330", ":r2a500", "ok", "ok"],
        sep="\r\n",
    ) as mhs:
        assert mhs.channel[0].amplitude[0] == 3.3 * u.V
        assert mhs.channel[1].amplitude[0] == 5.0 * u.V
        mhs.channel[0].amplitude = 6.6 * u.V
        mhs.channel[1].amplitude = 8.0 * u.V


def test_mhs_amplitude_dbm_notimplemented():
    with expected_protocol(ik.minghe.MHS5200, [], [], sep="\r\n") as mhs:
        with pytest.raises(NotImplementedError):
            mhs.channel[0].amplitude = u.Quantity(6.6, u.dBm)


def test_mhs_duty_cycle():
    with expected_protocol(
        ik.minghe.MHS5200,
        [":r1d", ":r2d", ":s1d6", ":s2d80"],
        [":r1d010", ":r2d100", "ok", "ok"],
        sep="\r\n",
    ) as mhs:
        assert mhs.channel[0].duty_cycle == 1.0
        assert mhs.channel[1].duty_cycle == 10.0
        mhs.channel[0].duty_cycle = 0.06
        mhs.channel[1].duty_cycle = 0.8


def test_mhs_enable():
    with expected_protocol(
        ik.minghe.MHS5200,
        [":r1b", ":r2b", ":s1b0", ":s2b1"],
        [":r1b1", ":r2b0", "ok", "ok"],
        sep="\r\n",
    ) as mhs:
        assert mhs.channel[0].enable
        assert not mhs.channel[1].enable
        mhs.channel[0].enable = False
        mhs.channel[1].enable = True


def test_mhs_frequency():
    with expected_protocol(
        ik.minghe.MHS5200,
        [":r1f", ":r2f", ":s1f600000", ":s2f800000"],
        [":r1f3300000", ":r2f50000000", "ok", "ok"],
        sep="\r\n",
    ) as mhs:
        assert mhs.channel[0].frequency == 33.0 * u.kHz
        assert mhs.channel[1].frequency == 500.0 * u.kHz
        mhs.channel[0].frequency = 6 * u.kHz
        mhs.channel[1].frequency = 8 * u.kHz


def test_mhs_offset():
    with expected_protocol(
        ik.minghe.MHS5200,
        [":r1o", ":r2o", ":s1o60", ":s2o180"],
        [":r1o120", ":r2o0", "ok", "ok"],
        sep="\r\n",
    ) as mhs:
        assert mhs.channel[0].offset == 0
        assert mhs.channel[1].offset == -1.2
        mhs.channel[0].offset = -0.6
        mhs.channel[1].offset = 0.6


def test_mhs_phase():
    with expected_protocol(
        ik.minghe.MHS5200,
        [":r1p", ":r2p", ":s1p60", ":s2p180"],
        [":r1p120", ":r2p0", "ok", "ok"],
        sep="\r\n",
    ) as mhs:
        assert mhs.channel[0].phase == 120 * u.degree
        assert mhs.channel[1].phase == 0 * u.degree
        mhs.channel[0].phase = 60
        mhs.channel[1].phase = 180


def test_mhs_wave_type():
    with expected_protocol(
        ik.minghe.MHS5200,
        [":r1w", ":r2w", ":s1w2", ":s2w3"],
        [":r1w0", ":r2w1", "ok", "ok"],
        sep="\r\n",
    ) as mhs:
        assert mhs.channel[0].function == mhs.Function.sine
        assert mhs.channel[1].function == mhs.Function.square
        mhs.channel[0].function = mhs.Function.triangular
        mhs.channel[1].function = mhs.Function.sawtooth_up


def test_mhs_serial_number():
    with expected_protocol(
        ik.minghe.MHS5200,
        [":r0c"],
        [
            ":r0c5225A1",
        ],
        sep="\r\n",
    ) as mhs:
        assert mhs.serial_number == "5225A1"


def test_mhs_get_amplitude():
    """Raise NotImplementedError when trying to get amplitude"""
    with expected_protocol(ik.minghe.MHS5200, [], [], sep="\r\n") as mhs:
        with pytest.raises(NotImplementedError):
            mhs._get_amplitude_()


def test_mhs_set_amplitude():
    """Raise NotImplementedError when trying to set amplitude"""
    with expected_protocol(ik.minghe.MHS5200, [], [], sep="\r\n") as mhs:
        with pytest.raises(NotImplementedError):
            mhs._set_amplitude_(1, 2)
