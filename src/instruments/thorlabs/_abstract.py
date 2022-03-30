#!/usr/bin/env python
"""
Defines a generic Thorlabs instrument to define some common functionality.
"""

# IMPORTS #####################################################################


import time

from instruments.units import ureg as u

from instruments.thorlabs import _packets
from instruments.abstract_instruments.instrument import Instrument
from instruments.util_fns import assume_units

# CLASSES #####################################################################


class ThorLabsInstrument(Instrument):

    """
    Generic class for ThorLabs instruments which require wrapping of
    commands and queries in packets.
    """

    def __init__(self, filelike):
        super().__init__(filelike)
        self.terminator = ""

    def sendpacket(self, packet):
        """
        Sends a packet to the connected APT instrument, and waits for a packet
        in response. Optionally, checks whether the received packet type is
        matches that the caller expects.

        :param packet: The thorlabs data packet that will be queried
        :type packet: `ThorLabsPacket`
        """
        self._file.write_raw(packet.pack())

    # pylint: disable=protected-access
    def querypacket(self, packet, expect=None, timeout=None, expect_data_len=None):
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

        :param timeout: Sets a timeout to wait before returning `None`, indicating
            no packet was received. If the timeout is set to `None`, then the
            timeout is inherited from the underlying communicator and no additional
            timeout is added. If timeout is set to `False`, then this method waits
            indefinitely. If timeout is set to a unitful quantity, then it is interpreted
            as a time and used as the timeout value. Finally, if the timeout is a unitless
            number (e.g. `float` or `int`), then seconds are assumed.

        :param int expect_data_len: Number of bytes to expect as the
            data for the returned packet.

        :return: Returns the response back from the instrument wrapped up in
            a ThorLabs APT packet, or None if no packet was received.
        :rtype: `ThorLabsPacket`
        """
        t_start = time.time()

        if timeout is not None:
            timeout = assume_units(timeout, u.second).to("second").magnitude

        while True:
            self._file.write_raw(packet.pack())
            resp = self._file.read_raw(
                expect_data_len + 6  # the header is six bytes.
                if expect_data_len
                else 6
            )
            if resp or timeout is None:
                break
            else:
                tic = time.time()
                if tic - t_start > timeout:
                    break

        if not resp:
            if expect is None:
                return None
            else:
                raise OSError(f"Expected packet {expect}, got nothing instead.")
        pkt = _packets.ThorLabsPacket.unpack(resp)
        if expect is not None and pkt._message_id != expect:
            # TODO: make specialized subclass that can record the offending
            #       packet.
            raise OSError(
                "APT returned message ID {}, expected {}".format(
                    pkt._message_id, expect
                )
            )

        return pkt
