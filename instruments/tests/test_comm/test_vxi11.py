#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for the VXI11 communication layer
"""

# IMPORTS ####################################################################

from __future__ import absolute_import

from nose.tools import raises, eq_
import mock

from instruments.abstract_instruments.comm import VXI11Communicator

# TEST CASES #################################################################

# pylint: disable=protected-access,unused-argument,no-member

import_base = "instruments.abstract_instruments.comm.vxi11_communicator.vxi11"


@mock.patch(import_base)
def test_vxi11comm_init(mock_vxi11):
    _ = VXI11Communicator("host")
    mock_vxi11.Instrument.assert_called_with("host")


@raises(ImportError)
@mock.patch(import_base, new=None)
def test_vxi11comm_init_no_vxi11():
    _ = VXI11Communicator("host")


@mock.patch(import_base)
def test_vxi11comm_address(mock_vxi11):
    # Create our communicator
    comm = VXI11Communicator()

    # Add in the host and name properties which are usually
    # done in vxi11.Instrument.__init__
    host = mock.PropertyMock(return_value="host")
    name = mock.PropertyMock(return_value="name")
    type(comm._inst).host = host
    type(comm._inst).name = name

    # Check that our address function is working
    eq_(comm.address, ["host", "name"])
    host.assert_called_with()
    name.assert_called_with()


@mock.patch(import_base)
def test_vxi11comm_terminator(mock_vxi11):
    comm = VXI11Communicator()

    term_char = mock.PropertyMock(return_value="\n")
    type(comm._inst).term_char = term_char

    eq_(comm.terminator, "\n")
    term_char.assert_called_with()

    comm.terminator = "*"
    term_char.assert_called_with("*")


@mock.patch(import_base)
def test_vxi11comm_timeout(mock_vxi11):
    comm = VXI11Communicator()

    timeout = mock.PropertyMock(return_value=30)
    type(comm._inst).timeout = timeout

    eq_(comm.timeout, 30)
    timeout.assert_called_with()

    comm.timeout = 10
    timeout.assert_called_with(10)


@mock.patch(import_base)
def test_vxi11comm_close(mock_vxi11):
    comm = VXI11Communicator()

    comm.close()
    comm._inst.close.assert_called_with()


@mock.patch(import_base)
def test_vxi11comm_close_fail(mock_vxi11):
    comm = VXI11Communicator()

    comm._inst.close.return_value = Exception
    comm.close()
    comm._inst.close.assert_called_once_with()


@mock.patch(import_base)
def test_vxi11comm_read(mock_vxi11):
    comm = VXI11Communicator()
    comm._inst.read_raw.return_value = b"mock"

    eq_(comm.read_raw(), b"mock")
    comm._inst.read_raw.assert_called_with(num=-1)

    comm.read(10)
    comm._inst.read_raw.assert_called_with(num=10)


@mock.patch(import_base)
def test_vxi11comm_write(mock_vxi11):
    comm = VXI11Communicator()

    comm.write_raw(b"mock")
    comm._inst.write_raw.assert_called_with(b"mock")


@mock.patch(import_base)
def test_vxi11comm_sendcmd(mock_vxi11):
    comm = VXI11Communicator()

    comm._sendcmd("mock")
    comm._inst.write_raw.assert_called_with(b"mock")


@mock.patch(import_base)
def test_vxi11comm_query(mock_vxi11):
    comm = VXI11Communicator()
    comm._inst.ask.return_value = "answer"

    eq_(comm._query("mock"), "answer")
    comm._inst.ask.assert_called_with("mock", num=-1)

    comm._query("mock", size=10)
    comm._inst.ask.assert_called_with("mock", num=10)


@raises(NotImplementedError)
@mock.patch(import_base)
def test_vxi11comm_seek(mock_vxi11):
    comm = VXI11Communicator()
    comm.seek(1)


@raises(NotImplementedError)
@mock.patch(import_base)
def test_vxi11comm_tell(mock_vxi11):
    comm = VXI11Communicator()
    comm.tell()


@raises(NotImplementedError)
@mock.patch(import_base)
def test_vxi11comm_flush(mock_vxi11):
    comm = VXI11Communicator()
    comm.flush_input()
