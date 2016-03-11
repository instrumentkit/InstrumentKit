#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides a communicator that uses Python-USBTMC for connecting with TMC
instruments.
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io
from builtins import str, bytes

try:
    import usbtmc
except ImportError:
    usbtmc = None

from instruments.abstract_instruments.comm import AbstractCommunicator

# CLASSES #####################################################################


class USBTMCCommunicator(io.IOBase, AbstractCommunicator):

    """
    Wraps a USBTMC device. Arguments are passed to `usbtmc.Instrument`.
    """

    def __init__(self, *args, **kwargs):
        if usbtmc is None:
            raise ImportError("usbtmc is required for TMC instruments.")
        super(USBTMCCommunicator, self).__init__(self)

        self._inst = usbtmc.Instrument(*args, **kwargs)
        self._terminator = "\n"

    # PROPERTIES #

    @property
    def address(self):
        if hasattr(self._filelike, "name"):
            return id(self._inst)  # TODO: replace with something more useful.
        else:
            return None

    @property
    def terminator(self):
        """
        Gets/sets the termination character used for communicating with the
        USBTMC instrument.

        :type: `str`
        """
        return self._inst.term_char

    @terminator.setter
    def terminator(self, newval):
        if isinstance(newval, bytes):
            newval = newval.decode("utf-8")
        if not isinstance(newval, str) or len(newval) > 1:
            raise TypeError("Terminator for loopback communicator must be "
                            "specified as a single character string.")
        self._terminator = newval

    @property
    def timeout(self):
        raise NotImplementedError

    @timeout.setter
    def timeout(self, newval):
        raise NotImplementedError

    # FILE-LIKE METHODS #

    def close(self):
        """
        Close the USBTMC connection object
        """
        try:
            self._filelike.close()
        except IOError:
            pass

    def read(self, size=-1, encoding="utf-8"):
        return self._inst.read(num=size, encoding=encoding)

    def read_raw(self, size=-1):
        """
        Read bytes in from the usbtmc connection.

        :param int size: The number of bytes to read in from the usbtmc
            connection.
        :return: The read bytes
        :rtype: `str`
        """
        return self._inst.read_raw(num=size)

    def write(self, msg, encoding="utf-8"):
        """
        Write bytes to the usbtmc connection.

        :param str msg: Bytes to be sent to the instrument over the usbtmc
            connection.
        """
        self._inst.write(msg, encoding=encoding)

    def write_raw(self, msg):
        self._inst.write_raw(msg)

    def seek(self, offset):
        raise NotImplementedError

    def tell(self):
        raise NotImplementedError

    def flush_input(self):
        raise NotImplementedError

    # METHODS #

    def _sendcmd(self, msg):
        """
        This is the implementation of ``sendcmd`` for communicating with
        usbtmc connections. This function is in turn wrapped by the concrete
        method `AbstractCommunicator.sendcmd` to provide consistent logging
        functionality across all communication layers.

        :param str msg: The command message to send to the instrument
        """
        self._inst.write("{}{}".format(msg, self.terminator))

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
        return self._inst.ask(msg, num=size, encoding="utf-8")
