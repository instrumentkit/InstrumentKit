#!/usr/bin/env python
"""
Unit tests for the USB communicator.
"""

# IMPORTS ####################################################################

from hypothesis import given, strategies as st
import pytest

import usb.core
import usb.util

from instruments.abstract_instruments.comm import USBCommunicator
from instruments.units import ureg as u
from .. import mock

# TEST CASES #################################################################

# pylint: disable=protected-access,unused-argument, redefined-outer-name

patch_util = "instruments.abstract_instruments.comm.usb_communicator.usb.util"


@pytest.fixture()
def dev():
    """Return a usb core device for initialization."""
    dev = mock.MagicMock()
    dev.__class__ = usb.core.Device
    return dev


@pytest.fixture()
@mock.patch(patch_util)
def inst(patch_util, dev):
    """Return a USB Communicator instrument."""
    return USBCommunicator(dev)


@mock.patch(patch_util)
def test_init(usb_util, dev):
    """Initialize usb communicator."""
    # mock some behavior of the device required for initializing
    dev.find.return_value.__class__ = usb.core.Device  # dev
    # shortcuts for asserting calls
    cfg = dev.get_active_configuration()
    interface_number = cfg[(0, 0)].bInterfaceNumber
    _ = dev.control.get_interface(dev, cfg[(0, 0)].bInterfaceNumber)

    inst = USBCommunicator(dev)

    # # assert calls according to manual
    dev.set_configuration.assert_called()  # check default configuration
    dev.get_active_configuration.assert_called()  # get active configuration
    dev.control.get_interface.assert_called_with(dev, interface_number)
    usb_util.find_descriptor.assert_has_calls(cfg)

    assert isinstance(inst, USBCommunicator)

    assert inst._dev == dev


def test_init_wrong_type():
    """Raise TypeError if initialized with wrong device."""
    with pytest.raises(TypeError) as err:
        _ = USBCommunicator(42)
    err_msg = err.value.args[0]
    assert err_msg == "USBCommunicator must wrap a usb.core.Device object."


def test_init_no_endpoints(dev):
    """Initialize usb communicator without endpoints."""
    # mock some behavior of the device required for initializing
    dev.find.return_value.__class__ = usb.core.Device  # dev

    with pytest.raises(IOError) as err:
        _ = USBCommunicator(dev)
    err_msg = err.value.args[0]
    assert err_msg == "USB endpoint not found."


def test_address(inst):
    """Address of device can not be read, nor written."""
    with pytest.raises(NotImplementedError):
        _ = inst.address

    with pytest.raises(ValueError) as err:
        inst.address = 42

    msg = err.value.args[0]
    assert msg == "Unable to change USB target address."


def test_terminator(inst):
    """Get / set terminator of instrument."""
    assert inst.terminator == "\n"
    inst.terminator = "\r\n"
    assert inst.terminator == "\r\n"


def test_terminator_wrong_type(inst):
    """Raise TypeError when setting bad terminator."""
    with pytest.raises(TypeError) as err:
        inst.terminator = 42
    msg = err.value.args[0]
    assert (
        msg == "Terminator for USBCommunicator must be specified as a "
        "character string."
    )


@given(val=st.integers(min_value=1))
def test_timeout_get(val, inst):
    """Get a timeout from device (ms) and turn into s."""
    # mock timeout value of device
    inst._dev.default_timeout = val

    ret_val = inst.timeout
    assert ret_val == u.Quantity(val, u.ms).to(u.s)


def test_timeout_set_unitless(inst):
    """Set a timeout value from device unitless (s)."""
    val = 1000
    inst.timeout = val
    set_val = inst._dev.default_timeout
    exp_val = 1000 * val
    assert set_val == exp_val


def test_timeout_set_minutes(inst):
    """Set a timeout value from device in minutes."""
    val = 10
    val_to_set = u.Quantity(val, u.min)
    inst.timeout = val_to_set
    set_val = inst._dev.default_timeout
    exp_val = 1000 * 60 * val
    assert set_val == exp_val


@mock.patch(patch_util)
def test_close(usb_util, inst):
    """Close the connection, release instrument."""
    inst.close()
    inst._dev.reset.assert_called()
    usb_util.dispose_resources.assert_called_with(inst._dev)


def test_read_raw(inst):
    """Read raw information from instrument."""
    msg = b"message\n"
    msg_exp = b"message"

    inst._ep_in.read.return_value = msg

    assert inst.read_raw() == msg_exp


def test_read_raw_size(inst):
    """If size is -1, read 1000 bytes."""
    msg = b"message\n"
    inst._ep_in.read.return_value = msg

    # set max package size
    max_size = 256
    inst._max_packet_size = max_size

    _ = inst.read_raw(size=-1)
    inst._ep_in.read.assert_called_with(max_size)


def test_read_raw_termination_char_not_found(inst):
    """Raise IOError if termination character not found."""
    msg = b"message"
    inst._ep_in.read.return_value = msg
    default_read_size = 1000

    inst._max_packet_size = default_read_size

    with pytest.raises(IOError) as err:
        _ = inst.read_raw()
    err_msg = err.value.args[0]
    assert (
        err_msg == f"Did not find the terminator in the returned "
        f"string. Total size of {default_read_size} might "
        f"not be enough."
    )


def test_write_raw(inst):
    """Write a message to the instrument."""
    msg = b"message\n"
    inst.write_raw(msg)
    inst._ep_out.write.assert_called_with(msg)


def test_seek(inst):
    """Raise NotImplementedError if `seek` is called."""
    with pytest.raises(NotImplementedError):
        inst.seek(42)


def test_tell(inst):
    """Raise NotImplementedError if `tell` is called."""
    with pytest.raises(NotImplementedError):
        inst.tell()


def test_flush_input(inst):
    """Flush the input out by trying to read until no more available."""
    inst._ep_in.read.side_effect = [b"message\n", usb.core.USBTimeoutError]
    inst.flush_input()
    inst._ep_in.read.assert_called()


def test_sendcmd(inst):
    """Send a command."""
    msg = "msg"
    msg_to_send = f"msg{inst._terminator}"

    inst.write = mock.MagicMock()

    inst._sendcmd(msg)
    inst.write.assert_called_with(msg_to_send)


def test_query(inst):
    """Query the instrument."""
    msg = "msg"
    size = 1000

    inst.sendcmd = mock.MagicMock()
    inst.read = mock.MagicMock()

    inst._query(msg, size=size)
    inst.sendcmd.assert_called_with(msg)
    inst.read.assert_called_with(size)
