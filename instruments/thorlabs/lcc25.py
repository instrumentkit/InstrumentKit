#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Provides the support for the Thorlabs LCC25 liquid crystal controller.

Class originally contributed by Catherine Holloway.
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division

from builtins import range
from enum import IntEnum

import quantities as pq

from instruments.thorlabs.thorlabs_utils import check_cmd

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

        """
        Enum containing valid output modes of the LCC25
        """
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

        :units: As specified (if a `~quantities.quantity.Quantity`) or assumed
            to be of units milliseconds.
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
        response = self.query("save")
        return check_cmd(response)

    def set_settings(self, slot):
        """
        Saves the current settings to memory.

        Returns 1 if successful, zero otherwise.

        :param slot: Memory slot to use, valid range `[1,4]`
        :type slot: `int`
        :rtype: `int`
        """
        if slot not in range(1, 5):
            raise ValueError("Cannot set memory out of `[1,4]` range")
        response = self.query("set={}".format(slot))
        return check_cmd(response)

    def get_settings(self, slot):
        """
        Gets the current settings to memory.

        Returns 1 if successful, zero otherwise.

        :param slot: Memory slot to use, valid range `[1,4]`
        :type slot: `int`
        :rtype: `int`
        """
        if slot not in range(1, 5):
            raise ValueError("Cannot set memory out of `[1,4]` range")
        response = self.query("get={}".format(slot))
        return check_cmd(response)

    def test_mode(self):
        """
        Puts the LCC in test mode - meaning it will increment the output
        voltage from the minimum value to the maximum value, in increments,
        waiting for the dwell time

        Returns 1 if successful, zero otherwise.

        :rtype: `int`
        """
        response = self.query("test")
        return check_cmd(response)
