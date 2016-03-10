#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides support for the Holzworth HS9000
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division

import quantities as pq

from instruments.abstract_instruments.signal_generator import (
    SignalGenerator,
    SGChannel
)
from instruments.util_fns import (
    ProxyList, split_unit_str, bounded_unitful_property, bool_property
)
from instruments.units import dBm

# CLASSES #####################################################################


class HS9000(SignalGenerator):

    """
    Communicates with a `Holzworth HS-9000 series`_ multi-channel frequency
    synthesizer.

    .. _Holzworth HS-9000 series: http://www.holzworth.com/synthesizers-multi.htm
    """

    # INNER CLASSES #

    class Channel(SGChannel):
        """
        Class representing a physical channel on the Holzworth HS9000

        .. warning:: This class should NOT be manually created by the user. It
        is designed to be initialized by the `HS9000` class.
        """

        def __init__(self, hs, idx_chan):
            self._hs = hs
            self._idx = idx_chan

            # We unpacked the channel index from the string of the form "CH1",
            # in order to make the API more Pythonic, but now we need to put
            # it back.
            # Some channel names, like "REF", are special and are preserved
            # as strs.
            self._ch_name = (
                idx_chan if isinstance(idx_chan, str)
                else "CH{}".format(idx_chan + 1)
            )

        # PRIVATE METHODS #

        def sendcmd(self, cmd):
            """
            Function used to send a command to the instrument while wrapping
            the command with the neccessary identifier for the channel.

            :param str cmd: Command that will be sent to the instrument after
                being prefixed with the channel identifier
            """
            self._hs.sendcmd(":{ch}:{cmd}".format(ch=self._ch_name, cmd=cmd))

        def query(self, cmd):
            """
            Function used to send a command to the instrument while wrapping
            the command with the neccessary identifier for the channel.

            :param str cmd: Command that will be sent to the instrument after
                being prefixed with the channel identifier
            :return: The result from the query
            :rtype: `str`
            """
            return self._hs.query(":{ch}:{cmd}".format(ch=self._ch_name, cmd=cmd))

        # STATE METHODS #

        def reset(self):
            """
            Resets the setting of the specified channel

            Example usage:
            >>> import instruments as ik
            >>> hs = ik.holzworth.HS9000.open_tcpip("192.168.0.2", 8080)
            >>> hs.channel[0].reset()
            """
            self.sendcmd("*RST")

        def recall_state(self):
            """
            Recalls the state of the specified channel from memory.

            Example usage:
            >>> import instruments as ik
            >>> hs = ik.holzworth.HS9000.open_tcpip("192.168.0.2", 8080)
            >>> hs.channel[0].recall_state()
            """
            self.sendcmd("*RCL")

        def save_state(self):
            """
            Saves the current state of the specified channel.

            Example usage:
            >>> import instruments as ik
            >>> hs = ik.holzworth.HS9000.open_tcpip("192.168.0.2", 8080)
            >>> hs.channel[0].save_state()
            """
            self.sendcmd("*SAV")

        # PROPERTIES #

        @property
        def temperature(self):
            """
            Gets the current temperature of the specified channel.

            :units: As specified by the instrument.
            :rtype: `~quantities.quantity.Quantity`
            """
            val, units = split_unit_str(self.query("TEMP?"))
            units = "deg{}".format(units)
            return pq.Quantity(val, units)

        frequency, frequency_min, frequency_max = bounded_unitful_property(
            "FREQ",
            units=pq.GHz,
            doc="""
            Gets/sets the frequency of the specified channel. When setting,
            values are bounded between what is returned by `frequency_min`
            and `frequency_max`.

            Example usage:
            >>> import instruments as ik
            >>> hs = ik.holzworth.HS9000.open_tcpip("192.168.0.2", 8080)
            >>> print(hs.channel[0].frequency)
            >>> print(hs.channel[0].frequency_min)
            >>> print(hs.channel[0].frequency_max)

            :type: `~quantities.quantity.Quantity`
            :units: As specified or assumed to be of units GHz
            """
        )
        power, power_min, power_max = bounded_unitful_property(
            "PWR",
            units=dBm,
            doc="""
            Gets/sets the output power of the specified channel. When setting,
            values are bounded between what is returned by `power_min`
            and `power_max`.

            Example usage:
            >>> import instruments as ik
            >>> hs = ik.holzworth.HS9000.open_tcpip("192.168.0.2", 8080)
            >>> print(hs.channel[0].power)
            >>> print(hs.channel[0].power_min)
            >>> print(hs.channel[0].power_max)

            :type: `~quantities.quantity.Quantity`
            :units: `instruments.units.dBm`
            """
        )
        phase, phase_min, phase_max = bounded_unitful_property(
            "PHASE",
            units=pq.degree,
            doc="""
            Gets/sets the output phase of the specified channel. When setting,
            values are bounded between what is returned by `phase_min`
            and `phase_max`.

            Example usage:
            >>> import instruments as ik
            >>> hs = ik.holzworth.HS9000.open_tcpip("192.168.0.2", 8080)
            >>> print(hs.channel[0].phase)
            >>> print(hs.channel[0].phase_min)
            >>> print(hs.channel[0].phase_max)

            :type: `~quantities.quantity.Quantity`
            :units: As specified or assumed to be of units degrees
            """
        )

        output = bool_property(
            "PWR:RF",
            inst_true="ON",
            inst_false="OFF",
            set_fmt="{}:{}",
            doc="""
            Gets/sets the output status of the channel. Setting to `True` will
            turn the channel's output stage on, while a value of `False` will
            turn it off.

            Example usage:
            >>> import instruments as ik
            >>> hs = ik.holzworth.HS9000.open_tcpip("192.168.0.2", 8080)
            >>> print(hs.channel[0].output)
            >>> hs.channel[0].output = True

            :type: `bool`
            """
        )

    # PROXY LIST ##

    def _channel_idxs(self):
        """
        Internal function used to get the list of valid channel names
        to be used by `HS9000.channel`

        :return: A list of valid channel indicies
        :rtype: `list` of `int` and `str`
        """
        # The command :ATTACH? returns a string of the form ":CH1:CH2" to
        # indicate what channels are attached to the internal USB bus.
        # We convert what channel names we can to integers, and leave the
        # rest as strings.
        return [
            (
                int(ch_name.replace("CH", "")) - 1
                if ch_name.startswith('CH') else
                ch_name.strip()
            )
            for ch_name in self.query(":ATTACH?").split(":")
            if ch_name
        ]

    @property
    def channel(self):
        """
        Gets a specific channel on the HS9000. The desired channel is accessed
        like one would access a list.

        Example usage:

        >>> import instruments as ik
        >>> hs = ik.holzworth.HS9000.open_tcpip("192.168.0.2", 8080)
        >>> print(hs.channel[0].frequency)

        :return: A channel object for the HS9000
        :rtype: `~HS9000.Channel`
        """
        return ProxyList(self, self.Channel, self._channel_idxs())

    # OTHER PROPERTIES #

    @property
    def name(self):
        """
        Gets identification string of the HS9000

        :return: The string as usually returned by ``*IDN?`` on SCPI instruments
        :rtype: `str`
        """
        # This is a weird one; the HS-9000 associates the :IDN? command
        # with each individual channel, though we want it to be a synthesizer-
        # wide property. To solve this, we assume that CH1 is always a channel
        # and ask its name.
        return self.channel[0].query("IDN?")

    @property
    def ready(self):
        """
        Gets the ready status of the HS9000.

        :return: If the instrument is ready for operation
        :rtype: `bool`
        """
        return "Ready" in self.query(":COMM:READY?")
