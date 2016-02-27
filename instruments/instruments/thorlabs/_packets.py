#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module for working with ThorLabs packets.
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division

import struct

# STRUCTS #####################################################################

message_header_nopacket = struct.Struct('<HBBBB')
message_header_wpacket = struct.Struct('<HHBB')

# CLASSES #####################################################################


class ThorLabsPacket(object):

    """
    This class is used to wrap data to-/from- the instrument. Because of the
    command protocol for some ThorLabs instruments, this helps get all the
    data formatted and organized correctly.
    """

    # pylint: disable=too-many-arguments
    def __init__(self, message_id, param1=None, param2=None, dest=0x50,
                 source=0x01, data=None):

        if param1 is not None or param2 is not None:
            has_data = False
        elif data is not None:
            has_data = True
        else:
            raise ValueError("Must specify either parameters or data.")

        if not has_data and (data is not None):
            raise ValueError("A ThorLabs packet can either have parameters "
                             "or data, but not both.")
        if param1 is None and param2 is None and data is None:
            raise ValueError("You must specify either data or parameters.")

        self._message_id = message_id
        self._param1 = param1
        self._param2 = param2
        self._data = data
        self._has_data = has_data
        self._dest = dest
        self._source = source

    def __str__(self):
        return """
ThorLabs APT packet:
    Message ID      0x{0._message_id:x}
    Parameter 1     0x{0._param1:x}
    Parameter 2     0x{0._param2:x}
    Destination     0x{0._dest:x}
    Source          0x{0._source:x}
    Data            {1}
""".format(self, "{:x}".format(self._data) if self._has_data else "None")

    @property
    def message_id(self):
        """
        Gets/sets the message ID for the packet

        :type: `str`
        """
        return self._message_id

    @message_id.setter
    def message_id(self, newval):
        self._message_id = newval

    @property
    def parameters(self):
        """
        Gets/sets both parameters for the packet

        :type: `tuple`
        """
        return self._param1, self._param2

    @parameters.setter
    def parameters(self, newval):
        self._message_id = newval

    @property
    def destination(self):
        """
        Gets/sets the destination for the packet

        :type: `str`
        """
        return self._dest

    @destination.setter
    def destination(self, newval):
        self._dest = newval

    @property
    def source(self):
        """
        Gets/sets the source for the packet

        :type: `str`
        """
        return self._source

    @source.setter
    def source(self, newval):
        self._source = newval

    @property
    def data(self):
        """
        Gets/sets the data for the packet

        :type: `str`
        """
        return self._data

    @data.setter
    def data(self, newval):
        self._data = newval

    def pack(self):
        """
        Pack this `ThorLabsPacket` object into the byte string that can then
        be sent to the instrument.
        """
        if self._has_data:
            return message_header_wpacket.pack(
                self._message_id, len(
                    self._data), 0x80 | self._dest, self._source
            ) + self._data
        else:
            return message_header_nopacket.pack(
                self._message_id, self._param1, self._param2, self._dest,
                self._source
            )

    @classmethod
    def unpack(cls, bytes):
        """
        Classmethod used to unpack the response from an instrument into
        a new `ThorLabsPacket` object.

        :param bytes: Data from the instrument that will be unpacked into
            the packet object
        :type bytes: `str`

        :return: The unpacked data in a new packet object
        :rtype: `ThorLabsPacket`
        """
        if not bytes:
            raise ValueError("Expected a packet, got an empty string instead.")
        if len(bytes) < 6:
            raise ValueError("Packet must be at least 6 bytes long.")

        header = bytes[:6]

        # Check if 0x80 is set on header byte 4. If so, then this packet
        # has data.
        if struct.unpack("B", header[4])[0] & 0x80:
            msg_id, length, dest, source = message_header_wpacket.unpack(
                header)
            dest = dest ^ 0x80  # Turn off 0x80.
            param1 = None
            param2 = None
            data = bytes[6: 6 + length]  # Count on this to raise an index
                                         # error if the length doesn't match
                                         # up.
        else:
            msg_id, param1, param2, dest, source = message_header_nopacket.unpack(
                header)
            data = None

        return cls(message_id=msg_id, param1=param1, param2=param2, data=data,
                   dest=dest, source=source)
