#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for the Yokogawa 6370
"""

# IMPORTS #####################################################################

from __future__ import absolute_import

import struct

import numpy as np
import quantities as pq

import instruments as ik
from instruments.tests import expected_protocol

from hypothesis import (
    given,
    strategies as st,
)

# TESTS #######################################################################


def test_channel_is_channel_class():
    inst = ik.yokogawa.Yokogawa6370.open_test()
    assert isinstance(inst.channel["A"], inst.Channel) is True


def test_init():
    with expected_protocol(
        ik.yokogawa.Yokogawa6370,
        [
            ":FORMat:DATA REAL,64"
        ],
        []
    ) as _:
        pass


@given(values=st.lists(st.decimals(allow_infinity=False, allow_nan=False), min_size=1),
       channel=st.sampled_from(ik.yokogawa.Yokogawa6370.Traces))
def test_channel_data(values, channel):
    values_packed = b"".join(struct.pack("<d", value) for value in values)
    values_len = str(len(values_packed)).encode()
    values_len_of_len = str(len(values_len)).encode()
    with expected_protocol(
        ik.yokogawa.Yokogawa6370,
        [
            ":FORMat:DATA REAL,64",
            ":TRAC:Y? {}".format(channel.value),
        ],
        [
            b"#" + values_len_of_len + values_len + values_packed
        ]
    ) as inst:
        np.testing.assert_array_equal(inst.channel[channel].data(), np.array(values, dtype="<d"))


@given(values=st.lists(st.decimals(allow_infinity=False, allow_nan=False), min_size=1),
       channel=st.sampled_from(ik.yokogawa.Yokogawa6370.Traces))
def test_channel_wavelength(values, channel):
    values_packed = b"".join(struct.pack("<d", value) for value in values)
    values_len = str(len(values_packed)).encode()
    values_len_of_len = str(len(values_len)).encode()
    with expected_protocol(
        ik.yokogawa.Yokogawa6370,
        [
            ":FORMat:DATA REAL,64",
            ":TRAC:X? {}".format(channel.value),
        ],
        [
            b"#" + values_len_of_len + values_len + values_packed
        ]
    ) as inst:
        np.testing.assert_array_equal(
            inst.channel[channel].wavelength(),
            np.array(values, dtype="<d")
        )


@given(value=st.floats(min_value=600e-9, max_value=1700e-9))
def test_start_wavelength(value):
    with expected_protocol(
        ik.yokogawa.Yokogawa6370,
        [
            ":FORMat:DATA REAL,64",
            ":SENS:WAV:STAR?",
            ":SENS:WAV:STAR {:e}".format(value),
        ],
        [
            "6.000000e-06"
        ]
    ) as inst:
        assert inst.start_wl == 6e-6 * pq.meter
        inst.start_wl = value * pq.meter


@given(value=st.floats(min_value=600e-9, max_value=1700e-9))
def test_end_wavelength(value):
    with expected_protocol(
        ik.yokogawa.Yokogawa6370,
        [
            ":FORMat:DATA REAL,64",
            ":SENS:WAV:STOP?",
            ":SENS:WAV:STOP {:e}".format(value),
        ],
        [
            "6.000000e-06"
        ]
    ) as inst:
        assert inst.stop_wl == 6e-6 * pq.meter
        inst.stop_wl = value * pq.meter


def test_bandwidth():
    with expected_protocol(
        ik.yokogawa.Yokogawa6370,
        [
            ":FORMat:DATA REAL,64",
            ":SENS:BAND:RES?",
            ":SENS:BAND:RES 1.000000e-06"
        ],
        [
            "6.000000e-06"
        ]
    ) as inst:
        assert inst.bandwidth == 6e-6 * pq.meter
        inst.bandwidth = 1e-6 * pq.meter


def test_span():
    with expected_protocol(
        ik.yokogawa.Yokogawa6370,
        [
            ":FORMat:DATA REAL,64",
            ":SENS:WAV:SPAN?",
            ":SENS:WAV:SPAN 1.000000e-06"
        ],
        [
            "6.000000e-06"
        ]
    ) as inst:
        assert inst.span == 6e-6 * pq.meter
        inst.span = 1e-6 * pq.meter


def test_center_wl():
    with expected_protocol(
        ik.yokogawa.Yokogawa6370,
        [
            ":FORMat:DATA REAL,64",
            ":SENS:WAV:CENT?",
            ":SENS:WAV:CENT 1.000000e-06"
        ],
        [
            "6.000000e-06"
        ]
    ) as inst:
        assert inst.center_wl == 6e-6 * pq.meter
        inst.center_wl = 1e-6 * pq.meter


def test_points():
    with expected_protocol(
        ik.yokogawa.Yokogawa6370,
        [
            ":FORMat:DATA REAL,64",
            ":SENS:SWE:POIN?",
            ":SENS:SWE:POIN 1.000000e+00"
        ],
        [
            "6"
        ]
    ) as inst:
        assert inst.points == 6
        inst.points = 1


def test_sweep_mode():
    with expected_protocol(
        ik.yokogawa.Yokogawa6370,
        [
            ":FORMat:DATA REAL,64",
            ":INIT:SMOD 1",
            ":INIT:SMOD 2",
            ":INIT:SMOD 3",
            ":INIT:SMOD?",
            ":INIT:SMOD?",
            ":INIT:SMOD?",
        ],
        [
            "1",
            "2",
            "3",
        ]
    ) as inst:
        for mode in inst.SweepModes:
            inst.sweep_mode = mode
        for mode in inst.SweepModes:
            assert inst.sweep_mode == mode


def test_active_trace():
    with expected_protocol(
        ik.yokogawa.Yokogawa6370,
        [
            ":FORMat:DATA REAL,64",
            ":TRAC:ACTIVE TRA",
            ":TRAC:ACTIVE TRD",
            ":TRAC:ACTIVE?",
            ":TRAC:ACTIVE?",
        ],
        [
            "TRB",
            "TRG",
        ]
    ) as inst:
        inst.active_trace = inst.Traces.A
        inst.active_trace = inst.Traces.D
        assert inst.active_trace == inst.Traces.B
        assert inst.active_trace == inst.Traces.G


def test_start_sweep():
    with expected_protocol(
        ik.yokogawa.Yokogawa6370,
        [
            ":FORMat:DATA REAL,64",
            "*CLS;:init",
        ],
        []
    ) as inst:
        inst.start_sweep()
