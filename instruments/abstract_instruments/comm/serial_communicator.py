#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides a serial communicator for connecting with instruments over serial
connections.
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io

from builtins import bytes, str
import serial

import quantities as pq

from instruments.abstract_instruments.comm import AbstractCommunicator
from instruments.util_fns import assume_units

# CLASSES #####################################################################


class SerialCommunicator(io.IOBase, AbstractCommunicator):

    """
    Wraps a `pyserial.Serial` object to add a few properties as well as
    handling of termination characters.
    """

    def __init__(self, conn):
        super(SerialCommunicator, self).__init__(self)

        if isinstance(conn, serial.Serial):
            self._conn = conn
            self._terminator = "\n"
            self._debug = False
        else:
            raise TypeError("SerialCommunicator must wrap a serial.Serial "
                            "object.")

    # PROPERTIES #

    @property
    def address(self):
        """
        Gets/sets the address port for the serial object.

        :type: `str`
        """
        return self._conn.port

    @address.setter
    def address(self, newval):
        # TODO: Input checking on Serial port newval
        # TODO: Add port changing capability to serialmanager
        # self._conn.port = newval
        raise NotImplementedError

    @property
    def terminator(self):
        """
        Gets/sets the termination character for the serial communication
        channel. This is apended to the end of commands when writing,
        and used to detect when transmission is done when receiving.

        :type: `str`
        """
        return self._terminator

    @terminator.setter
    def terminator(self, newval):
        if isinstance(newval, bytes):
            newval = newval.decode("utf-8")
        if not isinstance(newval, str) or len(newval) > 1:
            raise TypeError("Terminator for serial communicator must be "
                            "specified as a single character string.")
        self._terminator = newval

    @property
    def timeout(self):
        """
        Gets/sets the communication timeout of the serial comm channel.

        :type: `~quantities.Quantity`
        :units: As specified or assumed to be of units ``seconds``
        """
        return self._conn.timeout * pq.second

    @timeout.setter
    def timeout(self, newval):
        newval = assume_units(newval, pq.second).rescale(pq.second).magnitude
        self._conn.timeout = newval

    # FILE-LIKE METHODS #

    def close(self):
        """
        Shutdown and close the `pyserial.Serial` connection.
        """
        try:
            self._conn.shutdown()
        finally:
            self._conn.close()

    def read_raw(self, size=-1):
        """
        Read bytes in from the serial port.

        :param int size: The number of bytes to be read in from the serial port
        :rtype: `bytes`
        """
        if size >= 0:
            resp = self._conn.read(size)
            return resp
        elif size == -1:
            result = bytes()
            c = b''
            while c != self._terminator.encode("utf-8"):
                c = self._conn.read(1)
                if c == b"":
                    raise IOError("Serial connection timed out before reading "
                                  "a termination character.")
                if c != self._terminator.encode("utf-8"):
                    result += c
            return result
        else:
            raise ValueError("Must read a positive value of characters.")

    def write_raw(self, msg):
        """
        Write bytes to the `pyserial.Serial` object.

        :param bytes msg: Bytes to be written to the serial port
        """
        self._conn.write(msg)

    def seek(self, offset):  # pylint: disable=unused-argument,no-self-use
        """
        Go to a specific offset for the input data source.

        Not implemented for serial communicator.
        """
        raise NotImplementedError

    def tell(self):  # pylint: disable=no-self-use
        """
        Get the current positional offset for the input data source.

        Not implemented for serial communicator.
        """
        raise NotImplementedError

    def flush_input(self):
        """
        Instruct the communicator to flush the input buffer, discarding the
        entirety of its contents.

        Calls the pyserial flushInput() method.
        """
        self._conn.flushInput()

    # METHODS #

    def _sendcmd(self, msg):
        """
        This is the implementation of ``sendcmd`` for communicating with
        serial connections. This function is in turn wrapped by the concrete
        method `AbstractCommunicator.sendcmd` to provide consistent logging
        functionality across all communication layers.

        :param str msg: The command message to send to the instrument
        """
        msg += self._terminator
        self.write(msg)

    def _query(self, msg, size=-1):
        """
        This is the implementation of ``query`` for communicating with
        serial connections. This function is in turn wrapped by the concrete
        method `AbstractCommunicator.query` to provide consistent logging
        functionality across all communication layers.

        :param str msg: The query message to send to the instrument
        :param int size: The number of bytes to read back from the instrument
            response.
        :return: The instrument response to the query
        :rtype: `str`
        """
        self.sendcmd(msg)
        return self.read(size)
