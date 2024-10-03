#!/usr/bin/env python
"""
Unit tests for the VXI11 communication layer
"""

# IMPORTS ####################################################################


import pytest

from instruments.abstract_instruments.comm import VXI11Communicator
from .. import mock

# TEST CASES #################################################################

# pylint: disable=protected-access,unused-argument,no-member

import_base = "instruments.abstract_instruments.comm.vxi11_communicator.vxi11"


@mock.patch(import_base)
def test_vxi11comm_init(mock_vxi11):
    _ = VXI11Communicator("host")
    mock_vxi11.Instrument.assert_called_with("host")


@mock.patch(import_base, new=None)
def test_vxi11comm_init_no_vxi11():
    with pytest.raises(ImportError):
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
    assert comm.address == ["host", "name"]
    host.assert_called_with()
    name.assert_called_with()


@mock.patch(import_base)
def test_vxi11comm_terminator(mock_vxi11):
    comm = VXI11Communicator()

    term_char = mock.PropertyMock(return_value="\n")
    type(comm._inst).term_char = term_char

    assert comm.terminator == "\n"
    term_char.assert_called_with()

    comm.terminator = "*"
    term_char.assert_called_with("*")


@mock.patch(import_base)
def test_vxi11comm_timeout(mock_vxi11):
    comm = VXI11Communicator()

    timeout = mock.PropertyMock(return_value=30)
    type(comm._inst).timeout = timeout

    assert comm.timeout == 30
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

    assert comm.read_raw() == b"mock"
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

    assert comm._query("mock") == "answer"
    comm._inst.ask.assert_called_with("mock", num=-1)

    comm._query("mock", size=10)
    comm._inst.ask.assert_called_with("mock", num=10)


@mock.patch(import_base)
def test_vxi11comm_seek(mock_vxi11):
    with pytest.raises(NotImplementedError):
        comm = VXI11Communicator()
        comm.seek(1)


@mock.patch(import_base)
def test_vxi11comm_tell(mock_vxi11):
    with pytest.raises(NotImplementedError):
        comm = VXI11Communicator()
        comm.tell()


@mock.patch(import_base)
def test_vxi11comm_flush(mock_vxi11):
    with pytest.raises(NotImplementedError):
        comm = VXI11Communicator()
        comm.flush_input()
