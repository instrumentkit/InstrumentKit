# -*- coding: utf-8 -*-
"""
Unit tests for the Cryomagnetics serial communication layer
"""

# IMPORTS #####################################################################

from __future__ import absolute_import

from nose.tools import raises, eq_
from threading import Lock
import mock
import serial

from instruments.abstract_instruments.comm \
    import SerialCommunicator
from instruments.abstract_instruments.comm \
    import CryomagneticsSerialCommunicator

# TEST CASES ##################################################################

# pylint: disable=protected-access


def test_comm_init():
    comm = CryomagneticsSerialCommunicator(serial.Serial())
    eq_(comm._maximum_message_size, 140)
    assert isinstance(comm, SerialCommunicator) is True
    assert isinstance(comm._conn, serial.Serial) is True


@raises(TypeError)
def test_serialcomm_init_wrong_filelike():
    _ = CryomagneticsSerialCommunicator("derp")


def test_maximum_message_size():
    comm = CryomagneticsSerialCommunicator(serial.Serial())
    desired_maximum = 160
    comm.maximum_message_size = desired_maximum

    eq_(comm.maximum_message_size, desired_maximum)


def test_query_happy_path():
    command = 'command'
    expected_response = 'response'
    device_response = '%s\r\n%s\r\n' % (command, expected_response)

    comm = CryomagneticsSerialCommunicator(serial.Serial())
    comm.read = mock.MagicMock(return_value=device_response)
    comm.write = mock.MagicMock()

    comm._querying_lock = mock.MagicMock(spec=Lock().__class__)

    eq_(expected_response, comm._query(command, size=-1))

    comm.read.assert_called_once_with(size=comm.maximum_message_size)
    comm.write.assert_called_once_with(command + '\r')
    comm._querying_lock.acquire.assert_called_once()
    comm._querying_lock.release.assert_called_once()


def test_query_non_default_size():
    command = 'command'
    expected_response = 'response'
    size = 1000
    device_response = '%s\r\n%s\r\n' % (command, expected_response)

    comm = CryomagneticsSerialCommunicator(serial.Serial())
    comm.read = mock.MagicMock(return_value=device_response)
    comm.write = mock.MagicMock()
    comm._querying_lock = mock.MagicMock(spec=Lock().__class__)

    eq_(expected_response, comm._query(command, size=size))

    comm.read.assert_called_once_with(size=size)


def test_query_no_echoed_command():
    command = 'command'
    expected_response = 'response'
    device_response = expected_response

    comm = CryomagneticsSerialCommunicator(serial.Serial())
    comm.read = mock.MagicMock(return_value=device_response)
    comm.write = mock.MagicMock()
    comm._querying_lock = mock.MagicMock(spec=Lock().__class__)

    @raises(RuntimeError)
    def kaboom():
        comm._query(command)

    kaboom()
    comm._querying_lock.release.assert_called_once()


def test_query_no_response():
    command = 'command'
    device_response = command + '\r\n'

    comm = CryomagneticsSerialCommunicator(serial.Serial())
    comm.read = mock.MagicMock(return_value=device_response)
    comm.write = mock.MagicMock()
    comm._querying_lock = mock.MagicMock(spec=Lock().__class__)

    @raises(RuntimeError)
    def kaboom():
        comm._query(command)

    kaboom()
    comm._querying_lock.release.assert_called_once()


def test_query_non_matching_command():
    command = 'command'
    response = 'response'
    non_matching_command = 'bad command'
    device_response = '%s\r\n%s\r\n' % (non_matching_command, response)

    comm = CryomagneticsSerialCommunicator(serial.Serial())
    comm.read = mock.MagicMock(return_value=device_response)
    comm.write = mock.MagicMock()
    comm._querying_lock = mock.MagicMock(spec=Lock().__class__)

    @raises(RuntimeError)
    def kaboom():
        comm._query(command)

    kaboom()
    comm.write.assert_called_once_with(command + '\r')
    comm._querying_lock.release.assert_called_once()
