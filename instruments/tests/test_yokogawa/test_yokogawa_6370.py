#!/usr/bin/env python
"""
Unit tests for the Yokogawa 6370
"""

# IMPORTS #####################################################################


import struct

from hypothesis import (
    given,
    strategies as st,
)

import instruments as ik
from instruments.optional_dep_finder import numpy
from instruments.tests import (
    expected_protocol,
    iterable_eq,
)
from instruments.units import ureg as u


# TESTS #######################################################################


def test_channel_is_channel_class():
    inst = ik.yokogawa.Yokogawa6370.open_test()
    assert isinstance(inst.channel["A"], inst.Channel) is True


def test_init():
    with expected_protocol(ik.yokogawa.Yokogawa6370, [":FORMat:DATA REAL,64"], []) as _:
        pass


@given(
    values=st.lists(st.floats(allow_infinity=False, allow_nan=False), min_size=1),
    channel=st.sampled_from(ik.yokogawa.Yokogawa6370.Traces),
)
def test_channel_data(values, channel):
    values_packed = b"".join(struct.pack("<d", value) for value in values)
    values_len = str(len(values_packed)).encode()
    values_len_of_len = str(len(values_len)).encode()
    with expected_protocol(
        ik.yokogawa.Yokogawa6370,
        [
            ":FORMat:DATA REAL,64",
            f":TRAC:Y? {channel.value}",
        ],
        [b"#" + values_len_of_len + values_len + values_packed],
    ) as inst:
        values = tuple(values)
        if numpy:
            values = numpy.array(values, dtype="<d")
        iterable_eq(inst.channel[channel].data(), values)


@given(
    values=st.lists(st.floats(allow_infinity=False, allow_nan=False), min_size=1),
    channel=st.sampled_from(ik.yokogawa.Yokogawa6370.Traces),
)
def test_channel_wavelength(values, channel):
    values_packed = b"".join(struct.pack("<d", value) for value in values)
    values_len = str(len(values_packed)).encode()
    values_len_of_len = str(len(values_len)).encode()
    with expected_protocol(
        ik.yokogawa.Yokogawa6370,
        [
            ":FORMat:DATA REAL,64",
            f":TRAC:X? {channel.value}",
        ],
        [b"#" + values_len_of_len + values_len + values_packed],
    ) as inst:
        values = tuple(values)
        if numpy:
            values = numpy.array(values, dtype="<d")
        iterable_eq(inst.channel[channel].wavelength(), values)


@given(value=st.floats(min_value=600e-9, max_value=1700e-9))
def test_start_wavelength(value):
    with expected_protocol(
        ik.yokogawa.Yokogawa6370,
        [
            ":FORMat:DATA REAL,64",
            ":SENS:WAV:STAR?",
            f":SENS:WAV:STAR {value:e}",
        ],
        ["6.000000e-06"],
    ) as inst:
        assert inst.start_wl == 6e-6 * u.meter
        inst.start_wl = value * u.meter


@given(value=st.floats(min_value=600e-9, max_value=1700e-9))
def test_end_wavelength(value):
    with expected_protocol(
        ik.yokogawa.Yokogawa6370,
        [
            ":FORMat:DATA REAL,64",
            ":SENS:WAV:STOP?",
            f":SENS:WAV:STOP {value:e}",
        ],
        ["6.000000e-06"],
    ) as inst:
        assert inst.stop_wl == 6e-6 * u.meter
        inst.stop_wl = value * u.meter


def test_bandwidth():
    with expected_protocol(
        ik.yokogawa.Yokogawa6370,
        [":FORMat:DATA REAL,64", ":SENS:BAND:RES?", ":SENS:BAND:RES 1.000000e-06"],
        ["6.000000e-06"],
    ) as inst:
        assert inst.bandwidth == 6e-6 * u.meter
        inst.bandwidth = 1e-6 * u.meter


def test_span():
    with expected_protocol(
        ik.yokogawa.Yokogawa6370,
        [":FORMat:DATA REAL,64", ":SENS:WAV:SPAN?", ":SENS:WAV:SPAN 1.000000e-06"],
        ["6.000000e-06"],
    ) as inst:
        assert inst.span == 6e-6 * u.meter
        inst.span = 1e-6 * u.meter


def test_center_wl():
    with expected_protocol(
        ik.yokogawa.Yokogawa6370,
        [":FORMat:DATA REAL,64", ":SENS:WAV:CENT?", ":SENS:WAV:CENT 1.000000e-06"],
        ["6.000000e-06"],
    ) as inst:
        assert inst.center_wl == 6e-6 * u.meter
        inst.center_wl = 1e-6 * u.meter


def test_points():
    with expected_protocol(
        ik.yokogawa.Yokogawa6370,
        [":FORMat:DATA REAL,64", ":SENS:SWE:POIN?", ":SENS:SWE:POIN 1.000000e+00"],
        ["6"],
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
        ],
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
        ],
    ) as inst:
        inst.active_trace = inst.Traces.A
        inst.active_trace = inst.Traces.D
        assert inst.active_trace == inst.Traces.B
        assert inst.active_trace == inst.Traces.G


# METHODS #


@given(values=st.lists(st.decimals(allow_infinity=False, allow_nan=False), min_size=1))
def test_data_active_trace(values):
    """Get data from active trace - method."""
    values_packed = b"".join(struct.pack("<d", value) for value in values)
    values_len = str(len(values_packed)).encode()
    values_len_of_len = str(len(values_len)).encode()
    channel = "TRA"  # active trace
    with expected_protocol(
        ik.yokogawa.Yokogawa6370,
        [
            ":FORMat:DATA REAL,64",
            f":TRAC:Y? {channel}",
            ":TRAC:ACTIVE?",
            f":TRAC:Y? {channel}",
        ],
        [
            b"#" + values_len_of_len + values_len + values_packed,
            channel,
            b"#" + values_len_of_len + values_len + values_packed,
        ],
    ) as inst:
        # data by channel
        data_call_by_trace = inst.channel[channel].data()
        # call active trace data
        data_active_trace = inst.data()
        iterable_eq(data_call_by_trace, data_active_trace)


@given(values=st.lists(st.decimals(allow_infinity=False, allow_nan=False), min_size=1))
def test_wavelength_active_trace(values):
    """Get wavelength from active trace - method."""
    values_packed = b"".join(struct.pack("<d", value) for value in values)
    values_len = str(len(values_packed)).encode()
    values_len_of_len = str(len(values_len)).encode()
    channel = "TRA"  # active trace
    with expected_protocol(
        ik.yokogawa.Yokogawa6370,
        [
            ":FORMat:DATA REAL,64",
            f":TRAC:X? {channel}",
            ":TRAC:ACTIVE?",
            f":TRAC:X? {channel}",
        ],
        [
            b"#" + values_len_of_len + values_len + values_packed,
            channel,
            b"#" + values_len_of_len + values_len + values_packed,
        ],
    ) as inst:
        # data by channel
        data_call_by_trace = inst.channel[channel].wavelength()
        # call active trace data
        data_active_trace = inst.wavelength()
        iterable_eq(data_call_by_trace, data_active_trace)


def test_start_sweep():
    with expected_protocol(
        ik.yokogawa.Yokogawa6370,
        [
            ":FORMat:DATA REAL,64",
            "*CLS;:init",
        ],
        [],
    ) as inst:
        inst.start_sweep()
