#!/usr/bin/env python
"""
Provides a VISA communicator for connecting with instruments via the VISA
library.
"""

# IMPORTS #####################################################################


import io

import pyvisa

from instruments.abstract_instruments.comm import AbstractCommunicator
from instruments.util_fns import assume_units
from instruments.units import ureg as u

# CLASSES #####################################################################


class VisaCommunicator(io.IOBase, AbstractCommunicator):

    """
    Communicates a connection exposed by the VISA library and exposes it as a
    file-like object.
    """

    def __init__(self, conn):
        super().__init__(self)

        self._terminator = None

        version = int(pyvisa.__version__.replace(".", "").ljust(3, "0"))
        # pylint: disable=no-member
        if (version < 160 and isinstance(conn, pyvisa.Instrument)) or (
            version >= 160 and isinstance(conn, pyvisa.Resource)
        ):
            self._conn = conn
            self.terminator = "\n"
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
        raise NotImplementedError(
            "Changing addresses of a VISA Instrument " "is not supported."
        )

    @property
    def read_termination(self):
        """Get / Set the read termination that is defined in pyvisa."""
        return self._conn.read_termination

    @read_termination.setter
    def read_termination(self, newval):
        if not isinstance(newval, str):
            raise TypeError(
                "Read terminator for VisaCommunicator must be specified as a string."
            )
        self._conn.read_termination = newval

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
            raise TypeError(
                "Terminator for VisaCommunicator must be specified as a string."
            )
        self._terminator = newval
        self.read_termination = newval
        self.write_termination = newval

    @property
    def timeout(self):
        return self._conn.timeout * u.second

    @timeout.setter
    def timeout(self, newval):
        newval = assume_units(newval, u.second).to(u.second).magnitude
        self._conn.timeout = newval

    @property
    def write_termination(self):
        """Get / Set the write termination that is defined in pyvisa."""
        return self._conn.write_termination

    @write_termination.setter
    def write_termination(self, newval):
        if not isinstance(newval, str):
            raise TypeError(
                "Write terminator for VisaCommunicator must be specified as a string."
            )
        self._conn.write_termination = newval

    # FILE-LIKE METHODS #

    def close(self):
        """
        Close the pyVISA connection object
        """
        try:
            self._conn.close()
        except OSError:
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
            self._buf += self._conn.read_bytes(size)
            msg = self._buf[:size]
            # Remove the front of the buffer.
            del self._buf[:size]

        elif size == -1:
            # Read the whole contents, appending the buffer we've already read.
            msg = self._buf + self._conn.read_raw()
            # Reset the contents of the buffer.
            self._buf = bytearray()
        else:
            raise ValueError(
                "Must read a positive value of characters, or " "-1 for all characters."
            )
        return msg

    def write_raw(self, msg):
        """
        Write bytes to the VISA connection.

        :param bytes msg: Bytes to be sent to the instrument over the VISA
            connection.
        """
        self._conn.write_raw(msg)

    def seek(self, offset):  # pylint: disable=unused-argument,no-self-use
        raise NotImplementedError

    def tell(self):  # pylint: disable=no-self-use
        raise NotImplementedError

    def flush_input(self):
        """
        Instruct the communicator to flush the input buffer, discarding the
        entirety of its contents.
        """
        # TODO: Find out how to flush with pyvisa

    # METHODS #

    def _sendcmd(self, msg):
        """
        This is the implementation of ``sendcmd`` for communicating with
        VISA connections. This function is in turn wrapped by the concrete
        method `AbstractCommunicator.sendcmd` to provide consistent logging
        functionality across all communication layers.
        Termination characters are automatically added by pyvisa.

        :param str msg: The command message to send to the instrument
        """
        self.write(msg)

    def _query(self, msg, size=-1):
        """
        This is the implementation of ``query`` for communicating with
        VISA connections. This function is in turn wrapped by the concrete
        method `AbstractCommunicator.query` to provide consistent logging
        functionality across all communication layers.
        Termination characters are automatically added by pyvisa.

        :param str msg: The query message to send to the instrument
        :param int size: The number of bytes to read back from the instrument
            response.
        :return: The instrument response to the query
        :rtype: `str`
        """
        return self._conn.query(msg)
