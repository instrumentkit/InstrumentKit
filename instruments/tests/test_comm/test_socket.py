#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for the socket communication layer
"""

# IMPORTS ####################################################################

from __future__ import absolute_import

import socket

from nose.tools import raises, eq_
import mock
import quantities as pq

from instruments.abstract_instruments.comm import SocketCommunicator
from instruments.tests import unit_eq

# TEST CASES #################################################################

# pylint: disable=protected-access,unused-argument


def test_socketcomm_init():
    socket_object = socket.socket()
    comm = SocketCommunicator(socket_object)
    assert isinstance(comm._conn, socket.socket) is True
    assert comm._conn == socket_object


@raises(TypeError)
def test_socketcomm_init_wrong_filelike():
    _ = SocketCommunicator("derp")


def test_socketcomm_address():
    comm = SocketCommunicator(socket.socket())
    comm._conn = mock.MagicMock()
    comm._conn.getpeername.return_value = "127.0.0.1", 1234

    eq_(comm.address, ("127.0.0.1", 1234))
    comm._conn.getpeername.assert_called_with()


@raises(NotImplementedError)
def test_socketcomm_address_setting():
    comm = SocketCommunicator(socket.socket())
    comm.address = "foobar"


def test_socketcomm_terminator():
    comm = SocketCommunicator(socket.socket())

    # Default terminator should be \n
    eq_(comm.terminator, "\n")

    comm.terminator = b"*"
    eq_(comm.terminator, "*")
    eq_(comm._terminator, "*")

    comm.terminator = u"\r"  # pylint: disable=redefined-variable-type
    eq_(comm.terminator, u"\r")
    eq_(comm._terminator, u"\r")


def test_socketcomm_timeout():
    comm = SocketCommunicator(socket.socket())
    comm._conn = mock.MagicMock()
    comm._conn.gettimeout.return_value = 1.234

    unit_eq(comm.timeout, 1.234 * pq.second)
    comm._conn.gettimeout.assert_called_with()

    comm.timeout = 10
    comm._conn.settimeout.assert_called_with(10)

    comm.timeout = 1000 * pq.millisecond
    comm._conn.settimeout.assert_called_with(1)


def test_socketcomm_close():
    comm = SocketCommunicator(socket.socket())
    comm._conn = mock.MagicMock()

    comm.close()
    comm._conn.shutdown.assert_called_with()
    comm._conn.close.assert_called_with()


def test_socketcomm_read_raw():
    comm = SocketCommunicator(socket.socket())
    comm._conn = mock.MagicMock()
    comm._conn.recv = mock.MagicMock(side_effect=[b"a", b"b", b"c", b"\n"])

    eq_(comm.read_raw(), b"abc")
    comm._conn.recv.assert_has_calls([mock.call(1)]*4)
    assert comm._conn.recv.call_count == 4

    comm._conn.recv = mock.MagicMock()
    comm.read_raw(10)
    comm._conn.recv.assert_called_with(10)


@raises(IOError)
def test_serialcomm_read_raw_timeout():
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

    eq_(comm._query("mock"), "answer")
    comm.sendcmd.assert_called_with("mock")
    comm.read.assert_called_with(-1)

    comm._query("mock", size=10)
    comm.read.assert_called_with(10)


@raises(NotImplementedError)
def test_socketcomm_seek():
    comm = SocketCommunicator(socket.socket())
    comm.seek(1)


@raises(NotImplementedError)
def test_socketcomm_tell():
    comm = SocketCommunicator(socket.socket())
    comm.tell()


def test_socketcomm_flush_input():
    comm = SocketCommunicator(socket.socket())
    comm._conn = mock.MagicMock()
    comm.read = mock.MagicMock()
    comm.flush_input()

    comm.read.assert_called_with(-1)
