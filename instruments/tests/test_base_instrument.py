#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing tests for the base Instrument class
"""

# IMPORTS ####################################################################

from __future__ import absolute_import

import socket
import io

from builtins import bytes

from nose.tools import raises
import mock

import numpy as np

import instruments as ik
from instruments.tests import expected_protocol
# pylint: disable=unused-import
from instruments.abstract_instruments.comm import (
    SocketCommunicator, USBCommunicator, VisaCommunicator, FileCommunicator,
    LoopbackCommunicator, GPIBCommunicator, AbstractCommunicator,
    USBTMCCommunicator, VXI11Communicator, serial_manager, SerialCommunicator
)

# TESTS ######################################################################

# pylint: disable=no-member,protected-access


# BINBLOCKREAD TESTS

def test_instrument_binblockread():
    with expected_protocol(
        ik.Instrument,
        [],
        [
            b"#210" + bytes.fromhex("00000001000200030004") + b"0",
        ],
        sep="\n"
    ) as inst:
        np.testing.assert_array_equal(inst.binblockread(2), [0, 1, 2, 3, 4])


def test_instrument_binblockread_two_reads():
    inst = ik.Instrument.open_test()
    data = bytes.fromhex("00000001000200030004")
    inst._file.read_raw = mock.MagicMock(
        side_effect=[b"#", b"2", b"10", data[:6], data[6:]]
    )

    np.testing.assert_array_equal(inst.binblockread(2), [0, 1, 2, 3, 4])

    calls_expected = [1, 1, 2, 10, 4]
    calls_actual = [call[0][0] for call in inst._file.read_raw.call_args_list]
    np.testing.assert_array_equal(calls_expected, calls_actual)


@raises(IOError)
def test_instrument_binblockread_too_many_reads():
    inst = ik.Instrument.open_test()
    data = bytes.fromhex("00000001000200030004")
    inst._file.read_raw = mock.MagicMock(
        side_effect=[b"#", b"2", b"10", data[:6], b"", b"", b""]
    )

    _ = inst.binblockread(2)


@raises(IOError)
def test_instrument_binblockread_bad_block_start():
    inst = ik.Instrument.open_test()
    inst._file.read_raw = mock.MagicMock(return_value=b"@")

    _ = inst.binblockread(2)


# OPEN CONNECTION TESTS

@mock.patch("instruments.abstract_instruments.instrument.SocketCommunicator")
@mock.patch("instruments.abstract_instruments.instrument.socket")
def test_instrument_open_tcpip(mock_socket, mock_socket_comm):
    mock_socket.socket.return_value.__class__ = socket.socket
    mock_socket_comm.return_value.__class__ = SocketCommunicator

    inst = ik.Instrument.open_tcpip("127.0.0.1", 1234)

    assert isinstance(inst._file, SocketCommunicator) is True

    # Check for call: SocketCommunicator(socket.socket())
    mock_socket_comm.assert_called_with(mock_socket.socket.return_value)


@mock.patch("instruments.abstract_instruments.instrument.serial_manager")
def test_instrument_open_serial(mock_serial_manager):
    mock_serial_manager.new_serial_connection.return_value.__class__ = SerialCommunicator

    inst = ik.Instrument.open_serial("/dev/port", baud=1234)

    assert isinstance(inst._file, SerialCommunicator) is True

    mock_serial_manager.new_serial_connection.assert_called_with(
        "/dev/port",
        baud=1234,
        timeout=3,
        write_timeout=3
    )


@mock.patch("instruments.abstract_instruments.instrument.GPIBCommunicator")
@mock.patch("instruments.abstract_instruments.instrument.serial_manager")
def test_instrument_open_gpibusb(mock_serial_manager, mock_gpib_comm):
    mock_serial_manager.new_serial_connection.return_value.__class__ = SerialCommunicator
    mock_gpib_comm.return_value.__class__ = GPIBCommunicator

    inst = ik.Instrument.open_gpibusb("/dev/port", gpib_address=1)

    assert isinstance(inst._file, GPIBCommunicator) is True

    mock_serial_manager.new_serial_connection.assert_called_with(
        "/dev/port",
        baud=460800,
        timeout=3,
        write_timeout=3
    )

    mock_gpib_comm.assert_called_with(
        mock_serial_manager.new_serial_connection.return_value,
        1
    )


@raises(ImportError)
@mock.patch("instruments.abstract_instruments.instrument.visa", new=None)
def test_instrument_open_visa_import_error():
    _ = ik.Instrument.open_visa("abc123")


@mock.patch("instruments.abstract_instruments.instrument.VisaCommunicator")
@mock.patch("instruments.abstract_instruments.instrument.visa")
def test_instrument_open_visa_new_version(mock_visa, mock_visa_comm):
    mock_visa_comm.return_value.__class__ = VisaCommunicator
    mock_visa.__version__ = "1.8"
    visa_open_resource = mock_visa.ResourceManager.return_value.open_resource

    inst = ik.Instrument.open_visa("abc123")

    assert isinstance(inst._file, VisaCommunicator) is True

    visa_open_resource.assert_called_with("abc123")
    mock_visa_comm.assert_called_with(visa_open_resource("abc123"))


@mock.patch("instruments.abstract_instruments.instrument.VisaCommunicator")
@mock.patch("instruments.abstract_instruments.instrument.visa")
def test_instrument_open_visa_old_version(mock_visa, mock_visa_comm):
    mock_visa_comm.return_value.__class__ = VisaCommunicator
    mock_visa.__version__ = "1.5"

    inst = ik.Instrument.open_visa("abc123")

    assert isinstance(inst._file, VisaCommunicator) is True

    mock_visa.instrument.assert_called_with("abc123")


def test_instrument_open_test():
    a = mock.MagicMock()
    b = mock.MagicMock()
    a.__class__ = io.BytesIO
    b.__class__ = io.BytesIO

    inst = ik.Instrument.open_test(stdin=a, stdout=b)

    assert isinstance(inst._file, LoopbackCommunicator)
    assert inst._file._stdin == a
    assert inst._file._stdout == b
