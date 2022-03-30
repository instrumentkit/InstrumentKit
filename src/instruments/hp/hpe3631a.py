#!/usr/bin/env python
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

import time

from instruments.units import ureg as u

from instruments.abstract_instruments import PowerSupply
from instruments.generic_scpi import SCPIInstrument
from instruments.util_fns import (
    int_property,
    unitful_property,
    bounded_unitful_property,
    bool_property,
    split_unit_str,
    assume_units,
)

# CLASSES #####################################################################


class HPe3631a(PowerSupply, PowerSupply.Channel, SCPIInstrument):

    """
    The HPe3631a is a three channels voltage/current supply.
    - Channel 1 is a positive +6V/5A channel (P6V)
    - Channel 2 is a positive +25V/1A channel (P25V)
    - Channel 3 is a negative -25V/1A channel (N25V)

    This module is designed for the power supply to be set to
    a specific channel and remain set afterwards as this device
    does not offer commands to set or read multiple channels
    without calling the channel set command each time (0.5s). It is
    possible to call a specific channel through psu.channel[idx],
    which will automatically reset the channel id, when necessary.

    This module is likely to work as is for the Agilent E3631 and
    Keysight E3631 which seem to be rebranded but identical devices.

    Example usage:

    >>> import instruments as ik
    >>> psu = ik.hp.HPe3631a.open_gpibusb("/dev/ttyUSB0", 10)
    >>> psu.channelid = 2           # Sets channel to P25V
    >>> psu.voltage = 12.5          # Sets voltage to 12.5V
    >>> psu.voltage                 # Reads back set voltage
    array(12.5) * V
    >>> psu.voltage_sense           # Reads back sensed voltage
    array(12.501) * V
    """

    def __init__(self, filelike):
        super().__init__(filelike)
        self.sendcmd("SYST:REM")  # Puts the device in remote operation
        time.sleep(0.1)

    # INNER CLASSES #

    class Channel:
        """
        Class representing a power output channel on the HPe3631a.

        .. warning:: This class should NOT be manually created by the user. It is
            designed to be initialized by the `HPe3631a` class.
        """

        def __init__(self, parent, valid_set):
            self._parent = parent
            self._valid_set = valid_set

        def __getitem__(self, idx):
            # Check that the channel is available. If it is, set the
            # channelid of the device and return the device object.
            if self._parent.channelid != idx:
                self._parent.channelid = idx
                time.sleep(0.5)
            return self._parent

        def __len__(self):
            return len(self._valid_set)

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
        return self.Channel(self, [1, 2, 3])

    @property
    def mode(self):
        """
        Gets/sets the mode for the specified channel.

        The constant-voltage/constant-current modes of the power supply
        are selected automatically depending on the load (resistance)
        connected to the power supply. If the load greater than the set
        V/I is connected, a voltage V is applied and the current flowing
        is lower than I. If the load is smaller than V/I, the set current
        I acts as a current limiter and the voltage is lower than V.
        """
        raise AttributeError("The `HPe3631a` sets its mode automatically")

    channelid = int_property(
        "INST:NSEL",
        valid_set=[1, 2, 3],
        doc="""
        Gets/Sets the active channel ID.

        :type: `HPe3631a.ChannelType`
        """,
    )

    @property
    def voltage(self):
        """
        Gets/sets the output voltage of the source.

        :units: As specified, or assumed to be :math:`\\text{V}` otherwise.
        :type: `float` or `~pint.Quantity`
        """
        raw = self.query("SOUR:VOLT?")
        return u.Quantity(*split_unit_str(raw, u.volt)).to(u.volt)

    @voltage.setter
    def voltage(self, newval):
        """
        Gets/sets the output voltage of the source.

        :units: As specified, or assumed to be :math:`\\text{V}` otherwise.
        :type: `float` or `~pint.Quantity`
        """
        min_value, max_value = self.voltage_range
        if newval < min_value:
            raise ValueError(
                "Voltage quantity is too low. Got {}, minimum "
                "value is {}".format(newval, min_value)
            )

        if newval > max_value:
            raise ValueError(
                "Voltage quantity is too high. Got {}, maximum "
                "value is {}".format(newval, max_value)
            )

        # Rescale to the correct unit before printing. This will also
        # catch bad units.
        strval = f"{assume_units(newval, u.volt).to(u.volt).magnitude:e}"
        self.sendcmd(f"SOUR:VOLT {strval}")

    @property
    def voltage_min(self):
        """
        Gets the minimum voltage for the current channel.

        :units: :math:`\\text{V}`.
        :type: `~pint.Quantity`
        """
        return self.voltage_range[0]

    @property
    def voltage_max(self):
        """
        Gets the maximum voltage for the current channel.

        :units: :math:`\\text{V}`.
        :type: `~pint.Quantity`
        """
        return self.voltage_range[1]

    @property
    def voltage_range(self):
        """
        Gets the voltage range for the current channel.

        The MAX function SCPI command is designed in such a way
        on this device that it always returns the largest absolute value.
        There is no need to query MIN, as it is always 0., but one has to
        order the values as MAX can be negative.

        :units: :math:`\\text{V}`.
        :type: array of `~pint.Quantity`
        """
        value = u.Quantity(*split_unit_str(self.query("SOUR:VOLT? MAX"), u.volt))
        if value < 0.0:
            return value, 0.0
        return 0.0, value

    current, current_min, current_max = bounded_unitful_property(
        "SOUR:CURR",
        u.amp,
        min_fmt_str="{}? MIN",
        max_fmt_str="{}? MAX",
        doc="""
        Gets/sets the output current of the source.

        :units: As specified, or assumed to be :math:`\\text{A}` otherwise.
        :type: `float` or `~pint.Quantity`
        """,
    )

    voltage_sense = unitful_property(
        "MEAS:VOLT",
        u.volt,
        readonly=True,
        doc="""
        Gets the actual output voltage as measured by the sense wires.

        :units: As specified, or assumed to be :math:`\\text{V}` otherwise.
        :type: `~pint.Quantity`
        """,
    )

    current_sense = unitful_property(
        "MEAS:CURR",
        u.amp,
        readonly=True,
        doc="""
        Gets the actual output current as measured by the sense wires.

        :units: As specified, or assumed to be :math:`\\text{A}` otherwise.
        :type: `~pint.Quantity`
        """,
    )

    output = bool_property(
        "OUTP",
        inst_true="1",
        inst_false="0",
        doc="""
        Gets/sets the outputting status of the specified channel.

        This is a toggle setting. ON will turn on the channel output
        while OFF will turn it off.

        :type: `bool`
        """,
    )
