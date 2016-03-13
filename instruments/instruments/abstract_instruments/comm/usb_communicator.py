#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides a USB communicator for connecting with instruments over raw usb
connections.
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io
from builtins import str

from instruments.abstract_instruments.comm import AbstractCommunicator

# CLASSES #####################################################################


class USBCommunicator(io.IOBase, AbstractCommunicator):

    """
    This communicator is used to wrap a pyusb connection object. This is
    typically *not* the suggested way to interact with a USB-connected
    instrument. Most USB instruments can be interfaced through other
    communicators such as `FileCommunicator` (usbtmc on Linux),
    `VisaCommunicator`, or `USBTMCCommunicator`.

    .. warning:: The operational status of this communicator is unknown,
        and it is suggested that it is not relied on.
    """

    def __init__(self, conn):
        super(USBCommunicator, self).__init__(self)
        # TODO: Check to make sure this is a USB connection
        self._conn = conn
        self._terminator = "\n"

    # PROPERTIES #

    @property
    def address(self):
        raise NotImplementedError

    @address.setter
    def address(self, _):
        raise ValueError("Unable to change USB target address.")

    @property
    def terminator(self):
        """
        Gets/sets the termination character used for communicating with raw
        USB objects.
        :return:
        """
        return self._terminator

    @terminator.setter
    def terminator(self, newval):
        if not isinstance(newval, str):
            raise TypeError("Terminator for USBCommunicator must be specified "
                            "as a single character string.")
        if len(newval) > 1:
            raise ValueError("Terminator for USBCommunicator must only be 1 "
                             "character long.")
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
        Shutdown and close the USB connection
        """
        try:
            self._conn.shutdown()
        finally:
            self._conn.close()

    def read_raw(self, size=-1):
        raise NotImplementedError

    def read(self, size=-1, encoding="utf-8"):
        raise NotImplementedError

    def write_raw(self, msg):
        """
        Write bytes to the raw usb connection object.

        :param bytes msg: Bytes to be sent to the instrument over the usb
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

        Not implemented for usb communicator
        """
        raise NotImplementedError

    # METHODS #

    def _sendcmd(self, msg):
        """
        This is the implementation of ``sendcmd`` for communicating with
        raw usb connections. This function is in turn wrapped by the concrete
        method `AbstractCommunicator.sendcmd` to provide consistent logging
        functionality across all communication layers.

        :param str msg: The command message to send to the instrument
        """
        msg += self._terminator
        self._conn.sendall(msg)

    def _query(self, msg, size=-1):
        """
        This is the implementation of ``query`` for communicating with
        raw usb connections. This function is in turn wrapped by the concrete
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
