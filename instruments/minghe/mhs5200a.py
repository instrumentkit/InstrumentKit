#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides the support for the MingHe low-cost function generator.

Class originally contributed by Catherine Holloway.
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division

from builtins import range
from enum import Enum

import quantities as pq
from instruments.abstract_instruments import Instrument, FunctionGenerator
from instruments.util_fns import ProxyList, assume_units

# CLASSES #####################################################################


class MHS5200(Instrument):
    """
    The MHS5200 is a low-cost, 2 channel function generator.

    There is no user manual, but Al Williams has reverse-engineered the
    communications protocol:
    https://github.com/wd5gnr/mhs5200a/blob/master/MHS5200AProtocol.pdf
    """
    def __init__(self, filelike):
        super(MHS5200, self).__init__(filelike)
        self._channel_count = 2

    # INNER CLASSES #

    class Channel(FunctionGenerator):
        """
        Class representing a channel on the MHS52000.
        """
        # pylint: disable=protected-access

        __CHANNEL_NAMES = {
            1: '1',
            2: '2'
        }

        def __init__(self, mhs, idx):
            self._mhs = mhs
            super(MHS5200.Channel, self).__init__(self._mhs._file)
            # Use zero-based indexing for the external API, but one-based
            # for talking to the instrument.
            self._idx = idx + 1
            self._chan = self.__CHANNEL_NAMES[self._idx]
            self._count = 0

        def _get_amplitude_(self):
            """
            Gets/Sets the amplitude of this channel.

            :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of units volt.
            :type: `~quantities.Quantity`
            """
            query = ":r{0}a".format(self._chan)
            response = self._mhs.query(query)
            return float(response.replace(query, ""))/100.0, self.VoltageMode.rms

        def _set_amplitude_(self, new_val, units):
            if units == self.VoltageMode.peak_to_peak or \
                            units == self.VoltageMode.rms:
                new_val = assume_units(new_val, "V").rescale(pq.V).magnitude
            elif units == self.VoltageMode.dBm:
                raise NotImplementedError("Decibel units are not supported.")
            new_val *= 100
            query = ":s{0}a{1}".format(self._chan, int(new_val))
            self._mhs.sendcmd(query)

        @property
        def duty_cycle(self):
            """
            Gets/Sets the duty cycle of this channel.

            :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of units seconds.
            :type: `~quantities.Quantity`
            """
            query = ":r{0}d".format(self._chan)
            response = self._mhs.query(query)
            duty = float(response.replace(query, ""))*pq.s
            return duty

        @duty_cycle.setter
        def duty_cycle(self, new_val):
            new_val = assume_units(new_val, pq.s).rescale(pq.s).magnitude
            query = ":s{0}d{1}".format(self._chan, int(new_val))
            self._mhs.sendcmd(query)

        @property
        def enable(self):
            """
            Gets/Sets the enable state of this channel.

            :param new_val: the enable state
            :type: `bool`
            """
            query = ":r{0}b".format(self._chan)
            return int(self._mhs.query(query).replace(query, "").
                       replace("\r", ""))

        @enable.setter
        def enable(self, new_val):
            query = ":s{0}b{1}".format(self._chan, int(new_val))
            self._mhs.sendcmd(query)

        @property
        def frequency(self):
            """
            Gets/Sets the frequency of this channel.

            :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of units hertz.
            :type: `~quantities.Quantity`
            """
            query = ":r{0}f".format(self._chan)
            response = self._mhs.query(query)
            freq = float(response.replace(query, ""))*pq.Hz
            return freq/100.0

        @frequency.setter
        def frequency(self, new_val):
            new_val = assume_units(new_val, pq.Hz).rescale(pq.Hz).\
                          magnitude*100.0
            query = ":s{0}f{1}".format(self._chan, int(new_val))
            self._mhs.sendcmd(query)

        @property
        def offset(self):
            """
            Gets/Sets the offset of this channel.

            :param new_val: The fraction of the duty cycle to offset the
            function by.
            :type: `float`
            """
            # need to convert
            query = ":r{0}o".format(self._chan)
            response = self._mhs.query(query)
            return int(response.replace(query, ""))/100.0-1.20

        @offset.setter
        def offset(self, new_val):
            new_val = int(new_val*100)+120
            query = ":s{0}o{1}".format(self._chan, new_val)
            self._mhs.sendcmd(query)

        @property
        def phase(self):
            """
            Gets/Sets the phase of this channel.

            :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of degrees.
            :type: `~quantities.Quantity`
            """
            # need to convert
            query = ":r{0}p".format(self._chan)
            response = self._mhs.query(query)
            return int(response.replace(query, ""))*pq.deg

        @phase.setter
        def phase(self, new_val):
            new_val = assume_units(new_val, pq.deg).rescale("deg").magnitude
            query = ":s{0}p{1}".format(self._chan, int(new_val))
            self._mhs.sendcmd(query)

        @property
        def function(self):
            """
            Gets/Sets the wave type of this channel.

            :type: `MHS5200.WaveType`
            """
            query = ":r{0}w".format(self._chan)
            response = self._mhs.query(query).replace(query, "")
            return self._mhs.Function(int(response))

        @function.setter
        def function(self, new_val):
            query = ":s{0}w{1}".format(self._chan,
                                       self._mhs.Function(new_val).value)
            self._mhs.sendcmd(query)

    class Function(Enum):
        """
        Enum containing valid wave modes for
        """
        sine = 0
        square = 1
        triangular = 2
        sawtooth_up = 3
        sawtooth_down = 4

    @property
    def channel(self):
        """
        Gets a specific channel object. The desired channel is specified like
        one would access a list.

        For instance, this would print the counts of the first channel::

        >>> mhs = ik.minghe.MHS5200.open_serial(vid=1027, pid=24577,
        baud=19200, timeout=1)
        >>> print(mhs.channel[0].frequency)

        :rtype: `CC1.Channel`
        """
        return ProxyList(self, MHS5200.Channel, range(self._channel_count))

    @property
    def serial_number(self):
        """
        Get the serial number, as an int

        :rtype: int
        """
        query = ":r0c"
        response = self.query(query)
        response = response.replace(query, "").replace("\r", "")
        return response
