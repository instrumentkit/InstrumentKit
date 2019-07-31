#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# hpe3631a.py: Driver for the HP E3631A Power Supply
#
# © 2019 Francois Drielsma (francois.drielsma@gmail.com).
#
# This file is a part of the InstrumentKit project.
# Licensed under the AGPL version 3.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
"""
Driver for the HP E3631A Power Supply

Originally contributed and copyright held by Francois Drielsma
(francois.drielsma@gmail.com)

An unrestricted license has been provided to the maintainers of the Instrument
Kit project.
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division
import time

import quantities as pq

from instruments.abstract_instruments import (
    PowerSupply,
    PowerSupplyChannel
)
from instruments.util_fns import (
    ProxyList,
    unitful_property,
    bounded_unitful_property,
    bool_property
)

# CLASSES #####################################################################


class HPe3631a(PowerSupply):

    """
    The HPe3631a is three channels voltage/current supply.
    - Channel 1 is a positive +6V/5A channel (P6V)
    - Channel 2 is a positive +25V/1A channel (P25V)
    - Channel 3 is a negative -25V/1A channel (N25V)

    Example usage:

    >>> import instruments as ik
    >>> psu = ik.hp.HPe3631a.open_gpibusb("/dev/ttyUSB0", 10)
    >>> psu.channelid = 2   # Sets channel to P25V
    >>> psu.voltage = 12.5  # Sets voltage to 12.5V
    >>> print(psu.voltage)  # Reads back set current

    This module is designed for the power supply to be set to
    a specific channel and remain set afterwards as this device
    does not offer commands to set or read multiple channels
    without calling the channel set command each time (0.5s). It is
    possible to call a specific channel through psu.channel[idx],
    which will automatically reset the channel id, when necessary.

    This module is likely to work as is for the Agilent E3631 and
    Keysight E3631 which seem to be rebranded but identical devices.
    """

    def __init__(self, filelike):
        super(HPe3631a, self).__init__(filelike)
        self.channel_count = 3   # Total number of channels
        self.idx = 0             # Current channel to be set on the device
        self.channelid = 1       # Set the channel
        self.sendcmd('SYST:REM') # Puts the device in remote operation
        time.sleep(0.1)

    # INNER CLASSES #

    class Channel(PowerSupplyChannel):
        """
        Class representing a power output channel on the HPe3631a.

        .. warning:: This class should NOT be manually created by the user. It is
            designed to be initialized by the `HPe3631a` class.
        """

        def __init__(self, hp, idx):
            self._hp = hp
            self._idx = idx

        def sendcmd(self, cmd):
            """
            Function used to send a command to the instrument after
            checking that it is set to the right channel.

            :param str cmd: Command that will be sent to the instrument
            """
            if self._idx != self._hp.idx:
                self._hp.channelid = self._idx+1
            self._hp.sendcmd(cmd)

        def query(self, cmd):
            """
            Function used to send a command to the instrument after
            checking that it is set to the right channel.

            :param str cmd: Command that will be sent to the instrument
            :return: The result from the query
            :rtype: `str`
            """
            if self._idx != self._hp.idx:
                self._hp.channelid = self._idx+1
            return self._hp.query(cmd)

        # PROPERTIES #

        @property
        def mode(self):
            """
            Gets/sets the mode for the specified channel.
            """
            raise NotImplementedError

        @mode.setter
        def mode(self, newval):
            raise NotImplementedError

        voltage, voltage_min, voltage_max = bounded_unitful_property(
            "SOUR:VOLT",
            pq.volt,
            min_fmt_str="{}? MIN",
            max_fmt_str="{}? MAX",
            doc="""
            Gets/sets the output voltage of the source.

            :units: As specified, or assumed to be :math:`\\text{V}` otherwise.
            :type: `float` or `~quantities.Quantity`
            """
        )

        current, current_min, current_max = bounded_unitful_property(
            "SOUR:CURR",
            pq.amp,
            min_fmt_str="{}? MIN",
            max_fmt_str="{}? MAX",
            doc="""
            Gets/sets the output current of the source.

            :units: As specified, or assumed to be :math:`\\text{A}` otherwise.
            :type: `float` or `~quantities.Quantity`
            """
        )

        voltage_sense = unitful_property(
            "MEAS:VOLT",
            pq.volt,
            readonly=True,
            doc="""
            Gets the actual output voltage as measured by the sense wires.

            :units: As specified, or assumed to be :math:`\\text{V}` otherwise.
            :type: `float` or `~quantities.Quantity`
            """
        )

        current_sense = unitful_property(
            "MEAS:CURR",
            pq.amp,
            readonly=True,
            doc="""
            Gets the actual output current as measured by the sense wires.

            :units: As specified, or assumed to be :math:`\\text{A}` otherwise.
            :type: `float` or `~quantities.Quantity`
            """
        )

        output = bool_property(
            "OUTP",
            inst_true="1",
            inst_false="0s",
            doc="""
            Gets/sets the outputting status of the specified channel.

            This is a toggle setting. ON will turn on the channel output
            while OFF will turn it off.

            :type: `bool`
            """
        )

    # PROPERTIES ##

    @property
    def channel(self):
        """
        Gets a specific channel object. The desired channel is specified like
        one would access a list.

        :rtype: `HPe3631a.Channel`

        .. seealso::
            `HPe3631a` for example using this property.
        """
        return ProxyList(self, HPe3631a.Channel, range(self.channel_count))

    @property
    def channelid(self):
        """
        Select the active channel (0=P6V, 1=P25V, 2=N25V)
        """
        return self.idx+1

    @channelid.setter
    def channelid(self, newval):
        if newval not in [1, 2, 3]:
            raise ValueError('Channel {idx} not available, choose 1, 2 or 3'.format(idx=newval))
        self.idx = newval-1
        self.sendcmd('INST:NSEL {idx}'.format(idx=newval))
        time.sleep(0.5)

    @property
    def voltage(self):
        """
        Gets/sets the voltage for the current channel.

        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of units Volts.
        :type: `list` of `~quantities.quantity.Quantity` with units Volt
        """
        return self.channel[self.idx].voltage

    @voltage.setter
    def voltage(self, newval):
        self.channel[self.idx].voltage = newval

    @property
    def current(self):
        """
        Gets/sets the current for the current channel.

        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of units Amps.
        :type: `list` of `~quantities.quantity.Quantity` with units Amp
        """
        return self.channel[self.idx].current

    @current.setter
    def current(self, newval):
        self.channel[self.idx].current = newval

    @property
    def voltage_sense(self):
        """
        Gets/sets the voltage from the sense wires for the current channel.

        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of units Volts.
        :type: `list` of `~quantities.quantity.Quantity` with units Volt
        """
        return self.channel[self.idx].voltage_sense

    @voltage_sense.setter
    def voltage_sense(self, newval):
        self.channel[self.idx].voltage_sense = newval

    @property
    def current_sense(self):
        """
        Gets/sets the current from the sense wires for the current channel.

        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of units Amps.
        :type: `list` of `~quantities.quantity.Quantity` with units Amp
        """
        return self.channel[self.idx].current_sense

    @current_sense.setter
    def current_sense(self, newval):
        self.channel[self.idx].current_sense = newval

    @property
    def output(self):
        """
        Gets/sets the voltage for the current channel.

        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of units Volts.
        :type: `list` of `~quantities.quantity.Quantity` with units Volt
        """
        return self.channel[self.idx].output
