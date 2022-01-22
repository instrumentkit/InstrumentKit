#!/usr/bin/env python
"""
Unit tests for the socket communication layer
"""

# IMPORTS ####################################################################


import socket

import pytest
from instruments.units import ureg as u

from instruments.abstract_instruments.comm import SocketCommunicator
from instruments.tests import unit_eq
from .. import mock

# TEST CASES #################################################################

# pylint: disable=protected-access,unused-argument


def test_socketcomm_init():
    socket_object = socket.socket()
    comm = SocketCommunicator(socket_object)
    assert isinstance(comm._conn, socket.socket) is True
    assert comm._conn == socket_object


def test_socketcomm_init_wrong_filelike():
    with pytest.raises(TypeError):
        _ = SocketCommunicator("derp")


def test_socketcomm_address():
    comm = SocketCommunicator(socket.socket())
    comm._conn = mock.MagicMock()
    comm._conn.getpeername.return_value = "127.0.0.1", 1234

    assert comm.address == ("127.0.0.1", 1234)
    comm._conn.getpeername.assert_called_with()


def test_socketcomm_address_setting():
    with pytest.raises(NotImplementedError):
        comm = SocketCommunicator(socket.socket())
        comm.address = "foobar"


def test_socketcomm_terminator():
    comm = SocketCommunicator(socket.socket())

    # Default terminator should be \n
    assert comm.terminator == "\n"

    comm.terminator = b"*"
    assert comm.terminator == "*"
    assert comm._terminator == "*"

    comm.terminator = "\r"
    assert comm.terminator == "\r"
    assert comm._terminator == "\r"

    comm.terminator = "\r\n"
    assert comm.terminator == "\r\n"
    assert comm._terminator == "\r\n"


def test_socketcomm_timeout():
    comm = SocketCommunicator(socket.socket())
    comm._conn = mock.MagicMock()
    comm._conn.gettimeout.return_value = 1.234

    unit_eq(comm.timeout, 1.234 * u.second)
    comm._conn.gettimeout.assert_called_with()

    comm.timeout = 10
    comm._conn.settimeout.assert_called_with(10)

    comm.timeout = 1000 * u.millisecond
    comm._conn.settimeout.assert_called_with(1)


def test_socketcomm_close():
    comm = SocketCommunicator(socket.socket())
    comm._conn = mock.MagicMock()

    comm.close()
    comm._conn.shutdown.assert_called_with(socket.SHUT_RDWR)
    comm._conn.close.assert_called_with()


def test_socketcomm_read_raw():
    comm = SocketCommunicator(socket.socket())
    comm._conn = mock.MagicMock()
    comm._conn.recv = mock.MagicMock(side_effect=[b"a", b"b", b"c", b"\n"])

    assert comm.read_raw() == b"abc"
    comm._conn.recv.assert_has_calls([mock.call(1)] * 4)
    assert comm._conn.recv.call_count == 4

    comm._conn.recv = mock.MagicMock()
    comm.read_raw(10)
    comm._conn.recv.assert_called_with(10)


def test_loopbackcomm_read_raw_2char_terminator():
    comm = SocketCommunicator(socket.socket())
    comm._conn = mock.MagicMock()
    comm._conn.recv = mock.MagicMock(side_effect=[b"a", b"b", b"c", b"\r", b"\n"])
    comm._terminator = "\r\n"

    assert comm.read_raw() == b"abc"
    comm._conn.recv.assert_has_calls([mock.call(1)] * 5)
    assert comm._conn.recv.call_count == 5


def test_serialcomm_read_raw_timeout():
    with pytest.raises(IOError):
        comm = SocketCommunicator(socket.socket())
        comm._conn = mock.MagicMock()
        comm._conn.recv = mock.MagicMock(side_effect=[b"a", b"b", b""])

        _ = comm.read_raw(-1)


def test_socketcomm_write_raw():
    comm = SocketCommunicator(socket.socket())
    comm._conn = mock.MagicMock()

    comm.write_raw(b"mock")
    comm._conn.sendall.assert_called_with(b"mock")


def test_socketcomm_sendcmd():
    comm = SocketCommunicator(socket.socket())
    comm._conn = mock.MagicMock()

    comm._sendcmd("mock")
    comm._conn.sendall.assert_called_with(b"mock\n")


def test_socketcomm_query():
    comm = SocketCommunicator(socket.socket())
    comm._conn = mock.MagicMock()
    comm.read = mock.MagicMock(return_value="answer")
    comm.sendcmd = mock.MagicMock()

    assert comm._query("mock") == "answer"
    comm.sendcmd.assert_called_with("mock")
    comm.read.assert_called_with(-1)

    comm._query("mock", size=10)
    comm.read.assert_called_with(10)


def test_socketcomm_seek():
    with pytest.raises(NotImplementedError):
        comm = SocketCommunicator(socket.socket())
        comm.seek(1)


def test_socketcomm_tell():
    with pytest.raises(NotImplementedError):
        comm = SocketCommunicator(socket.socket())
        comm.tell()


def test_socketcomm_flush_input():
    comm = SocketCommunicator(socket.socket())
    comm._conn = mock.MagicMock()
    comm.read = mock.MagicMock()
    comm.flush_input()

    comm.read.assert_called_with(-1)
