#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for the USBTMC communication layer
"""

# IMPORTS ####################################################################

from __future__ import absolute_import

from nose.tools import raises, eq_
import mock

from instruments.abstract_instruments.comm import USBTMCCommunicator

# TEST CASES #################################################################

# pylint: disable=protected-access,unused-argument,no-member

patch_path = "instruments.abstract_instruments.comm.usbtmc_communicator.usbtmc"


@mock.patch(patch_path)
def test_usbtmccomm_init(mock_usbtmc):
    _ = USBTMCCommunicator("foobar", var1=123)
    mock_usbtmc.Instrument.assert_called_with("foobar", var1=123)


@raises(ImportError)
@mock.patch(patch_path, new=None)
def test_usbtmccomm_init_missing_module():
    _ = USBTMCCommunicator()


@mock.patch(patch_path)
def test_usbtmccomm_terminator_getter(mock_usbtmc):
    comm = USBTMCCommunicator()

    term_char = mock.PropertyMock(return_value="\n")
    type(comm._filelike).term_char = term_char

    eq_(comm.terminator, "\n")
    term_char.assert_called_with()


@mock.patch(patch_path)
def test_usbtmccomm_terminator_setter(mock_usbtmc):
    comm = USBTMCCommunicator()

    term_char = mock.PropertyMock(return_value="\n")
    type(comm._filelike).term_char = term_char

    comm.terminator = "*"
    eq_(comm._terminator, "*")
    term_char.assert_called_with("*")

    comm.terminator = b"*"  # pylint: disable=redefined-variable-type
    eq_(comm._terminator, "*")
    term_char.assert_called_with("*")


@raises(NotImplementedError)
@mock.patch(patch_path)
def test_usbtmccomm_timeout_getter(mock_usbtmc):
    comm = USBTMCCommunicator()
    _ = comm.timeout


@raises(NotImplementedError)
@mock.patch(patch_path)
def test_usbtmccomm_timeout_setter(mock_usbtmc):
    comm = USBTMCCommunicator()
    comm.timeout = 1


@mock.patch(patch_path)
def test_usbtmccomm_close(mock_usbtmc):
    comm = USBTMCCommunicator()

    comm.close()
    comm._filelike.close.assert_called_with()


@mock.patch(patch_path)
def test_usbtmccomm_read_raw(mock_usbtmc):
    comm = USBTMCCommunicator()
    comm._filelike.read_raw = mock.MagicMock(return_value=b"abc")

    eq_(comm.read_raw(), b"abc")
    comm._filelike.read_raw.assert_called_with(num=-1)
    assert comm._filelike.read_raw.call_count == 1

    comm._filelike.read_raw = mock.MagicMock()
    comm.read_raw(10)
    comm._filelike.read_raw.assert_called_with(num=10)


@mock.patch(patch_path)
def test_usbtmccomm_write_raw(mock_usbtmc):
    comm = USBTMCCommunicator()

    comm.write_raw(b"mock")
    comm._filelike.write_raw.assert_called_with(b"mock")


@mock.patch(patch_path)
def test_usbtmccomm_sendcmd(mock_usbtmc):
    comm = USBTMCCommunicator()
    comm.terminator = "\n"  # included due to mocking

    comm._sendcmd("mock")
    comm._filelike.write.assert_called_with("mock\n")


@mock.patch(patch_path)
def test_usbtmccomm_query(mock_usbtmc):
    comm = USBTMCCommunicator()
    comm._filelike.ask = mock.MagicMock(return_value="answer")

    eq_(comm._query("mock"), "answer")
    comm._filelike.ask.assert_called_with("mock", num=-1, encoding="utf-8")

    comm._query("mock", size=10)
    comm._filelike.ask.assert_called_with("mock", num=10, encoding="utf-8")


@raises(NotImplementedError)
@mock.patch(patch_path)
def test_usbtmccomm_seek(mock_usbtmc):
    comm = USBTMCCommunicator()
    comm.seek(1)


@raises(NotImplementedError)
@mock.patch(patch_path)
def test_usbtmccomm_tell(mock_usbtmc):
    comm = USBTMCCommunicator()
    comm.tell()


@raises(NotImplementedError)
@mock.patch(patch_path)
def test_usbtmccomm_flush_input(mock_usbtmc):
    comm = USBTMCCommunicator()
    comm.flush_input()
