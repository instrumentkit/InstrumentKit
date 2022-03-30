#!/usr/bin/env python
"""
Unit tests for the VISA communication layer
"""

# IMPORTS ####################################################################


import pytest
import pyvisa

from instruments.units import ureg as u
from instruments.abstract_instruments.comm import VisaCommunicator


# TEST CASES #################################################################

# pylint: disable=protected-access,redefined-outer-name

# create a visa instrument
@pytest.fixture()
def visa_inst():
    """Create a default visa-sim instrument and return it."""
    inst = pyvisa.ResourceManager("@sim").open_resource("ASRL1::INSTR")
    return inst


def test_visacomm_init(visa_inst):
    """Initialize visa communicator."""
    comm = VisaCommunicator(visa_inst)
    assert comm._conn == visa_inst
    assert comm._terminator == "\n"
    assert comm._buf == bytearray()


def test_visacomm_init_wrong_type():
    """Raise TypeError if not a VISA instrument."""
    with pytest.raises(TypeError) as err:
        VisaCommunicator(42)
    err_msg = err.value.args[0]
    assert err_msg == "VisaCommunicator must wrap a VISA Instrument."


def test_visacomm_address(visa_inst):
    """Get / Set instrument address."""
    comm = VisaCommunicator(visa_inst)
    assert comm.address == visa_inst.resource_name
    with pytest.raises(NotImplementedError) as err:
        comm.address = "new address"
    err_msg = err.value.args[0]
    assert err_msg == ("Changing addresses of a VISA Instrument is not supported.")


def test_visacomm_terminator(visa_inst):
    """Get / Set terminator."""
    comm = VisaCommunicator(visa_inst)
    comm.terminator = "\r"
    assert comm.terminator == "\r"


def test_visacomm_terminator_not_string(visa_inst):
    """Raise TypeError if terminator is set with non-string character."""
    comm = VisaCommunicator(visa_inst)
    with pytest.raises(TypeError) as err:
        comm.terminator = 42
    err_msg = err.value.args[0]
    assert err_msg == (
        "Terminator for VisaCommunicator must be specified as a single "
        "character string."
    )


def test_visacomm_terminator_not_single_char(visa_inst):
    """Raise ValueError if terminator longer than one character."""
    comm = VisaCommunicator(visa_inst)
    with pytest.raises(ValueError) as err:
        comm.terminator = "\r\n"
    err_msg = err.value.args[0]
    assert err_msg == ("Terminator for VisaCommunicator must only be 1 character long.")


def test_visacomm_timeout(visa_inst):
    """Set / Get timeout of VISA communicator."""
    comm = VisaCommunicator(visa_inst)
    comm.timeout = 3
    assert comm.timeout == u.Quantity(3, u.s)
    comm.timeout = u.Quantity(40000, u.ms)
    assert comm.timeout == u.Quantity(40, u.s)


def test_visacomm_close(visa_inst, mocker):
    """Raise an IOError if comms cannot be closed."""
    io_error_mock = mocker.Mock()
    io_error_mock.side_effect = IOError
    mock_close = mocker.patch.object(visa_inst, "close", io_error_mock)
    comm = VisaCommunicator(visa_inst)
    comm.close()
    mock_close.assert_called()  # but error will just pass!


def test_visacomm_read_raw(visa_inst, mocker):
    """Read raw data from instrument without size specification."""
    comm = VisaCommunicator(visa_inst)
    mock_read_raw = mocker.patch.object(visa_inst, "read_raw", return_value=b"asdf")
    comm.read_raw()
    mock_read_raw.assert_called()
    assert comm._buf == bytearray()


def test_visacomm_read_raw_size(visa_inst, mocker):
    """Read raw data from instrument with size specification."""
    comm = VisaCommunicator(visa_inst)
    size = 3
    mock_read_bytes = mocker.patch.object(visa_inst, "read_bytes", return_value=b"123")
    ret_val = comm.read_raw(size=size)
    assert ret_val == b"123"
    mock_read_bytes.assert_called()
    assert comm._buf == bytearray()


def test_visacomm_read_raw_wrong_size(visa_inst):
    """Raise ValueError if size is invalid."""
    comm = VisaCommunicator(visa_inst)
    with pytest.raises(ValueError) as err:
        comm.read_raw(size=-3)
    err_msg = err.value.args[0]
    assert err_msg == (
        "Must read a positive value of characters, or -1 for all characters."
    )


def test_visacomm_write_raw(visa_inst, mocker):
    """Write raw message to instrument."""
    mock_write = mocker.patch.object(visa_inst, "write_raw")
    comm = VisaCommunicator(visa_inst)
    msg = b"12345"
    comm.write_raw(msg)
    mock_write.assert_called_with(msg)


def test_visacomm_seek_not_implemented(visa_inst):
    """Raise NotImplementedError when calling seek."""
    comm = VisaCommunicator(visa_inst)
    with pytest.raises(NotImplementedError):
        comm.seek(42)


def test_visacomm_tell_not_implemented(visa_inst):
    """Raise NotImplementedError when calling tell."""
    comm = VisaCommunicator(visa_inst)
    with pytest.raises(NotImplementedError):
        comm.tell()


def test_visacomm_sendcmd(visa_inst, mocker):
    """Write to device."""
    mock_write = mocker.patch.object(VisaCommunicator, "write")
    comm = VisaCommunicator(visa_inst)
    msg = "asdf"
    comm._sendcmd(msg)
    mock_write.assert_called_with(msg + comm.terminator)


def test_visacomm_query(visa_inst, mocker):
    """Query device."""
    mock_query = mocker.patch.object(visa_inst, "query")
    comm = VisaCommunicator(visa_inst)
    msg = "asdf"
    comm._query(msg)
    mock_query.assert_called_with(msg + comm.terminator)
