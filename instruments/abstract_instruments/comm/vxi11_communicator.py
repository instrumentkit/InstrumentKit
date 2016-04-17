#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides a communication layer that uses python-vxi11 to interface with
VXI11 devices.
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io

from builtins import str, bytes

import vxi11

from instruments.abstract_instruments.comm import AbstractCommunicator

# CLASSES #####################################################################


class VXI11Communicator(io.IOBase, AbstractCommunicator):

    """
    Wraps a VXI-11 device. Arguments are all essentially just passed
    to `vxi11.Instrument`.

    VXI-11 is an RPC-based communication protocol over ethernet primarily used
    for connecting test and measurement equipment to controller hardware.
    VXI-11 allows for improved communication speeds and reduced latency over
    that of communicating using TCP over a socket connection.

    VXI-11 is developed and maintained by the IVI Foundation. More information
    can be found on their website, as well as that of the LXI standard website.

    VXI-11 has since been superseded by HiSLIP, which features fixes, improved
    performance, and new features such as IPv6 support.
    """

    def __init__(self, *args, **kwargs):
        super(VXI11Communicator, self).__init__(self)
        if vxi11 is None:
            raise ImportError("Package python-vxi11 is required for XVI11 "
                              "connected instruments.")
        AbstractCommunicator.__init__(self)

        self._inst = vxi11.Instrument(*args, **kwargs)

    # PROPERTIES #

    @property
    def address(self):
        """
        Gets the host and name for the vxi11 connection. Returns the ``host``
        and ``name`` in a list.

        :rtype: `list`[`str`]
        """
        return [self._inst.host, self._inst.name]

    @property
    def terminator(self):
        """
        Gets/sets the termination character for the VXI11 communication
        channel. This is apended to the end of commands when writing,
        and used to detect when transmission is done when receiving.

        :type: `str`
        """
        return self._inst.term_char

    @terminator.setter
    def terminator(self, newval):
        if isinstance(newval, bytes):
            newval = newval.decode("utf-8")
        if not isinstance(newval, str) or len(newval) > 1:
            raise TypeError("Terminator for VXI11 communicator must be "
                            "specified as a single character string.")
        self._inst.term_char = newval

    @property
    def timeout(self):
        """
        Gets/sets the communication timeout of the vxi11 comm channel.

        :type: `~quantities.Quantity`
        :units: As specified or assumed to be of units ``seconds``
        """
        return self._inst.timeout

    @timeout.setter
    def timeout(self, newval):
        self._inst.timeout = newval  # In seconds

    # FILE-LIKE METHODS #

    def close(self):
        """
        Shutdown and close the vxi11 connection.
        """
        try:
            self._inst.close()
        except IOError:
            pass

    def read_raw(self, size=-1):
        """
        Read bytes in from the vxi11 connection.

        :param int size: The number of bytes to be read in from the vxi11
            connection
        :rtype: `bytes`
        """
        return self._inst.read_raw(num=size)

    def write_raw(self, msg):
        """
        Write bytes to the vxi11 connection.

        :param bytes msg: Bytes to be written to the vxi11 connection
        """
        self._inst.write_raw(msg)

    def seek(self, offset):
        """
        Go to a specific offset for the input data source.

        Not implemented for vxi11 communicator.
        """
        raise NotImplementedError

    def tell(self):
        """
        Get the current positional offset for the input data source.

        Not implemented for vxi11 communicator.
        """
        raise NotImplementedError

    def flush_input(self):
        """
        Instruct the communicator to flush the input buffer, discarding the
        entirety of its contents.

        Not implemented for vxi11 communicator.
        """
        raise NotImplementedError

    # METHODS #

    def _sendcmd(self, msg):
        """
        This is the implementation of ``sendcmd`` for communicating with
        vxi11 connections. This function is in turn wrapped by the concrete
        method `AbstractCommunicator.sendcmd` to provide consistent logging
        functionality across all communication layers.

        :param str msg: The command message to send to the instrument
        """
        self.write(msg)

    def _query(self, msg, size=-1):
        """
        This is the implementation of ``query`` for communicating with
        vxi11 connections. This function is in turn wrapped by the concrete
        method `AbstractCommunicator.query` to provide consistent logging
        functionality across all communication layers.

        :param str msg: The query message to send to the instrument
        :param int size: The number of bytes to read back from the instrument
            response.
        :return: The instrument response to the query
        :rtype: `str`
        """
        return self._inst.ask(msg, num=size)
