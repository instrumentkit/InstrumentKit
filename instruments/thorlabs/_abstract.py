#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines a generic Thorlabs instrument to define some common functionality.
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division

from instruments.thorlabs import _packets
from instruments.abstract_instruments.instrument import Instrument

# CLASSES #####################################################################


class ThorLabsInstrument(Instrument):

    """
    Generic class for ThorLabs instruments which require wrapping of
    commands and queries in packets.
    """

    def __init__(self, filelike):
        super(ThorLabsInstrument, self).__init__(filelike)
        self.terminator = ''

    def sendpacket(self, packet):
        """
        Sends a packet to the connected APT instrument, and waits for a packet
        in response. Optionally, checks whether the received packet type is
        matches that the caller expects.

        :param packet: The thorlabs data packet that will be queried
        :type packet: `ThorLabsPacket`
        """
        self.sendcmd(packet.pack())

    # pylint: disable=protected-access
    def querypacket(self, packet, expect=None):
        """
        Sends a packet to the connected APT instrument, and waits for a packet
        in response. Optionally, checks whether the received packet type is
        matches that the caller expects.

        :param packet: The thorlabs data packet that will be queried
        :type packet: `ThorLabsPacket`

        :param expect: The expected message id from the response. If an
            an incorrect id is received then an `IOError` is raised. If left
            with the default value of `None` then no checking occurs.
        :type expect: `str` or `None`

        :return: Returns the response back from the instrument wrapped up in
            a thorlabs packet
        :rtype: `ThorLabsPacket`
        """
        resp = self.query(packet.pack())
        if not resp:
            if expect is None:
                return None
            else:
                raise IOError("Expected packet {}, got nothing instead.".format(
                    expect
                ))
        pkt = _packets.ThorLabsPacket.unpack(resp)
        if expect is not None and pkt._message_id != expect:
            # TODO: make specialized subclass that can record the offending
            #       packet.
            raise IOError("APT returned message ID {}, expected {}".format(
                pkt._message_id, expect
            ))
        return pkt
