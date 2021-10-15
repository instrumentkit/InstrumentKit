#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides a USB communicator for connecting with instruments over raw usb
connections.
"""

# IMPORTS #####################################################################


import io

import usb.core
import usb.util

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

    def __init__(self, dev):
        super(USBCommunicator, self).__init__(self)
        # TODO: Check to make sure this is a USB connection

        # follow (mostly) pyusb tutorial

        # set the active configuration. With no arguments, the first
        # configuration will be the active one
        dev.set_configuration()

        # get an endpoint instance
        cfg = dev.get_active_configuration()
        intf = cfg[(0, 0)]

        # initialize in and out endpoints
        ep_out = usb.util.find_descriptor(
            intf,
            # match the first OUT endpoint
            custom_match= \
                lambda e: \
                    usb.util.endpoint_direction(e.bEndpointAddress) == \
                    usb.util.ENDPOINT_OUT
        )

        ep_in = usb.util.find_descriptor(
            intf,
            # match the first OUT endpoint
            custom_match= \
                lambda e: \
                    usb.util.endpoint_direction(e.bEndpointAddress) == \
                    usb.util.ENDPOINT_IN
        )

        if (ep_in or ep_out) is None:
            raise IOError("USB endpoint not found.")

        self._dev = dev
        self._ep_in = ep_in
        self._ep_out = ep_out
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
                            "as a character string.")
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
        self._dev.reset()
        usb.util.dispose_resources(self._dev)

    def read_raw(self, size=1000):
        """Read raw string back from device and return.

        String returned is most likely shorter than the size requested. Will
        terminate by itself.
        Read size of -1 will be transformed into 1000.

        :param size: Size to read in bytes
        :type size: int
        """
        if size == -1:
            size = 1000
        read_val = bytes(self._ep_in.read(size))
        return read_val.rstrip(bytes(self._terminator, encoding="utf-8"))

    def read(self, size=1000, encoding="utf-8"):
        return self.read_raw(size).decode(encoding=encoding)

    def write_raw(self, msg):
        """Write bytes to the raw usb connection object.

        :param bytes msg: Bytes to be sent to the instrument over the usb
            connection.
        """
        msg = msg + bytes(self._terminator, encoding="utf-8")
        self._ep_out.write(msg)

    def write(self, msg, encoding="utf-8"):
        """Write string to usb connection.

        First, message is encoded and then termination character is added.

        :param msg: Message to send to instrument
        :type msg: str
        :param encoding: Encoding for message
        :type encoding: str
        """
        self.write_raw(bytes(f"{msg}{self._terminator}", encoding=encoding))

    def seek(self, offset):  # pylint: disable=unused-argument,no-self-use
        return NotImplemented

    def tell(self):  # pylint: disable=no-self-use
        return NotImplemented

    def flush_input(self):
        """
        Instruct the communicator to flush the input buffer, discarding the
        entirety of its contents. Read 1000 bytes at a time and be done
        once a timeout error comes back (which means the buffer is empty).
        """
        while True:
            try:
                self._ep_in.read(1000, 10)
            except usb.core.USBTimeoutError:
                break

    # METHODS #

    def _sendcmd(self, msg):
        """
        This is the implementation of ``sendcmd`` for communicating with
        raw usb connections. This function is in turn wrapped by the concrete
        method `AbstractCommunicator.sendcmd` to provide consistent logging
        functionality across all communication layers.

        :param str msg: The command message to send to the instrument
        """
        self.write(msg)

    def _query(self, msg, size=1000):
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
