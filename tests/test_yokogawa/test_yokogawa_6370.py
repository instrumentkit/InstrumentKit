#!/usr/bin/env python
"""
Unit tests for the Yokogawa 6370
"""

# IMPORTS #####################################################################

import hashlib
import struct

from hypothesis import (
    given,
    strategies as st,
)
import socket

import instruments as ik
from instruments.abstract_instruments.comm import SocketCommunicator
from instruments.optional_dep_finder import numpy
from tests import (
    expected_protocol,
    iterable_eq,
    pytest,
)
from instruments.units import ureg as u
from .. import mock


# TESTS #######################################################################


def test_channel_is_channel_class():
    inst = ik.yokogawa.Yokogawa6370.open_test()
    assert isinstance(inst.channel["A"], inst.Channel) is True


def test_init():
    with expected_protocol(ik.yokogawa.Yokogawa6370, [":FORMat:DATA REAL,64"], []) as _:
        pass


def test_id():
    with expected_protocol(
        ik.yokogawa.Yokogawa6370,
        [":FORMat:DATA REAL,64", "*IDN?"],
        ["'YOKOGAWA,AQ6370D,x,02.08'"],
    ) as inst:
        assert inst.id == "YOKOGAWA,AQ6370D,x,02.08"


@mock.patch("instruments.abstract_instruments.instrument.socket")
def test_tcpip_connection_terminator(mock_socket):
    """Ensure terminator is `\r\n` if connected via TCP-IP (issue #386)."""
    mock_socket.socket.return_value.__class__ = socket.socket
    inst = ik.yokogawa.Yokogawa6370.open_tcpip("127.0.0.1", port=1001)
    assert inst.terminator == "\r\n"


@mock.patch("instruments.abstract_instruments.instrument.socket")
def test_tcpip_authentication(mock_socket, mocker):
    mock_socket.socket.return_value.__class__ = socket.socket

    call_order = []

    mock_query = mocker.patch("instruments.yokogawa.Yokogawa6370.query")
    mock_sendcmd = mocker.patch("instruments.yokogawa.Yokogawa6370.sendcmd")

    def query_return(*args, **kwargs):
        """Return results and add to `call_order`."""
        call_order.append(mock_query)
        return "ready"

    mock_query.side_effect = query_return
    mock_sendcmd.side_effect = lambda *a, **kw: call_order.append(mock_sendcmd)

    username = "user"
    password = "my_password"

    _ = ik.yokogawa.Yokogawa6370.open_tcpip(
        "127.0.0.1", 1234, auth=(username, password)
    )

    pwd = hashlib.md5(bytes(f"ready{password}", "utf-8")).hexdigest()
    calls = [
        mocker.call(f'OPEN "{username}"'),
        mocker.call("AUTHENTICATE CRAM-MD5 OK"),
        mocker.call(f"{pwd}"),
    ]
    mock_query.assert_has_calls(calls, any_order=False)

    assert call_order == [mock_query, mock_query, mock_query, mock_sendcmd]


@mock.patch("instruments.abstract_instruments.instrument.socket")
def test_tcpip_authentication_anonymous(mock_socket, mocker):
    """Authenticate as anonymous user (any password accepted)."""
    mock_socket.socket.return_value.__class__ = socket.socket

    call_order = []

    mock_query = mocker.patch("instruments.yokogawa.Yokogawa6370.query")
    mock_sendcmd = mocker.patch("instruments.yokogawa.Yokogawa6370.sendcmd")

    def query_return(*args, **kwargs):
        """Return results and add to `call_order`."""
        call_order.append(mock_query)
        return "ready"

    mock_query.side_effect = query_return
    mock_sendcmd.side_effect = lambda *a, **kw: call_order.append(mock_sendcmd)

    username = "anonymous"
    password = "my_password"

    _ = ik.yokogawa.Yokogawa6370.open_tcpip(
        "127.0.0.1", 1234, auth=(username, password)
    )

    pwd = hashlib.md5(bytes(f"ready{password}", "utf-8")).hexdigest()
    calls = [
        mocker.call(f'OPEN "{username}"'),
        mocker.call(
            "AUTHENTICATE CRAM-MD5 OK"
        ),  # this is the password since any is accepted
    ]
    mock_query.assert_has_calls(calls, any_order=False)

    assert call_order == [mock_query, mock_query, mock_sendcmd]


@mock.patch("instruments.abstract_instruments.instrument.socket")
def test_tcpip_authentication_error(mock_socket, mocker):
    mock_socket.socket.return_value.__class__ = socket.socket

    mock_query = mocker.patch("instruments.yokogawa.Yokogawa6370.query")

    mock_query.side_effect = ["asdf", "asdf", "error"]  # three calls total

    username = "user"
    password = "my_password"

    with pytest.raises(ConnectionError):
        _ = ik.yokogawa.Yokogawa6370.open_tcpip(
            "127.0.0.1", 1234, auth=(username, password)
        )


def test_status():
    with expected_protocol(
        ik.yokogawa.Yokogawa6370, [":FORMat:DATA REAL,64", "*STB?"], ["7"]
    ) as inst:
        assert inst.status == 7


def test_operation_event():
    with expected_protocol(
        ik.yokogawa.Yokogawa6370,
        [":FORMat:DATA REAL,64", ":status:operation:event?"],
        ["7"],
    ) as inst:
        assert inst.operation_event == 7


@pytest.mark.parametrize("axis", ("X", "Y"))
@given(
    values=st.lists(st.floats(allow_infinity=False, allow_nan=False), min_size=1),
    channel=st.sampled_from(ik.yokogawa.Yokogawa6370.Traces),
)
def test_channel_private_data_wo_limits(values, channel, axis):
    values_packed = b"".join(struct.pack("<d", value) for value in values)
    values_len = str(len(values_packed)).encode()
    values_len_of_len = str(len(values_len)).encode()
    with expected_protocol(
        ik.yokogawa.Yokogawa6370,
        [
            ":FORMat:DATA REAL,64",
            f":TRAC:{axis}? {channel.value}",
        ],
        [b"#" + values_len_of_len + values_len + values_packed],
    ) as inst:
        values = tuple(values)
        if numpy:
            values = numpy.array(values, dtype="<d")
        iterable_eq(inst.channel[channel]._data(axis), values)


@pytest.mark.parametrize("axis", ("X", "Y"))
@given(
    values=st.lists(st.floats(allow_infinity=False, allow_nan=False), min_size=1),
    channel=st.sampled_from(ik.yokogawa.Yokogawa6370.Traces),
    start=st.integers(0, 25000),
    length=st.integers(0, 25000),
)
def test_channel_private_data_with_limits(values, channel, axis, start, length):
    values_packed = b"".join(struct.pack("<d", value) for value in values)
    values_len = str(len(values_packed)).encode()
    values_len_of_len = str(len(values_len)).encode()
    with expected_protocol(
        ik.yokogawa.Yokogawa6370,
        [
            ":FORMat:DATA REAL,64",
            f":TRAC:{axis}? {channel.value},{start+1},{start+1+length}",
        ],
        [b"#" + values_len_of_len + values_len + values_packed],
    ) as inst:
        values = tuple(values)
        if numpy:
            values = numpy.array(values, dtype="<d")
        iterable_eq(inst.channel[channel]._data(axis, (start, start + length)), values)


@pytest.mark.parametrize("limits", ([5], "abc", (7,), 3))
def test_channel_private_data_limit_error(limits):
    with expected_protocol(
        ik.yokogawa.Yokogawa6370, [":FORMat:DATA REAL,64"], []
    ) as inst:
        with pytest.raises(ValueError):
            inst.channel["A"]._data("X", limits)


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
            f":TRAC:X? {channel.value},1,501",
        ],
        [b"#" + values_len_of_len + values_len + values_packed],
    ) as inst:
        values = tuple(values)
        if numpy:
            values = numpy.array(values, dtype="<d")
        iterable_eq(inst.channel[channel].wavelength((0, 500)), values)


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


def test_analysis():
    with expected_protocol(
        ik.yokogawa.Yokogawa6370,
        [
            ":FORMat:DATA REAL,64",
            ":CALC:DATA?",
        ],
        ["1,2,3,7.3,3.12314,.2345"],
    ) as inst:
        assert inst.analysis() == [1, 2, 3, 7.3, 3.12314, 0.2345]


def test_abort():
    with expected_protocol(
        ik.yokogawa.Yokogawa6370,
        [
            ":FORMat:DATA REAL,64",
            ":ABORT",
        ],
        [],
    ) as inst:
        inst.abort()


def test_clear():
    with expected_protocol(
        ik.yokogawa.Yokogawa6370,
        [
            ":FORMat:DATA REAL,64",
            "*CLS",
        ],
        [],
    ) as inst:
        inst.clear()
