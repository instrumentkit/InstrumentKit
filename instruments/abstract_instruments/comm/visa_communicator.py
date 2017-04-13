#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides a VISA communicator for connecting with instruments via the VISA
library.
"""

# IMPORTS #####################################################################

# pylint: disable=wrong-import-position

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io
from builtins import str

import quantities as pq

from instruments.abstract_instruments.comm import AbstractCommunicator
from instruments.util_fns import assume_units

if not getattr(__builtins__, "WindowsError", None):
    class WindowsError(OSError):
        pass
try:
    import visa
except (ImportError, WindowsError, OSError):
    visa = None

# CLASSES #####################################################################


class VisaCommunicator(io.IOBase, AbstractCommunicator):

    """
    Communicates a connection exposed by the VISA library and exposes it as a
    file-like object.
    """

    def __init__(self, conn):
        super(VisaCommunicator, self).__init__(self)

        if visa is None:
            raise ImportError("PyVISA required for accessing VISA instruments.")

        version = int(visa.__version__.replace(".", ""))
        if (version < 160 and isinstance(conn, visa.Instrument)) or \
                (version >= 160 and isinstance(conn, visa.Resource)):
            self._conn = conn
            self._terminator = "\n"
        else:
            raise TypeError("VisaCommunicator must wrap a VISA Instrument.")

        # Make a bytearray for holding data read in from the device
        # so that we can buffer for two-argument read.
        self._buf = bytearray()

    # PROPERTIES #

    @property
    def address(self):
        """
        Gets the address or "resource name" for the VISA connection

        :type: `str`
        """
        return self._conn.resource_name

    @address.setter
    def address(self, newval):
        raise NotImplementedError("Changing addresses of a VISA Instrument "
                                  "is not supported.")

    @property
    def terminator(self):
        """
        Gets/sets the termination character used for VISA connections

        :type: `str`
        """
        return self._terminator

    @terminator.setter
    def terminator(self, newval):
        if not isinstance(newval, str):
            raise TypeError("Terminator for VisaCommunicator must be specified "
                            "as a single character string.")
        if len(newval) > 1:
            raise ValueError("Terminator for VisaCommunicator must only be 1 "
                             "character long.")
        self._terminator = newval

    @property
    def timeout(self):
        return self._conn.timeout * pq.second

    @timeout.setter
    def timeout(self, newval):
        newval = assume_units(newval, pq.second).rescale(pq.second).magnitude
        self._conn.timeout = newval

    # FILE-LIKE METHODS #

    def close(self):
        """
        Close the pyVISA connection object
        """
        try:
            self._conn.close()
        except IOError:
            pass

    def read_raw(self, size=-1):
        """
        Read bytes in from the pyVISA connection.

        :param int size: The number of bytes to read in from the VISA
            connection.

        :return: The read bytes from the VISA connection
        :rtype: `bytes`
        """
        if size >= 0:
            while len(self._buf) < size:
                data = self._conn.read()
                if data == "":
                    break
                self._buf += data
            msg = self._buf[:size]
            # Remove the front of the buffer.
            del self._buf[:size]
        elif size == -1:
            # Read the whole contents, appending the buffer we've already read.
            msg = self._buf + self._conn.read()
            # Reset the contents of the buffer.
            self._buf = bytearray()
        else:
            raise ValueError("Must read a positive value of characters, or "
                             "-1 for all characters.")
        return msg

    def write_raw(self, msg):
        """
        Write bytes to the VISA connection.

        :param bytes msg: Bytes to be sent to the instrument over the VISA
            connection.
        """
        self._conn.write(msg)

    def seek(self, offset):  # pylint: disable=unused-argument,no-self-use
        return NotImplemented

    def tell(self):  # pylint: disable=no-self-use
        return NotImplemented

    def flush_input(self):
        """
        Instruct the communicator to flush the input buffer, discarding the
        entirety of its contents.
        """
        # TODO: Find out how to flush with pyvisa
        pass

    # METHODS #

    def _sendcmd(self, msg):
        """
        This is the implementation of ``sendcmd`` for communicating with
        VISA connections. This function is in turn wrapped by the concrete
        method `AbstractCommunicator.sendcmd` to provide consistent logging
        functionality across all communication layers.

        :param str msg: The command message to send to the instrument
        """
        msg += self._terminator
        self.write(msg)

    def _query(self, msg, size=-1):
        """
        This is the implementation of ``query`` for communicating with
        VISA connections. This function is in turn wrapped by the concrete
        method `AbstractCommunicator.query` to provide consistent logging
        functionality across all communication layers.

        :param str msg: The query message to send to the instrument
        :param int size: The number of bytes to read back from the instrument
            response.
        :return: The instrument response to the query
        :rtype: `str`
        """
        msg += self._terminator
        return self._conn.ask(msg)
