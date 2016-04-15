#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides support for the Yokogawa 7651 power supply.
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division

from enum import IntEnum

import quantities as pq

from instruments.abstract_instruments import (
    PowerSupply,
    PowerSupplyChannel,
)
from instruments.abstract_instruments import Instrument
from instruments.util_fns import assume_units, ProxyList

# CLASSES #####################################################################


class Yokogawa7651(PowerSupply, Instrument):

    """
    The Yokogawa 7651 is a single channel DC power supply.

    Example usage:

    >>> import instruments as ik
    >>> import quantities as pq
    >>> inst = ik.yokogawa.Yokogawa7651.open_gpibusb("/dev/ttyUSB0", 1)
    >>> inst.voltage = 10 * pq.V
    """

    def __init__(self, filelike):
        super(Yokogawa7651, self).__init__(filelike)

    # INNER CLASSES #

    class Channel(PowerSupplyChannel):

        """
        Class representing the only channel on the Yokogawa 7651.

        This class inherits from `PowerSupplyChannel`.

        .. warning:: This class should NOT be manually created by the user. It
            is designed to be initialized by the `Yokogawa7651` class.
        """

        def __init__(self, parent, name):
            self._parent = parent
            self._name = name

        # PROPERTIES #

        @property
        def mode(self):
            """
            Sets the output mode for the power supply channel.
            This is either constant voltage or constant current.

            Querying the mode is not supported by this instrument.

            :type: `Yokogawa7651.Mode`
            """
            raise NotImplementedError('This instrument does not support '
                                      'querying the operation mode.')

        @mode.setter
        def mode(self, newval):
            if not isinstance(newval, Yokogawa7651.Mode):
                raise TypeError("Mode setting must be a `Yokogawa7651.Mode` "
                                "value, got {} instead.".format(type(newval)))
            self._parent.sendcmd('F{};'.format(newval.value))
            self._parent.trigger()

        @property
        def voltage(self):
            """
            Sets the voltage of the specified channel. This device has a voltage
            range of 0V to +30V.

            Querying the voltage is not supported by this instrument.

            :units: As specified (if a `~quantities.quantity.Quantity`) or
                assumed to be of units Volts.
            :type: `~quantities.quantity.Quantity` with units Volt
            """
            raise NotImplementedError('This instrument does not support '
                                      'querying the output voltage setting.')

        @voltage.setter
        def voltage(self, newval):
            newval = assume_units(newval, pq.volt).rescale(pq.volt).magnitude
            self.mode = self._parent.Mode.voltage
            self._parent.sendcmd('SA{};'.format(newval))
            self._parent.trigger()

        @property
        def current(self):
            """
            Sets the current of the specified channel. This device has an max
            setting of 100mA.

            Querying the current is not supported by this instrument.

            :units: As specified (if a `~quantities.quantity.Quantity`) or
                assumed to be of units Amps.
            :type: `~quantities.quantity.Quantity` with units Amp
            """
            raise NotImplementedError('This instrument does not support '
                                      'querying the output current setting.')

        @current.setter
        def current(self, newval):
            newval = assume_units(newval, pq.amp).rescale(pq.amp).magnitude
            self.mode = self._parent.Mode.current
            self._parent.sendcmd('SA{};'.format(newval))
            self._parent.trigger()

        @property
        def output(self):
            """
            Sets the output status of the specified channel. This either enables
            or disables the output.

            Querying the output status is not supported by this instrument.

            :type: `bool`
            """
            raise NotImplementedError('This instrument does not support '
                                      'querying the output status.')

        @output.setter
        def output(self, newval):
            if newval is True:
                self._parent.sendcmd('O1;')
                self._parent.trigger()
            else:
                self._parent.sendcmd('O0;')
                self._parent.trigger()

    # ENUMS #

    class Mode(IntEnum):
        """
        Enum containing valid output modes for the Yokogawa 7651
        """
        voltage = 1
        current = 5

    # PROPERTIES #

    @property
    def channel(self):
        """
        Gets the specific power supply channel object. Since the Yokogawa7651
        is only equiped with a single channel, a list with a single element
        will be returned.

        This (single) channel is accessed as a list in the following manner::

        >>> import instruments as ik
        >>> yoko = ik.yokogawa.Yokogawa7651.open_gpibusb('/dev/ttyUSB0', 10)
        >>> yoko.channel[0].voltage = 1 # Sets output voltage to 1V

        :rtype: `~Yokogawa7651.Channel`
        """
        return ProxyList(self, Yokogawa7651.Channel, [0])

    @property
    def voltage(self):
        """
        Sets the voltage. This device has a voltage range of 0V to +30V.

        Querying the voltage is not supported by this instrument.

        :units: As specified (if a `~quantities.quantity.Quantity`) or assumed
            to be of units Volts.
        :type: `~quantities.quantity.Quantity` with units Volt
        """
        raise NotImplementedError('This instrument does not support querying '
                                  'the output voltage setting.')

    @voltage.setter
    def voltage(self, newval):
        self.channel[0].voltage = newval

    @property
    def current(self):
        """
        Sets the current. This device has an max setting of 100mA.

        Querying the current is not supported by this instrument.

        :units: As specified (if a `~quantities.quantity.Quantity`) or assumed
            to be of units Amps.
        :type: `~quantities.quantity.Quantity` with units Amp
        """
        raise NotImplementedError('This instrument does not support querying '
                                  'the output current setting.')

    @current.setter
    def current(self, newval):
        self.channel[0].current = newval

    # METHODS #

    def trigger(self):
        """
        Triggering function for the Yokogawa 7651.

        After changing any parameters of the instrument (for example, output
        voltage), the device needs to be triggered before it will update.
        """
        self.sendcmd('E;')
