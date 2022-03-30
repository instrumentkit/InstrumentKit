#!/usr/bin/env python
"""
Provides a communicator that uses Python-USBTMC for connecting with TMC
instruments.
"""

# IMPORTS #####################################################################


import io

import usbtmc

from instruments.abstract_instruments.comm import AbstractCommunicator
from instruments.util_fns import assume_units
from instruments.units import ureg as u

# CLASSES #####################################################################


class USBTMCCommunicator(io.IOBase, AbstractCommunicator):

    """
    Wraps a USBTMC device. Arguments are passed to `usbtmc.Instrument`.
    """

    def __init__(self, *args, **kwargs):
        if usbtmc is None:
            raise ImportError("usbtmc is required for TMC instruments.")
        super().__init__(self)

        self._filelike = usbtmc.Instrument(*args, **kwargs)
        self._terminator = "\n"

    # PROPERTIES #

    @property
    def address(self):
        if hasattr(self._filelike, "name"):
            return id(self._filelike)  # TODO: replace with something more useful.

        return None

    @property
    def terminator(self):
        """
        Gets/sets the termination character used for communicating with the
        USBTMC instrument.

        :type: `str`
        """
        return chr(self._filelike.term_char)

    @terminator.setter
    def terminator(self, newval):
        if isinstance(newval, bytes):
            newval = newval.decode("utf-8")
        if not isinstance(newval, str) or len(newval) > 1:
            raise TypeError(
                "Terminator for loopback communicator must be "
                "specified as a single character string."
            )
        self._terminator = newval
        self._filelike.term_char = ord(newval)

    @property
    def timeout(self):
        """
        Gets/sets the communication timeout of the usbtmc comm channel.

        :type: `~pint.Quantity`
        :units: As specified or assumed to be of units ``seconds``
        """
        return self._filelike.timeout * u.second

    @timeout.setter
    def timeout(self, newval):
        newval = assume_units(newval, u.second).to(u.s).magnitude
        self._filelike.timeout = newval

    # FILE-LIKE METHODS #

    def close(self):
        """
        Close the USBTMC connection object
        """
        try:
            self._filelike.close()
        except OSError:
            pass

    def read(self, size=-1, encoding="utf-8"):
        """
        Read bytes in from the usbtmc connection, returning a decoded string
        using the provided encoding method.

        :param int size: The number of bytes to read in from the usbtmc
            connection.
        :param str encoding: Encoding that will be applied to the read bytes

        :return: The read string from the connection
        :rtype: `str`
        """
        return self._filelike.read(num=size, encoding=encoding)

    def read_raw(self, size=-1):
        """
        Read bytes in from the usbtmc connection.

        :param int size: The number of bytes to read in from the usbtmc
            connection.

        :return: The read bytes
        :rtype: `bytes`
        """
        return self._filelike.read_raw(num=size)

    def write(self, msg, encoding="utf-8"):
        """
        Write a string to the usbtmc connection. This string will be converted
        to `bytes` using the provided encoding method.

        :param str msg: String to be sent to the instrument over the usbtmc
            connection.
        :param str encoding: Encoding to apply on msg to convert the message
            into bytes
        """
        self._filelike.write(msg, encoding=encoding)

    def write_raw(self, msg):
        """
        Write bytes to the usbtmc connection.

        :param bytes msg: Bytes to be sent to the instrument over the usbtmc
            connection.
        """
        self._filelike.write_raw(msg)

    def seek(self, offset):
        raise NotImplementedError

    def tell(self):
        raise NotImplementedError

    def flush_input(self):
        """
        For a USBTMC connection, this function does not actually do anything
        and simply returns.
        """

    # METHODS #

    def _sendcmd(self, msg):
        """
        This is the implementation of ``sendcmd`` for communicating with
        usbtmc connections. This function is in turn wrapped by the concrete
        method `AbstractCommunicator.sendcmd` to provide consistent logging
        functionality across all communication layers.

        :param str msg: The command message to send to the instrument
        """
        self.write(msg)

    def _query(self, msg, size=-1):
        """
        This is the implementation of ``query`` for communicating with
        usbtmc connections. This function is in turn wrapped by the concrete
        method `AbstractCommunicator.query` to provide consistent logging
        functionality across all communication layers.

        :param str msg: The query message to send to the instrument
        :param int size: The number of bytes to read back from the instrument
            response.
        :return: The instrument response to the query
        :rtype: `str`
        """
        return self._filelike.ask(msg, num=size, encoding="utf-8")
