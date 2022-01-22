#!/usr/bin/env python
"""
Unit tests for the serial communication layer
"""

# IMPORTS ####################################################################


import pytest
import serial
from instruments.units import ureg as u

from instruments.abstract_instruments.comm import SerialCommunicator
from instruments.tests import unit_eq
from .. import mock

# TEST CASES #################################################################

# pylint: disable=protected-access,unused-argument


def test_serialcomm_init():
    comm = SerialCommunicator(serial.Serial())
    assert isinstance(comm._conn, serial.Serial) is True


def test_serialcomm_init_wrong_filelike():
    with pytest.raises(TypeError):
        _ = SerialCommunicator("derp")


def test_serialcomm_address():
    # Create our communicator
    comm = SerialCommunicator(serial.Serial())
    comm._conn = mock.MagicMock()

    port_name = mock.PropertyMock(return_value="/dev/address")
    type(comm._conn).port = port_name

    # Check that our address function is working
    assert comm.address == "/dev/address"
    port_name.assert_called_with()


def test_serialcomm_terminator():
    comm = SerialCommunicator(serial.Serial())

    # Default terminator should be \n
    assert comm.terminator == "\n"

    comm.terminator = "*"
    assert comm.terminator == "*"

    comm.terminator = "\r\n"
    assert comm.terminator == "\r\n"
    assert comm._terminator == "\r\n"


def test_serialcomm_timeout():
    comm = SerialCommunicator(serial.Serial())
    comm._conn = mock.MagicMock()

    timeout = mock.PropertyMock(return_value=30)
    type(comm._conn).timeout = timeout

    unit_eq(comm.timeout, 30 * u.second)
    timeout.assert_called_with()

    comm.timeout = 10
    timeout.assert_called_with(10)

    comm.timeout = 1000 * u.millisecond
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

    assert comm.read_raw() == b"abc"
    comm._conn.read.assert_has_calls([mock.call(1)] * 4)
    assert comm._conn.read.call_count == 4

    comm._conn.read = mock.MagicMock()
    comm.read_raw(10)
    comm._conn.read.assert_called_with(10)


def test_loopbackcomm_read_raw_2char_terminator():
    comm = SerialCommunicator(serial.Serial())
    comm._conn = mock.MagicMock()
    comm._conn.read = mock.MagicMock(side_effect=[b"a", b"b", b"c", b"\r", b"\n"])
    comm._terminator = "\r\n"

    assert comm.read_raw() == b"abc"
    comm._conn.read.assert_has_calls([mock.call(1)] * 5)
    assert comm._conn.read.call_count == 5


def test_serialcomm_read_raw_timeout():
    with pytest.raises(IOError):
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

    assert comm._query("mock") == "answer"
    comm.sendcmd.assert_called_with("mock")
    comm.read.assert_called_with(-1)

    comm._query("mock", size=10)
    comm.read.assert_called_with(10)


def test_serialcomm_seek():
    with pytest.raises(NotImplementedError):
        comm = SerialCommunicator(serial.Serial())
        comm.seek(1)


def test_serialcomm_tell():
    with pytest.raises(NotImplementedError):
        comm = SerialCommunicator(serial.Serial())
        comm.tell()


def test_serialcomm_flush_input():
    comm = SerialCommunicator(serial.Serial())
    comm._conn = mock.MagicMock()
    comm.flush_input()

    comm._conn.flushInput.assert_called_with()
