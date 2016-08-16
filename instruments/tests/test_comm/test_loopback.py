#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for the loopback communication layer
"""

# IMPORTS ####################################################################

from __future__ import absolute_import

from nose.tools import raises, eq_
import mock

from instruments.abstract_instruments.comm import LoopbackCommunicator

# TEST CASES #################################################################

# pylint: disable=protected-access,unused-argument


def test_loopbackcomm_init():
    var1 = "abc"
    var2 = "123"
    comm = LoopbackCommunicator(stdin=var1, stdout=var2)
    assert comm._stdin is var1
    assert comm._stdout is var2


@mock.patch("instruments.abstract_instruments.comm.loopback_communicator.sys")
def test_loopbackcomm_address(mock_sys):
    mock_name = mock.PropertyMock(return_value="address")
    type(mock_sys.stdin).name = mock_name
    comm = LoopbackCommunicator()
    comm._conn = mock.MagicMock()

    # Check that our address function is working
    eq_(comm.address, "address")
    mock_name.assert_called_with()


def test_loopbackcomm_terminator():
    comm = LoopbackCommunicator()

    # Default terminator should be \n
    eq_(comm.terminator, "\n")

    comm.terminator = b"*"
    eq_(comm.terminator, "*")
    eq_(comm._terminator, "*")

    comm.terminator = u"\r"  # pylint: disable=redefined-variable-type
    eq_(comm.terminator, u"\r")
    eq_(comm._terminator, u"\r")


def test_loopbackcomm_timeout():
    comm = LoopbackCommunicator()

    eq_(comm.timeout, 0)

    comm.timeout = 10
    eq_(comm.timeout, 0)  # setting should be ignored


def test_loopbackcomm_close():
    mock_stdin = mock.MagicMock()
    comm = LoopbackCommunicator(stdin=mock_stdin)

    comm.close()
    mock_stdin.close.assert_called_with()


def test_loopbackcomm_read_raw():
    mock_stdin = mock.MagicMock()
    mock_stdin.read.side_effect = [b"a", b"b", b"c", b"\n"]
    comm = LoopbackCommunicator(stdin=mock_stdin)

    eq_(comm.read_raw(), b"abc")
    mock_stdin.read.assert_has_calls([mock.call(1)]*4)
    assert mock_stdin.read.call_count == 4

    mock_stdin.read = mock.MagicMock()
    comm.read_raw(10)
    mock_stdin.read.assert_called_with(10)


def test_loopbackcomm_write_raw():
    mock_stdout = mock.MagicMock()
    comm = LoopbackCommunicator(stdout=mock_stdout)

    comm.write_raw(b"mock")
    mock_stdout.write.assert_called_with(b"mock")


def test_loopbackcomm_sendcmd():
    mock_stdout = mock.MagicMock()
    comm = LoopbackCommunicator(stdout=mock_stdout)

    comm._sendcmd("mock")
    mock_stdout.write.assert_called_with(b"mock\n")

    comm.write = mock.MagicMock()
    comm._sendcmd("mock")
    comm.write.assert_called_with("mock\n")


def test_loopbackcomm_query():
    comm = LoopbackCommunicator()
    comm.read = mock.MagicMock(return_value="answer")
    comm.sendcmd = mock.MagicMock()

    eq_(comm._query("mock"), "answer")
    comm.sendcmd.assert_called_with("mock")
    comm.read.assert_called_with(-1)

    comm._query("mock", size=10)
    comm.read.assert_called_with(10)


@raises(NotImplementedError)
def test_loopbackcomm_seek():
    comm = LoopbackCommunicator()
    comm.seek(1)


@raises(NotImplementedError)
def test_loopbackcomm_tell():
    comm = LoopbackCommunicator()
    comm.tell()


def test_loopbackcomm_flush_input():
    comm = LoopbackCommunicator()
    comm.flush_input()
