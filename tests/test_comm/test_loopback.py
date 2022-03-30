#!/usr/bin/env python
"""
Unit tests for the loopback communication layer
"""

# IMPORTS ####################################################################


import pytest

from instruments.abstract_instruments.comm import LoopbackCommunicator
from .. import mock

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
    assert comm.address == "address"
    mock_name.assert_called_with()


def test_loopbackcomm_terminator():
    comm = LoopbackCommunicator()

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


def test_loopbackcomm_timeout():
    comm = LoopbackCommunicator()

    assert comm.timeout == 0

    comm.timeout = 10
    assert comm.timeout == 0  # setting should be ignored


def test_loopbackcomm_close():
    mock_stdin = mock.MagicMock()
    comm = LoopbackCommunicator(stdin=mock_stdin)

    comm.close()
    mock_stdin.close.assert_called_with()


def test_loopbackcomm_read_raw():
    mock_stdin = mock.MagicMock()
    mock_stdin.read.side_effect = [b"a", b"b", b"c", b"\n"]
    comm = LoopbackCommunicator(stdin=mock_stdin)

    assert comm.read_raw() == b"abc"
    mock_stdin.read.assert_has_calls([mock.call(1)] * 4)
    assert mock_stdin.read.call_count == 4

    mock_stdin.read = mock.MagicMock()
    comm.read_raw(10)
    mock_stdin.read.assert_called_with(10)


def test_loopbackcomm_read_raw_2char_terminator():
    mock_stdin = mock.MagicMock()
    mock_stdin.read.side_effect = [b"a", b"b", b"c", b"\r", b"\n"]
    comm = LoopbackCommunicator(stdin=mock_stdin)
    comm._terminator = "\r\n"

    assert comm.read_raw() == b"abc"
    mock_stdin.read.assert_has_calls([mock.call(1)] * 5)
    assert mock_stdin.read.call_count == 5


def test_loopbackcomm_read_raw_terminator_is_empty_string():
    mock_stdin = mock.MagicMock()
    mock_stdin.read.side_effect = [b"abc"]
    comm = LoopbackCommunicator(stdin=mock_stdin)
    comm._terminator = ""

    assert comm.read_raw() == b"abc"
    mock_stdin.read.assert_has_calls([mock.call(-1)])
    assert mock_stdin.read.call_count == 1


def test_loopbackcomm_read_raw_size_invalid():
    with pytest.raises(ValueError):
        mock_stdin = mock.MagicMock()
        mock_stdin.read.side_effect = [b"abc"]
        comm = LoopbackCommunicator(stdin=mock_stdin)
        comm.read_raw(size=-2)


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

    assert comm._query("mock") == "answer"
    comm.sendcmd.assert_called_with("mock")
    comm.read.assert_called_with(-1)

    comm._query("mock", size=10)
    comm.read.assert_called_with(10)


def test_loopbackcomm_seek():
    with pytest.raises(NotImplementedError):
        comm = LoopbackCommunicator()
        comm.seek(1)


def test_loopbackcomm_tell():
    with pytest.raises(NotImplementedError):
        comm = LoopbackCommunicator()
        comm.tell()


def test_loopbackcomm_flush_input():
    comm = LoopbackCommunicator()
    comm.flush_input()
