#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for the GI GPIBUSB communication layer
"""

# IMPORTS ####################################################################

from __future__ import absolute_import

from nose.tools import raises, eq_
import mock
import serial
import quantities as pq

from instruments.abstract_instruments.comm import GPIBCommunicator, SerialCommunicator
from instruments.tests import unit_eq

# TEST CASES #################################################################

# pylint: disable=protected-access,unused-argument


def test_gpibusbcomm_init():
    serial_comm = SerialCommunicator(serial.Serial())
    serial_comm._conn = mock.MagicMock()
    serial_comm._query = mock.MagicMock(return_value="1")
    comm = GPIBCommunicator(serial_comm, 1)
    assert isinstance(comm._file, SerialCommunicator)


def test_gpibusbcomm_address():
    # Create our communicator
    comm = GPIBCommunicator(mock.MagicMock(), 1)

    port_name = mock.PropertyMock(return_value="/dev/address")
    type(comm._file).address = port_name

    # Check that our address function is working
    eq_(comm.address, (1, "/dev/address"))
    port_name.assert_called_with()


def test_gpibusbcomm_terminator():
    comm = GPIBCommunicator(mock.MagicMock(), 1)
    comm._version = 5

    # Default terminator should be eoi
    eq_(comm.terminator, "eoi")
    eq_(comm._eoi, True)

    comm.terminator = "\n"
    eq_(comm.terminator, "\n")
    eq_(comm._eoi, False)

    comm.terminator = "eoi"
    eq_(comm.terminator, "eoi")
    eq_(comm._eoi, True)


def test_gpibusbcomm_timeout():
    comm = GPIBCommunicator(mock.MagicMock(), 1)
    comm._version = 5

    # timeout = mock.PropertyMock(return_value=30)
    # type(comm._conn).timeout = timeout

    unit_eq(comm.timeout, 1000 * pq.millisecond)

    comm.timeout = 5000 * pq.millisecond
    comm._file.sendcmd.assert_called_with("++read_tmo_ms 5000.0")


def test_gpibusbcomm_close():
    comm = GPIBCommunicator(mock.MagicMock(), 1)
    comm._version = 5

    comm.close()
    comm._file.close.assert_called_with()


def test_gpibusbcomm_read_raw():
    comm = GPIBCommunicator(mock.MagicMock(), 1)
    comm._version = 5
    comm._file.read_raw = mock.MagicMock(return_value=b"abc")

    eq_(comm.read_raw(3), b"abc")
    comm._file.read_raw.assert_called_with(3)


def test_gpibusbcomm_write_raw():
    comm = GPIBCommunicator(mock.MagicMock(), 1)
    comm._version = 5

    comm.write_raw(b"mock")
    comm._file.write_raw.assert_called_with(b"mock")


def test_gpibusbcomm_sendcmd():
    comm = GPIBCommunicator(mock.MagicMock(), 1)
    comm._version = 5

    comm._sendcmd("mock")
    comm._file.sendcmd.assert_has_calls([
        mock.call("+a:1"),
        mock.call("++eoi 1"),
        mock.call("++read_tmo_ms 1000.0"),
        mock.call("++eos 2"),
        mock.call("mock")
    ])


def test_gpibusbcomm_query():
    comm = GPIBCommunicator(mock.MagicMock(), 1)
    comm._version = 5

    comm._file.read = mock.MagicMock(return_value="answer")
    comm.sendcmd = mock.MagicMock()

    eq_(comm._query("mock?"), "answer")
    comm.sendcmd.assert_called_with("mock?")
    comm._file.read.assert_called_with(-1)

    comm._query("mock?", size=10)
    comm._file.read.assert_called_with(10)


def test_serialcomm_flush_input():
    comm = GPIBCommunicator(mock.MagicMock(), 1)
    comm._version = 5

    comm.flush_input()
    comm._file.flush_input.assert_called_with()
