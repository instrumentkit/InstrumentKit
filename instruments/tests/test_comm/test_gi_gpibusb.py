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


def test_gpibusbcomm_init_correct_values_new_firmware():
    mock_gpib = mock.MagicMock()
    mock_gpib.query.return_value = "5"
    comm = GPIBCommunicator(mock_gpib, 1)

    eq_(comm._terminator, "\n")
    eq_(comm._version, 5)
    eq_(comm._eos, "\n")
    eq_(comm._eoi, True)
    unit_eq(comm._timeout, 1000 * pq.millisecond)


def test_gpibusbcomm_init_correct_values_old_firmware():
    # This test just has the differences between the new and old firmware
    mock_gpib = mock.MagicMock()
    mock_gpib.query.return_value = "4"
    comm = GPIBCommunicator(mock_gpib, 1)

    eq_(comm._eos, 10)


def test_gpibusbcomm_address():
    # Create our communicator
    comm = GPIBCommunicator(mock.MagicMock(), 1)

    port_name = mock.PropertyMock(return_value="/dev/address")
    type(comm._file).address = port_name

    # Check that our address function is working
    eq_(comm.address, (1, "/dev/address"))
    port_name.assert_called_with()

    # Able to set GPIB address
    comm.address = 5
    eq_(comm._gpib_address, 5)

    # Able to set address with a list
    comm.address = [6, "/dev/foobar"]  # pylint: disable=redefined-variable-type
    eq_(comm._gpib_address, 6)
    port_name.assert_called_with("/dev/foobar")


@raises(ValueError)
def test_gpibusbcomm_address_out_of_range():
    comm = GPIBCommunicator(mock.MagicMock(), 1)

    comm.address = 31


@raises(TypeError)
def test_gpibusbcomm_address_wrong_type():
    comm = GPIBCommunicator(mock.MagicMock(), 1)
    comm.address = "derp"


def test_gpibusbcomm_eoi():
    comm = GPIBCommunicator(mock.MagicMock(), 1)
    comm._version = 5

    comm._file.sendcmd = mock.MagicMock()
    comm.eoi = True
    eq_(comm.eoi, True)
    eq_(comm._eoi, True)
    comm._file.sendcmd.assert_called_with("++eoi 1")

    comm._file.sendcmd = mock.MagicMock()
    comm.eoi = False
    eq_(comm.eoi, False)
    eq_(comm._eoi, False)
    comm._file.sendcmd.assert_called_with("++eoi 0")


def test_gpibusbcomm_eoi_old_firmware():
    comm = GPIBCommunicator(mock.MagicMock(), 1)
    comm._version = 4

    comm._file.sendcmd = mock.MagicMock()
    comm.eoi = True
    eq_(comm.eoi, True)
    eq_(comm._eoi, True)
    comm._file.sendcmd.assert_called_with("+eoi:1")

    comm._file.sendcmd = mock.MagicMock()
    comm.eoi = False
    eq_(comm.eoi, False)
    eq_(comm._eoi, False)
    comm._file.sendcmd.assert_called_with("+eoi:0")


@raises(TypeError)
def test_gpibusbcomm_eoi_bad_type():
    comm = GPIBCommunicator(mock.MagicMock(), 1)
    comm._version = 5
    comm.eoi = "abc"


def test_gpibusbcomm_eos_rn():
    comm = GPIBCommunicator(mock.MagicMock(), 1)
    comm._version = 5

    comm._file.sendcmd = mock.MagicMock()
    comm.eos = "\r\n"
    eq_(comm.eos, "\r\n")
    eq_(comm._eos, "\r\n")
    comm._file.sendcmd.assert_called_with("++eos 0")


def test_gpibusbcomm_eos_r():
    comm = GPIBCommunicator(mock.MagicMock(), 1)
    comm._version = 5

    comm._file.sendcmd = mock.MagicMock()
    comm.eos = "\r"
    eq_(comm.eos, "\r")
    eq_(comm._eos, "\r")
    comm._file.sendcmd.assert_called_with("++eos 1")


def test_gpibusbcomm_eos_n():
    comm = GPIBCommunicator(mock.MagicMock(), 1)
    comm._version = 5

    comm._file.sendcmd = mock.MagicMock()
    comm.eos = "\n"
    eq_(comm.eos, "\n")
    eq_(comm._eos, "\n")
    comm._file.sendcmd.assert_called_with("++eos 2")


@raises(ValueError)
def test_gpibusbcomm_eos_invalid():
    comm = GPIBCommunicator(mock.MagicMock(), 1)
    comm._version = 5
    comm.eos = "*"


def test_gpibusbcomm_eos_old_firmware():
    comm = GPIBCommunicator(mock.MagicMock(), 1)
    comm._version = 4

    comm._file.sendcmd = mock.MagicMock()
    comm.eos = "\n"
    eq_(comm._eos, 10)
    comm._file.sendcmd.assert_called_with("+eos:10")


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


def test_gpibusbcomm_sendcmd_empty_string():
    comm = GPIBCommunicator(mock.MagicMock(), 1)
    comm._version = 5
    comm._file.sendcmd = mock.MagicMock()  # Refreshed because init makes calls

    comm._sendcmd("")
    comm._file.sendcmd.assert_not_called()


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


def test_gpibusbcomm_query_no_question_mark():
    comm = GPIBCommunicator(mock.MagicMock(), 1)
    comm._version = 5
    comm._file.sendcmd = mock.MagicMock()  # Refreshed because init makes calls

    comm._file.read = mock.MagicMock(return_value="answer")
    comm.sendcmd = mock.MagicMock()

    eq_(comm._query("mock"), "answer")
    comm.sendcmd.assert_called_with("mock")
    comm._file.read.assert_called_with(-1)
    comm._file.sendcmd.assert_has_calls([mock.call("+read")])


def test_serialcomm_flush_input():
    comm = GPIBCommunicator(mock.MagicMock(), 1)
    comm._version = 5

    comm.flush_input()
    comm._file.flush_input.assert_called_with()
