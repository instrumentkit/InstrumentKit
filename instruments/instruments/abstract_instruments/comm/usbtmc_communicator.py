#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides a communicator that uses Python-USBTMC for connecting with TMC
instruments.
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division

import io

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
        self._terminator = "\n"  # Use the system default line ending by default.

    # PROPERTIES ##

    @property
    def address(self):
        if hasattr(self._filelike, 'name'):
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
        return self._terminator

    @terminator.setter
    def terminator(self, newval):
        self._terminator = str(newval)

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

    def read(self, size):
        """
        Read bytes in from the usbtmc connection.

        :param int size: The number of bytes to read in from the usbtmc
            connection.
        :return: The read bytes
        :rtype: `str`
        """
        msg = self._inst.read_raw(size)
        return msg

    def write(self, msg):
        """
        Write bytes to the usbtmc connection.

        :param str msg: Bytes to be sent to the instrument over the usbtmc
            connection.
        """
        self._inst.write(msg)

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
        return self._inst.ask(msg)
