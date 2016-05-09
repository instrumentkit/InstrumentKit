#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides a tcpip socket communicator for connecting with instruments over
raw ethernet connections.
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io
import socket

from builtins import str, bytes
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
        super(SocketCommunicator, self).__init__(self)

        if isinstance(conn, socket.socket):
            self._conn = conn
            self._terminator = "\n"
        else:
            raise TypeError("SocketCommunicator must wrap a "
                            ":class:`socket.socket` object, instead got "
                            "{}".format(type(conn)))

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
        if isinstance(newval, bytes):
            newval = newval.decode("utf-8")
        if not isinstance(newval, str) or len(newval) > 1:
            raise TypeError("Terminator for socket communicator must be "
                            "specified as a single character string.")
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

    def read_raw(self, size=-1):
        """
        Read bytes in from the socket connection.

        :param int size: The number of bytes to read in from the socket
            connection.
        :return: The read bytes
        :rtype: `bytes`
        """
        if size >= 0:
            return self._conn.recv(size)
        elif size == -1:
            result = bytes()
            c = b''
            while c != self._terminator.encode("utf-8"):
                c = self._conn.recv(1)
                if c == b"":
                    raise IOError("Socket connection timed out before reading "
                                  "a termination character.")
                if c != self._terminator.encode("utf-8"):
                    result += c
            return result
        else:
            raise ValueError("Must read a positive value of characters.")

    def write_raw(self, msg):
        """
        Write bytes to the `socket.socket` connection object.

        :param bytes msg: Bytes to be sent to the instrument over the socket
            connection.
        """
        self._conn.sendall(msg)

    def seek(self, offset):  # pylint: disable=unused-argument,no-self-use
        """
        Go to a specific offset for the input data source.

        Not implemented for socket communicator.
        """
        raise NotImplementedError

    def tell(self):  # pylint: disable=no-self-use
        """
        Get the current positional offset for the input data source.

        Not implemented for socket communicator.
        """
        raise NotImplementedError

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
        self.write(msg)

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
