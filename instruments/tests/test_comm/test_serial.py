#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for the serial communication layer
"""

# IMPORTS ####################################################################

from __future__ import absolute_import

from nose.tools import raises, eq_
import mock
import serial
import quantities as pq

from instruments.abstract_instruments.comm import SerialCommunicator
from instruments.tests import unit_eq

# TEST CASES #################################################################

# pylint: disable=protected-access,unused-argument


def test_serialcomm_init():
    comm = SerialCommunicator(serial.Serial())
    assert isinstance(comm._conn, serial.Serial) is True


@raises(TypeError)
def test_serialcomm_init_wrong_filelike():
    _ = SerialCommunicator("derp")


def test_serialcomm_address():
    # Create our communicator
    comm = SerialCommunicator(serial.Serial())
    comm._conn = mock.MagicMock()

    port_name = mock.PropertyMock(return_value="/dev/address")
    type(comm._conn).port = port_name

    # Check that our address function is working
    eq_(comm.address, "/dev/address")
    port_name.assert_called_with()


def test_serialcomm_terminator():
    comm = SerialCommunicator(serial.Serial())

    # Default terminator should be \n
    eq_(comm.terminator, "\n")

    comm.terminator = "*"
    eq_(comm.terminator, "*")


def test_serialcomm_timeout():
    comm = SerialCommunicator(serial.Serial())
    comm._conn = mock.MagicMock()

    timeout = mock.PropertyMock(return_value=30)
    type(comm._conn).timeout = timeout

    unit_eq(comm.timeout, 30 * pq.second)
    timeout.assert_called_with()

    comm.timeout = 10
    timeout.assert_called_with(10)

    comm.timeout = 1000 * pq.millisecond
    timeout.assert_called_with(1)


def test_serialcomm_close():
    comm = SerialCommunicator(serial.Serial())
    comm._conn = mock.MagicMock()

    comm.close()
    comm._conn.shutdown.assert_called_with()
    comm._conn.close.assert_called_with()


def test_serialcomm_read_raw():
    comm = SerialCommunicator(serial.Serial())
    comm._conn = mock.MagicMock()
    comm._conn.read = mock.MagicMock(side_effect=[b"a", b"b", b"c", b"\n"])

    eq_(comm.read_raw(), b"abc")
    comm._conn.read.assert_has_calls([mock.call(1)]*4)
    assert comm._conn.read.call_count == 4

    comm._conn.read = mock.MagicMock()
    comm.read_raw(10)
    comm._conn.read.assert_called_with(10)


@raises(IOError)
def test_serialcomm_read_raw_timeout():
    comm = SerialCommunicator(serial.Serial())
    comm._conn = mock.MagicMock()
    comm._conn.read = mock.MagicMock(side_effect=[b"a", b"b", b""])

    _ = comm.read_raw(-1)


def test_serialcomm_write_raw():
    comm = SerialCommunicator(serial.Serial())
    comm._conn = mock.MagicMock()

    comm.write_raw(b"mock")
    comm._conn.write.assert_called_with(b"mock")


def test_serialcomm_sendcmd():
    comm = SerialCommunicator(serial.Serial())
    comm._conn = mock.MagicMock()

    comm._sendcmd("mock")
    comm._conn.write.assert_called_with(b"mock\n")


def test_serialcomm_query():
    comm = SerialCommunicator(serial.Serial())
    comm._conn = mock.MagicMock()
    comm.read = mock.MagicMock(return_value="answer")
    comm.sendcmd = mock.MagicMock()

    eq_(comm._query("mock"), "answer")
    comm.sendcmd.assert_called_with("mock")
    comm.read.assert_called_with(-1)

    comm._query("mock", size=10)
    comm.read.assert_called_with(10)


@raises(NotImplementedError)
def test_serialcomm_seek():
    comm = SerialCommunicator(serial.Serial())
    comm.seek(1)


@raises(NotImplementedError)
def test_serialcomm_tell():
    comm = SerialCommunicator(serial.Serial())
    comm.tell()


def test_serialcomm_flush_input():
    comm = SerialCommunicator(serial.Serial())
    comm._conn = mock.MagicMock()
    comm.flush_input()

    comm._conn.flushInput.assert_called_with()
