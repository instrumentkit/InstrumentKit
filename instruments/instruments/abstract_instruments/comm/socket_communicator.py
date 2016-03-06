#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides a tcpip socket communicator for connecting with instruments over
raw ethernet connections.
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division

import io
import socket

import quantities as pq

from instruments.abstract_instruments.comm import AbstractCommunicator
from instruments.util_fns import assume_units

# CLASSES #####################################################################


class SocketCommunicator(io.IOBase, AbstractCommunicator):

    """
    Communicates with a socket and makes it look like a `file`. Note that this
    is used instead of `socket.makefile`, as that method does not support
    timeouts. We do not support all features of `file`-like objects here, but
    enough to make `~instrument.Instrument` happy.
    """

    def __init__(self, conn):
        AbstractCommunicator.__init__(self)
        if isinstance(conn, socket.socket):
            self._conn = conn
            self._terminator = "\n"
        else:
            raise TypeError("SocketCommunicator must wrap a "
                            ":class:`socket.socket` object.")

    # PROPERTIES #

    @property
    def address(self):
        """
        Returns the socket peer address information as a tuple.
        """
        return self._conn.getpeername()

    @address.setter
    def address(self, newval):
        raise NotImplementedError("Unable to change address of sockets.")

    @property
    def terminator(self):
        return self._terminator

    @terminator.setter
    def terminator(self, newval):
        if not isinstance(newval, str):
            raise TypeError("Terminator for SocketCommunicator must be "
                            "specified as a single character string.")
        if len(newval) > 1:
            raise ValueError("Terminator for SocketCommunicator must only be 1 "
                             "character long.")
        self._terminator = newval

    @property
    def timeout(self):
        """
        Gets/sets the connection timeout of the socket comm channel.

        :type: `~quantities.Quantity`
        :units: As specified or assumed to be of units ``seconds``
        """
        return self._conn.gettimeout() * pq.second

    @timeout.setter
    def timeout(self, newval):
        newval = assume_units(newval, pq.second).rescale(pq.second).magnitude
        self._conn.settimeout(newval)

    # FILE-LIKE METHODS #

    def close(self):
        """
        Shutdown and close the `socket.socket` connection.
        """
        try:
            self._conn.shutdown()
        finally:
            self._conn.close()

    def read(self, size):
        """
        Read bytes in from the socket connection.

        :param int size: The number of bytes to read in from the socket
            connection.
        :return: The read bytes
        :rtype: `str`
        """
        if size >= 0:
            return self._conn.recv(size)
        elif size == -1:
            result = bytearray()
            c = 0
            while c != self._terminator:
                c = self._conn.recv(1)
                result += c
            return bytes(result)
        else:
            raise ValueError("Must read a positive value of characters.")

    def write(self, msg):
        """
        Write bytes to the `socket.socket` connection object.

        :param str msg: Bytes to be sent to the instrument over the socket
            connection.
        """
        self._conn.sendall(msg)

    def seek(self, offset):  # pylint: disable=unused-argument,no-self-use
        """
        Go to a specific offset for the input data source.

        Not implemented for socket communicator.
        """
        return NotImplemented

    def tell(self):  # pylint: disable=no-self-use
        """
        Get the current positional offset for the input data source.

        Not implemented for socket communicator.
        """
        return NotImplemented

    def flush_input(self):
        """
        Instruct the communicator to flush the input buffer, discarding the
        entirety of its contents.
        """
        _ = self.read(-1)  # Read in everything in the buffer and trash it

    # METHODS #

    def _sendcmd(self, msg):
        """
        This is the implementation of ``sendcmd`` for communicating with
        socket connections. This function is in turn wrapped by the concrete
        method `AbstractCommunicator.sendcmd` to provide consistent logging
        functionality across all communication layers.

        :param str msg: The command message to send to the instrument
        """
        msg += self._terminator
        self._conn.sendall(msg)

    def _query(self, msg, size=-1):
        """
        This is the implementation of ``query`` for communicating with
        socket connections. This function is in turn wrapped by the concrete
        method `AbstractCommunicator.query` to provide consistent logging
        functionality across all communication layers.

        :param str msg: The query message to send to the instrument
        :param int size: The number of bytes to read back from the instrument
            response.
        :return: The instrument response to the query
        :rtype: `str`
        """
        self.sendcmd(msg)
        resp = self.read(size)
        return resp
