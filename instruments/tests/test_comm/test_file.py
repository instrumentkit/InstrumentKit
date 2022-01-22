#!/usr/bin/env python
"""
Unit tests for the file communication layer
"""

# IMPORTS ####################################################################


import pytest

from instruments.abstract_instruments.comm import FileCommunicator
from .. import mock

# TEST CASES #################################################################

# pylint: disable=protected-access,unused-argument

patch_path = "instruments.abstract_instruments.comm.file_communicator.usbtmc"


def test_filecomm_init():
    mock_file = mock.MagicMock()
    comm = FileCommunicator(mock_file)
    assert comm._filelike is mock_file


def test_filecomm_address_getter():
    mock_file = mock.MagicMock()
    comm = FileCommunicator(mock_file)

    mock_name = mock.PropertyMock(return_value="/home/user/file")
    type(comm._filelike).name = mock_name

    assert comm.address == "/home/user/file"
    mock_name.assert_called_with()


def test_filecomm_address_getter_no_name():
    mock_file = mock.MagicMock()
    comm = FileCommunicator(mock_file)

    del comm._filelike.name

    assert comm.address is None


def test_filecomm_address_setter():
    with pytest.raises(NotImplementedError):
        comm = FileCommunicator(mock.MagicMock())
        comm.address = "abc123"


def test_filecomm_terminator():
    comm = FileCommunicator(mock.MagicMock())

    assert comm.terminator == "\n"

    comm.terminator = "*"
    assert comm._terminator == "*"

    comm.terminator = b"*"
    assert comm._terminator == "*"


def test_filecomm_timeout_getter():
    with pytest.raises(NotImplementedError):
        comm = FileCommunicator(mock.MagicMock())
        _ = comm.timeout


def test_filecomm_timeout_setter():
    with pytest.raises(NotImplementedError):
        comm = FileCommunicator(mock.MagicMock())
        comm.timeout = 1


def test_filecomm_close():
    comm = FileCommunicator(mock.MagicMock())

    comm.close()
    comm._filelike.close.assert_called_with()


def test_filecomm_read_raw():
    comm = FileCommunicator(mock.MagicMock())
    comm._filelike.read = mock.MagicMock(side_effect=[b"a", b"b", b"c", b"\n"])

    assert comm.read_raw() == b"abc"
    comm._filelike.read.assert_has_calls([mock.call(1)] * 4)
    assert comm._filelike.read.call_count == 4

    comm._filelike.read = mock.MagicMock()
    comm.read_raw(10)
    comm._filelike.read.assert_called_with(10)


def test_filecomm_write_raw():
    comm = FileCommunicator(mock.MagicMock())

    comm.write_raw(b"mock")
    comm._filelike.write.assert_called_with(b"mock")


def test_filecomm_sendcmd():
    comm = FileCommunicator(mock.MagicMock())

    comm._sendcmd("mock")
    comm._filelike.write.assert_called_with(b"mock\n")


def test_filecomm_query():
    comm = FileCommunicator(mock.MagicMock())
    comm._testing = True  # to disable the delay in the _query function
    comm._filelike.read = mock.MagicMock(side_effect=[b"a", b"b", b"c", b"\n"])

    assert comm._query("mock") == "abc"


def test_filecomm_seek():
    comm = FileCommunicator(mock.MagicMock())
    comm.seek(1)
    comm._filelike.seek.assert_called_with(1)


def test_filecomm_tell():
    comm = FileCommunicator(mock.MagicMock())
    comm._filelike.tell.return_value = 5

    assert comm.tell() == 5
    comm._filelike.tell.assert_called_with()


def test_filecomm_flush_input():
    comm = FileCommunicator(mock.MagicMock())
    comm.flush_input()
    comm._filelike.flush.assert_called_with()
