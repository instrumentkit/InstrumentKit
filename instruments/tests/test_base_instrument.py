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
from instruments.errors import AcknowledgementError, PromptError

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


@mock.patch("instruments.abstract_instruments.instrument.VXI11Communicator")
def test_instrument_open_vxi11(mock_vxi11_comm):
    mock_vxi11_comm.return_value.__class__ = VXI11Communicator

    inst = ik.Instrument.open_vxi11("string", 1, key1="value")

    assert isinstance(inst._file, VXI11Communicator) is True

    mock_vxi11_comm.assert_called_with("string", 1, key1="value")


@mock.patch("instruments.abstract_instruments.instrument.USBTMCCommunicator")
def test_instrument_open_usbtmc(mock_usbtmc_comm):
    mock_usbtmc_comm.return_value.__class__ = USBTMCCommunicator

    inst = ik.Instrument.open_usbtmc("string", 1, key1="value")

    assert isinstance(inst._file, USBTMCCommunicator) is True

    mock_usbtmc_comm.assert_called_with("string", 1, key1="value")


@mock.patch("instruments.abstract_instruments.instrument.FileCommunicator")
def test_instrument_open_file(mock_file_comm):
    mock_file_comm.return_value.__class__ = FileCommunicator

    inst = ik.Instrument.open_file("filename")

    assert isinstance(inst._file, FileCommunicator) is True

    mock_file_comm.assert_called_with("filename")


# OPEN URI TESTS

@mock.patch("instruments.abstract_instruments.instrument.Instrument.open_serial")
def test_instrument_open_from_uri_serial(mock_open_conn):
    _ = ik.Instrument.open_from_uri("serial:///dev/foobar")

    mock_open_conn.assert_called_with("/dev/foobar", baud=115200)


@mock.patch("instruments.abstract_instruments.instrument.Instrument.open_serial")
def test_instrument_open_from_uri_serial_with_baud(mock_open_conn):
    _ = ik.Instrument.open_from_uri("serial:///dev/foobar?baud=230400")

    mock_open_conn.assert_called_with("/dev/foobar", baud=230400)


@mock.patch("instruments.abstract_instruments.instrument.Instrument.open_tcpip")
def test_instrument_open_from_uri_tcpip(mock_open_conn):
    _ = ik.Instrument.open_from_uri("tcpip://192.169.0.1:8080")

    mock_open_conn.assert_called_with("192.169.0.1", 8080)


@mock.patch("instruments.abstract_instruments.instrument.Instrument.open_gpibusb")
def test_instrument_open_from_uri_gpibusb(mock_open_conn):
    _ = ik.Instrument.open_from_uri("gpib+usb:///dev/foobar/15")

    mock_open_conn.assert_called_with("/dev/foobar", 15)


@mock.patch("instruments.abstract_instruments.instrument.Instrument.open_gpibusb")
def test_instrument_open_from_uri_gpibserial(mock_open_conn):
    _ = ik.Instrument.open_from_uri("gpib+serial:///dev/foobar/7")

    mock_open_conn.assert_called_with("/dev/foobar", 7)


@mock.patch("instruments.abstract_instruments.instrument.Instrument.open_visa")
def test_instrument_open_from_uri_visa(mock_open_conn):
    _ = ik.Instrument.open_from_uri("visa://USB::0x1234::0xFF12::0x7421::0::INSTR")

    mock_open_conn.assert_called_with("USB::0x1234::0xFF12::0x7421::0::INSTR")


@mock.patch("instruments.abstract_instruments.instrument.Instrument.open_usbtmc")
def test_instrument_open_from_uri_usbtmc(mock_open_conn):
    _ = ik.Instrument.open_from_uri("usbtmc://USB::0x1234::0xFF12::0x7421::0::INSTR")

    mock_open_conn.assert_called_with("USB::0x1234::0xFF12::0x7421::0::INSTR")


@mock.patch("instruments.abstract_instruments.instrument.Instrument.open_file")
def test_instrument_open_from_uri_file(mock_open_conn):
    _ = ik.Instrument.open_from_uri("file:///dev/filename")

    mock_open_conn.assert_called_with("/dev/filename")


@mock.patch("instruments.abstract_instruments.instrument.Instrument.open_vxi11")
def test_instrument_open_from_uri_vxi11(mock_open_conn):
    _ = ik.Instrument.open_from_uri("vxi11://TCPIP::192.168.1.105::gpib,5::INSTR")

    mock_open_conn.assert_called_with("TCPIP::192.168.1.105::gpib,5::INSTR")


@raises(NotImplementedError)
def test_instrument_open_from_uri_invalid_scheme():
    _ = ik.Instrument.open_from_uri("foo://bar")


# INIT TESTS

@raises(TypeError)
def test_instrument_init_bad_filelike():
    _ = ik.Instrument(mock.MagicMock())


def test_instrument_init():
    mock_filelike = mock.MagicMock()
    mock_filelike.__class__ = AbstractCommunicator
    inst = ik.Instrument(mock_filelike)

    assert inst._testing is False
    assert inst._prompt is None
    assert inst._terminator == "\n"
    assert inst._file == mock_filelike


def test_instrument_init_loopbackcomm():
    mock_filelike = mock.MagicMock()
    mock_filelike.__class__ = LoopbackCommunicator
    inst = ik.Instrument(mock_filelike)

    assert inst._testing is True


# COMM TESTS

def test_instrument_default_ack_expected():
    mock_filelike = mock.MagicMock()
    mock_filelike.__class__ = AbstractCommunicator
    inst = ik.Instrument(mock_filelike)

    assert inst._ack_expected() is None
    assert inst._ack_expected("foobar") is None


def test_instrument_sendcmd_noack_noprompt():
    mock_filelike = mock.MagicMock()
    mock_filelike.__class__ = AbstractCommunicator
    inst = ik.Instrument(mock_filelike)

    inst.sendcmd("foobar")

    inst._file.sendcmd.assert_called_with("foobar")


def test_instrument_sendcmd_noprompt():
    mock_filelike = mock.MagicMock()
    mock_filelike.__class__ = AbstractCommunicator
    inst = ik.Instrument(mock_filelike)

    def new_ack(msg):
        return msg

    inst._ack_expected = new_ack
    inst.read = mock.MagicMock(return_value="foobar")

    inst.sendcmd("foobar")
    inst.read.assert_called_with()
    inst._file.sendcmd.assert_called_with("foobar")


@raises(AcknowledgementError)
def test_instrument_sendcmd_bad_ack():
    mock_filelike = mock.MagicMock()
    mock_filelike.__class__ = AbstractCommunicator
    inst = ik.Instrument(mock_filelike)

    def new_ack(msg):
        return msg

    inst._ack_expected = new_ack
    inst.read = mock.MagicMock(return_value="derp")

    inst.sendcmd("foobar")


def test_instrument_sendcmd_noack():
    mock_filelike = mock.MagicMock()
    mock_filelike.__class__ = AbstractCommunicator
    inst = ik.Instrument(mock_filelike)

    inst.prompt = "> "
    inst.read = mock.MagicMock(return_value="> ")

    inst.sendcmd("foobar")
    inst.read.assert_called_with(2)
    inst._file.sendcmd.assert_called_with("foobar")


@raises(PromptError)
def test_instrument_sendcmd_noack_bad_prompt():
    mock_filelike = mock.MagicMock()
    mock_filelike.__class__ = AbstractCommunicator
    inst = ik.Instrument(mock_filelike)

    inst.prompt = "> "
    inst.read = mock.MagicMock(return_value="* ")

    inst.sendcmd("foobar")


def test_instrument_sendcmd():
    mock_filelike = mock.MagicMock()
    mock_filelike.__class__ = AbstractCommunicator
    inst = ik.Instrument(mock_filelike)

    def new_ack(msg):
        return msg

    inst._ack_expected = new_ack
    inst.prompt = "> "
    inst.read = mock.MagicMock(side_effect=["foobar", "> "])

    inst.sendcmd("foobar")
    inst.read.assert_any_call()
    inst.read.assert_any_call(2)
    inst._file.sendcmd.assert_called_with("foobar")
    assert inst.read.call_count == 2


def test_instrument_query_noack_noprompt():
    mock_filelike = mock.MagicMock()
    mock_filelike.__class__ = AbstractCommunicator
    inst = ik.Instrument(mock_filelike)
    inst._file.query.return_value = "datas"

    assert inst.query("foobar?") == "datas"

    inst._file.query.assert_called_with("foobar?", -1)


def test_instrument_query_noprompt():
    """
    Expected order of operations:

    - IK sends command to instrument
    - Instrument sends ACK, commonly an echo of the command
    - ACK is verified with _ack_expected function
    - If ACK is good, do another read which contains our return data
    """
    mock_filelike = mock.MagicMock()
    mock_filelike.__class__ = AbstractCommunicator
    inst = ik.Instrument(mock_filelike)
    inst._file.query.return_value = "foobar?"
    inst.read = mock.MagicMock(return_value="datas")

    def new_ack(msg):
        return msg

    inst._ack_expected = new_ack

    assert inst.query("foobar?") == "datas"
    inst._file.query.assert_called_with("foobar?")
    inst.read.assert_called_with(-1)


@raises(AcknowledgementError)
def test_instrument_query_bad_ack():
    mock_filelike = mock.MagicMock()
    mock_filelike.__class__ = AbstractCommunicator
    inst = ik.Instrument(mock_filelike)
    inst.read = mock.MagicMock(return_value="derp")

    def new_ack(msg):
        return msg

    inst._ack_expected = new_ack

    _ = inst.query("foobar?")


def test_instrument_query_noack():
    """
    Expected order of operations:

    - IK sends command to instrument and gets responce containing our data
    - Another read is done to capture the prompt characters sent by the
        instrument. Read should be equal to the length of the expected prompt
    - Exception is raised is prompt is not correct
    """
    mock_filelike = mock.MagicMock()
    mock_filelike.__class__ = AbstractCommunicator
    inst = ik.Instrument(mock_filelike)
    inst._file.query.return_value = "datas"

    inst.prompt = "> "
    inst.read = mock.MagicMock(return_value="> ")

    assert inst.query("foobar?") == "datas"
    inst._file.query.assert_called_with("foobar?", -1)
    inst.read.assert_called_with(2)


@raises(PromptError)
def test_instrument_query_noack_bad_prompt():
    mock_filelike = mock.MagicMock()
    mock_filelike.__class__ = AbstractCommunicator
    inst = ik.Instrument(mock_filelike)
    inst._file.query.return_value = "datas"

    inst.prompt = "> "
    inst.read = mock.MagicMock(return_value="* ")

    _ = inst.query("foobar?")


def test_instrument_query():
    """
    Expected order of operations:

    - IK sends command to instrument
    - Instrument sends ACK, commonly an echo of the command
    - ACK is verified with _ack_expected function
    - If ACK is good, do another read which contains our return data
    - Another read is done to capture the prompt characters sent by the
        instrument. Read should be equal to the length of the expected prompt
    - Exception is raised is prompt is not correct
    """
    mock_filelike = mock.MagicMock()
    mock_filelike.__class__ = AbstractCommunicator
    inst = ik.Instrument(mock_filelike)
    inst._file.query.return_value = "foobar?"
    inst.read = mock.MagicMock(side_effect=["datas", "> "])

    def new_ack(msg):
        return msg

    inst._ack_expected = new_ack
    inst.prompt = "> "

    assert inst.query("foobar?") == "datas"
    inst.read.assert_any_call(-1)
    inst.read.assert_any_call(2)
    inst._file.query.assert_called_with("foobar?")
    assert inst.read.call_count == 2


def test_instrument_read():
    mock_filelike = mock.MagicMock()
    mock_filelike.__class__ = AbstractCommunicator
    inst = ik.Instrument(mock_filelike)
    inst._file.read.return_value = "foobar"

    assert inst.read() == "foobar"
    inst._file.read.assert_called_with(-1)

    inst._file = mock.MagicMock()
    inst._file.read.return_value = "foobar"

    assert inst.read(6) == "foobar"
    inst._file.read.assert_called_with(6)


def test_instrument_write():
    mock_filelike = mock.MagicMock()
    mock_filelike.__class__ = AbstractCommunicator
    inst = ik.Instrument(mock_filelike)

    inst.write("foobar")
    inst._file.write.assert_called_with("foobar")


# PROPERTIES #

def test_instrument_timeout():
    mock_filelike = mock.MagicMock()
    mock_filelike.__class__ = AbstractCommunicator
    inst = ik.Instrument(mock_filelike)
    timeout = mock.PropertyMock(return_value=1)
    type(inst._file).timeout = timeout

    assert inst.timeout == 1
    timeout.assert_called_with()

    inst.timeout = 5
    timeout.assert_called_with(5)


def test_instrument_address():
    mock_filelike = mock.MagicMock()
    mock_filelike.__class__ = AbstractCommunicator
    inst = ik.Instrument(mock_filelike)
    address = mock.PropertyMock(return_value="/dev/foobar")
    type(inst._file).address = address

    assert inst.address == "/dev/foobar"
    address.assert_called_with()

    inst.address = "COM1"
    address.assert_called_with("COM1")


def test_instrument_terminator():
    mock_filelike = mock.MagicMock()
    mock_filelike.__class__ = AbstractCommunicator
    inst = ik.Instrument(mock_filelike)
    terminator = mock.PropertyMock(return_value="\n")
    type(inst._file).terminator = terminator

    assert inst.terminator == "\n"
    terminator.assert_called_with()

    inst.terminator = "*"
    terminator.assert_called_with("*")


def test_instrument_prompt():
    mock_filelike = mock.MagicMock()
    mock_filelike.__class__ = AbstractCommunicator
    inst = ik.Instrument(mock_filelike)

    assert inst.prompt is None

    inst.prompt = "> "
    assert inst.prompt == "> "

    inst.prompt = None
    assert inst.prompt is None
