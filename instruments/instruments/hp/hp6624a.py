#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides support for the HP6624a power supply
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division
from builtins import range

import quantities as pq
from enum import Enum

from instruments.abstract_instruments import (
    PowerSupply,
    PowerSupplyChannel
)
from instruments.util_fns import assume_units, ProxyList

# CLASSES #####################################################################


class HP6624a(PowerSupply):

    """
    The HP6624a is a multi-output power supply.

    This class can also be used for HP662xa, where x=1,2,3,4,7. Note that some
    models have less channels then the HP6624 and it is up to the user to take
    this into account. This can be changed with the `~HP6624a.channel_count`
    property.

    Example usage:

    >>> import instruments as ik
    >>> psu = ik.hp.HP6624a.open_gpibusb('/dev/ttyUSB0', 1)
    >>> psu.channel[0].voltage = 10 # Sets channel 1 voltage to 10V.
    """

    def __init__(self, filelike):
        super(HP6624a, self).__init__(filelike)
        self._channel_count = 4

    # INNER CLASSES #

    class Channel(PowerSupplyChannel):
        """
        Class representing a power output channel on the HP6624a.

        .. warning:: This class should NOT be manually created by the user. It is
            designed to be initialized by the `HP6624a` class.
        """

        def __init__(self, hp, idx):
            self._hp = hp
            self._idx = idx + 1

        # PRIVATE METHODS #

        def _format_cmd(self, cmd):
            cmd = cmd.split(" ")
            if len(cmd) == 1:
                cmd = "{cmd} {idx}".format(cmd=cmd[0], idx=self._idx)
            else:
                cmd = "{cmd} {idx},{value}".format(cmd=cmd[0], idx=self._idx, value=cmd[1])
            return cmd

        def sendcmd(self, cmd):
            """
            Function used to send a command to the instrument while wrapping
            the command with the neccessary identifier for the channel.

            :param str cmd: Command that will be sent to the instrument after
                being prefixed with the channel identifier
            """
            cmd = self._format_cmd(cmd)
            self._hp.sendcmd(cmd)

        def query(self, cmd):
            """
            Function used to send a command to the instrument while wrapping
            the command with the neccessary identifier for the channel.

            :param str cmd: Command that will be sent to the instrument after
                being prefixed with the channel identifier
            :return: The result from the query
            :rtype: `str`
            """
            cmd = self._format_cmd(cmd)
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

        @property
        def voltage(self):
            """
            Gets/sets the voltage of the specified channel. If the device is in
            constant current mode, this sets the voltage limit.

            Note there is no bounds checking on the value specified.

            :units: As specified, or assumed to be :math:`\\text{V}` otherwise.
            :type: `float` or `~quantities.Quantity`
            """
            return pq.Quantity(float(self._hp.query(
                'VSET? {}'.format(self._idx)).strip()), pq.volt)

        @voltage.setter
        def voltage(self, newval):
            self._hp.sendcmd('VSET {},{}'.format(
                self._idx,
                assume_units(newval, pq.volt).rescale(pq.volt).magnitude,
            ))

        @property
        def current(self):
            """
            Gets/sets the current of the specified channel. If the device is in
            constant voltage mode, this sets the current limit.

            Note there is no bounds checking on the value specified.

            :units: As specified, or assumed to be :math:`\\text{A}` otherwise.
            :type: `float` or `~quantities.Quantity`
            """
            return pq.Quantity(float(self._hp.query(
                'ISET? {}'.format(self._idx)).strip()), pq.amp)

        @current.setter
        def current(self, newval):
            self._hp.sendcmd('ISET {},{}'.format(
                self._idx,
                assume_units(newval, pq.amp).rescale(pq.amp).magnitude
            ))

        @property
        def voltage_sense(self):
            """
            Gets the actual voltage as measured by the sense wires for the
            specified channel.

            :units: :math:`\\text{V}` (volts)
            :rtype: `~quantities.Quantity`
            """
            return pq.Quantity(float(self._hp.query(
                'VOUT? {}'.format(self._idx)).strip()), pq.volt)

        @property
        def current_sense(self):
            """
            Gets the actual output current as measured by the instrument for
            the specified channel.

            :units: :math:`\\text{A}` (amps)
            :rtype: `~quantities.Quantity`
            """
            return pq.Quantity(float(self._hp.query(
                'IOUT? {}'.format(self._idx)).strip()), pq.amp)

        @property
        def overvoltage(self):
            """
            Gets/sets the overvoltage protection setting for the specified channel.

            Note there is no bounds checking on the value specified.

            :units: As specified, or assumed to be :math:`\\text{V}` otherwise.
            :type: `float` or `~quantities.Quantity`
            """
            return pq.Quantity(float(self._hp.query(
                'OVSET? {}'.format(self._idx)).strip()), pq.volt)

        @overvoltage.setter
        def overvoltage(self, newval):
            self._hp.sendcmd('OVSET {},{}'.format(
                self._idx,
                assume_units(newval, pq.volt).rescale(pq.volt).magnitude
            ))

        @property
        def overcurrent(self):
            """
            Gets/sets the overcurrent protection setting for the specified channel.

            This is a toggle setting. It is either on or off.

            :type: `bool`
            """
            return (True if self._hp.query('OVP? {}'.format(self._idx)).strip()
                    is '1' else False)

        @overcurrent.setter
        def overcurrent(self, newval):
            if newval is True:
                newval = 1
            else:
                newval = 0
            self._hp.sendcmd('OVP {},{}'.format(self._idx, newval))

        @property
        def output(self):
            """
            Gets/sets the outputting status of the specified channel.

            This is a toggle setting. True will turn on the channel output
            while False will turn it off.

            :type: `bool`
            """
            return (True if self._hp.query('OUT? {}'.format(self._idx)).strip()
                    is '1' else False)

        @output.setter
        def output(self, newval):
            if newval is True:
                newval = 1
            else:
                newval = 0
            self._hp.sendcmd('OUT {},{}'.format(self._idx, newval))

        # METHODS ##

        def reset(self):
            """
            Reset overvoltage and overcurrent errors to resume operation.
            """
            self._hp.sendcmd('OVRST {}'.format(self._idx))
            self._hp.sendcmd('OCRST {}'.format(self._idx))

    # ENUMS #

    class Mode(Enum):
        # TODO: lookup correct values here...can this model even do this?
        voltage = 0
        current = 0

    # PROPERTIES ##

    @property
    def channel(self):
        """
        Gets a specific channel object. The desired channel is specified like
        one would access a list.

        :rtype: `HP6624a.Channel`

        .. seealso::
            `HP6624a` for example using this property.
        """
        return ProxyList(self, HP6624a.Channel, range(self.channel_count))

    @property
    def voltage(self):
        """
        Gets/sets the voltage for all four channels.

        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of units Volts.
        :type: `list` of `~quantities.Quantity` with units Volt
        """
        values = []
        for i in range(self.channel_count):
            values.append(self.channel[i].voltage)
        return tuple(values)

    @voltage.setter
    def voltage(self, newval):
        if isinstance(newval, (list, tuple)):
            if len(newval) is not self.channel_count:
                raise ValueError('When specifying the voltage for all channels '
                                 'as a list or tuple, it must be of '
                                 'length {}.'.format(self.channel_count))
            for i in range(self.channel_count):
                self.channel[i].voltage = newval[i]
        else:
            for i in range(self.channel_count):
                self.channel[i].voltage = newval

    @property
    def current(self):
        """
        Gets/sets the current for all four channels.

        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of units Amps.
        :type: `list` of `~quantities.Quantity` with units Amp
        """
        values = []
        for i in range(self.channel_count):
            values.append(self.channel[i].current)
        return tuple(values)

    @current.setter
    def current(self, newval):
        if isinstance(newval, list) or isinstance(newval, tuple):
            if len(newval) is not self.channel_count:
                raise ValueError('When specifying the current for all channels '
                                 'as a list or tuple, it must be of '
                                 'length {}.'.format(self.channel_count))
            for i in range(self.channel_count):
                self.channel[i].current = newval[i]
        else:
            for i in range(self.channel_count):
                self.channel[i].current = newval

    @property
    def voltage_sense(self):
        """
        Gets the actual voltage as measured by the sense wires for all channels.

        :units: :math:`\\text{V}` (volts)
        :rtype: `tuple` of `~quantities.Quantity`
        """
        values = []
        for i in range(self.channel_count):
            values.append(self.channel[i].voltage_sense)
        return tuple(values)

    @property
    def current_sense(self):
        """
        Gets the actual current as measured by the instrument for all channels.

        :units: :math:`\\text{A}` (amps)
        :rtype: `tuple` of `~quantities.Quantity`
        """
        values = []
        for i in range(self.channel_count):
            values.append(self.channel[i].current_sense)
        return tuple(values)

    @property
    def channel_count(self):
        """
        Gets/sets the number of output channels available for the connected
        power supply.

        :type: `int`
        """
        return self._channel_count

    @channel_count.setter
    def channel_count(self, newval):
        if not isinstance(newval, int):
            raise TypeError('Channel count must be specified as an integer.')
        if newval < 1:
            raise ValueError('Channel count must be >=1')
        self._channel_count = newval

    # METHODS ##

    def clear(self):
        """
        Taken from the manual:

        Return the power supply to its power-on state and all parameters are
        returned to their initial power-on values except the following:

        #) The store/recall registers are not cleared.
        #) The power supply remains addressed to listen.
        #) The PON bit in the serial poll register is cleared.
        """
        self.sendcmd('CLR')
