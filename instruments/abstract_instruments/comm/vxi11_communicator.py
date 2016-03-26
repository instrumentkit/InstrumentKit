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

from instruments.abstract_instruments.comm import AbstractCommunicator

try:
    import vxi11
except ImportError:
    vxi11 = None

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
        if vxi11 is None:
            raise ImportError("Package python-vxi11 is required for XVI11 "
                              "connected instruments.")
        AbstractCommunicator.__init__(self)

        self._inst = vxi11.Instrument(*args, **kwargs)

    # PROPERTIES #

    @property
    def address(self):
        return [self._inst.host, self._inst.name]

    @property
    def terminator(self):
        return self._inst.term_char

    @terminator.setter
    def terminator(self, newval):
        self._inst.term_char = newval

    @property
    def timeout(self):
        return self._inst.timeout

    @timeout.setter
    def timeout(self, newval):
        self._inst.timeout = newval  # In seconds

    # FILE-LIKE METHODS #

    def close(self):
        try:
            self._inst.close()
        except IOError:
            pass

    def read_raw(self, size=-1):
        return self._inst.read_raw(num=size)

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
        self.write(msg)

    def _query(self, msg, size=-1):
        return self._inst.ask(msg, num=size)
