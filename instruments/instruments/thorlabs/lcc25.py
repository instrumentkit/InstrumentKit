#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# lcc25.py: class for the Thorlabs LCC25 Liquid Crystal Controller
#
# © 2014-2016 Steven Casagrande (scasagrande@galvant.ca).
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
# LCC25 Class contributed by Catherine Holloway
#
# IMPORTS #####################################################################

import quantities as pq
from flufl.enum import IntEnum

from instruments.thorlabs._utils import check_cmd

from instruments.abstract_instruments import Instrument
from instruments.util_fns import enum_property, bool_property, unitful_property

# CLASSES #####################################################################


class LCC25(Instrument):

    """
    The LCC25 is a controller for the thorlabs liquid crystal modules.
    it can set two voltages and then oscillate between them at a specific
    repetition rate.

    The user manual can be found here:
    http://www.thorlabs.com/thorcat/18800/LCC25-Manual.pdf
    """

    def __init__(self, filelike):
        super(LCC25, self).__init__(filelike)
        self.terminator = "\r"
        self.prompt = ">"

    def _ack_expected(self, msg=""):
        return msg

    # ENUMS #

    class Mode(IntEnum):
        normal = 0
        voltage1 = 1
        voltage2 = 2

    # PROPERTIES #

    @property
    def name(self):
        """
        Gets the name and version number of the device

        :rtype: `str`
        """
        return self.query("*idn?")

    frequency = unitful_property(
        "freq",
        pq.Hz,
        format_code="{:.1f}",
        set_fmt="{}={}",
        valid_range=(5, 150),
        doc="""
        Gets/sets the frequency at which the LCC oscillates between the
        two voltages.

        :units: As specified (if a `~quantities.quantity.Quantity`) or assumed
            to be of units Hertz.
        :rtype: `~quantities.quantity.Quantity`
        """
    )

    mode = enum_property(
        "mode",
        Mode,
        input_decoration=int,
        set_fmt="{}={}",
        doc="""
        Gets/sets the output mode of the LCC25

        :rtype: `LCC25.Mode`
        """
     )

    enable = bool_property(
        "enable",
        "1",
        "0",
        set_fmt="{}={}",
        doc="""
        Gets/sets the output enable status.

        If output enable is on (`True`), there is a voltage on the output.

        :rtype: `bool`
        """
    )

    extern = bool_property(
        "extern",
        "1",
        "0",
        set_fmt="{}={}",
        doc="""
        Gets/sets the use of the external TTL modulation.

        Value is `True` for external TTL modulation and `False` for internal
        modulation.

        :rtype: `bool`
        """
    )

    remote = bool_property(
        "remote",
        "1",
        "0",
        set_fmt="{}={}",
        doc="""
        Gets/sets front panel lockout status for remote instrument operation.

        Value is `False` for normal operation and `True` to lock out the front
        panel buttons.

        :rtype: `bool`
        """
    )

    voltage1 = unitful_property(
        "volt1",
        pq.V,
        format_code="{:.1f}",
        set_fmt="{}={}",
        valid_range=(0, 25),
        doc="""
        Gets/sets the voltage value for output 1.

        :units: As specified (if a `~quantities.quantity.Quantity`) or
            assumed to be of units Volts.
        :rtype: `~quantities.quantity.Quantity`
        """
    )

    voltage2 = unitful_property(
        "volt2",
        pq.V,
        format_code="{:.1f}",
        set_fmt="{}={}",
        valid_range=(0, 25),
        doc="""
        Gets/sets the voltage value for output 2.

        :units: As specified (if a `~quantities.quantity.Quantity`) or
            assumed to be of units Volts.
        :rtype: `~quantities.quantity.Quantity`
        """
    )

    min_voltage = unitful_property(
        "min",
        pq.V,
        format_code="{:.1f}",
        set_fmt="{}={}",
        valid_range=(0, 25),
        doc="""
        Gets/sets the minimum voltage value for the test mode.

        :units: As specified (if a `~quantities.quantity.Quantity`) or assumed
            to be of units Volts.
        :rtype: `~quantities.quantity.Quantity`
        """
    )

    max_voltage = unitful_property(
        "max",
        pq.V,
        format_code="{:.1f}",
        set_fmt="{}={}",
        valid_range=(0, 25),
        doc="""
        Gets/sets the maximum voltage value for the test mode. If the maximum
        voltage is less than the minimum voltage, nothing happens.

        :units: As specified (if a `~quantities.quantity.Quantity`) or assumed
            to be of units Volts.
        :rtype: `~quantities.quantity.Quantity`
        """
    )

    dwell = unitful_property(
        "dwell",
        units=pq.ms,
        format_code="{:n}",
        set_fmt="{}={}",
        valid_range=(0, None),
        doc="""
        Gets/sets the dwell time for voltages for the test mode.

        :units: As specified (if a `~quantities.quantity.Quantity`) or assumed to be
            of units milliseconds.
        :rtype: `~quantities.quantity.Quantity`
        """
    )

    increment = unitful_property(
        "increment",
        units=pq.V,
        format_code="{:.1f}",
        set_fmt="{}={}",
        valid_range=(0, None),
        doc="""
        Gets/sets the voltage increment for voltages for the test mode.

        :units: As specified (if a `~quantities.quantity.Quantity`) or assumed
            to be of units Volts.
        :rtype: `~quantities.quantity.Quantity`
        """
    )

    # METHODS #

    def default(self):
        """
        Restores instrument to factory settings.

        Returns 1 if successful, 0 otherwise

        :rtype: `int`
        """
        response = self.query("default")
        return check_cmd(response)

    def save(self):
        """
        Stores the parameters in static memory

        Returns 1 if successful, zero otherwise.

        :rtype: `int`
        """
        self.sendcmd("save")

    def set_settings(self, slot):
        """
        Saves the current settings to memory.

        :param slot: Memory slot to use, valid range `[1,4]`
        :type slot: `int`
        """
        if slot not in xrange(1, 5):
            raise ValueError("Cannot set memory out of `[1,4]` range")
        self.sendcmd("set={}".format(slot))

    def get_settings(self, slot):
        """
        Gets the current settings to memory.

        :param slot: Memory slot to use, valid range `[1,4]`
        :type slot: `int`
        """
        if slot not in xrange(1, 5):
            raise ValueError("Cannot set memory out of `[1,4]` range")
        self.sendcmd("get={}".format(slot))

    def test_mode(self):
        """
        Puts the LCC in test mode - meaning it will increment the output
        voltage from the minimum value to the maximum value, in increments,
        waiting for the dwell time
        """
        self.sendcmd("test")
