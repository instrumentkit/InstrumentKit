#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Provides the support for the Thorlabs SC10 optical beam shutter controller.

Class originally contributed by Catherine Holloway.
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division
from builtins import range

from enum import IntEnum
import quantities as pq

from instruments.abstract_instruments import Instrument
from instruments.util_fns import (
    bool_property, enum_property, int_property, unitful_property
)
from instruments.thorlabs.thorlabs_utils import check_cmd

# CLASSES #####################################################################


class SC10(Instrument):

    """
    The SC10 is a shutter controller, to be used with the Thorlabs SH05 and SH1.
    The user manual can be found here:
    http://www.thorlabs.com/thorcat/8600/SC10-Manual.pdf
    """

    def __init__(self, filelike):
        super(SC10, self).__init__(filelike)
        self.terminator = '\r'
        self.prompt = '>'

    def _ack_expected(self, msg=""):
        return msg

    # ENUMS #

    class Mode(IntEnum):

        """
        Enum containing valid output modes of the SC10
        """
        manual = 1
        auto = 2
        single = 3
        repeat = 4
        external = 5

    # PROPERTIES #

    @property
    def name(self):
        """
        Gets the name and version number of the device.

        :return: Name and verison number of the device
        :rtype: `str`
        """
        return self.query("id?")

    enable = bool_property(
        "ens",
        "1",
        "0",
        set_fmt="{}={}",
        doc="""
        Gets/sets the shutter enable status, False for disabled, True if
        enabled

        If output enable is on (`True`), there is a voltage on the output.

        :rtype: `bool`
        """
    )

    repeat = int_property(
        "rep",
        valid_set=range(1, 100),
        set_fmt="{}={}",
        doc="""
        Gets/sets the repeat count for repeat mode. Valid range is [1,99]
        inclusive.

        :type: `int`
        """
    )

    mode = enum_property(
        "mode",
        Mode,
        input_decoration=int,
        set_fmt="{}={}",
        doc="""
        Gets/sets the output mode of the SC10

        :rtype: `SC10.Mode`
        """
    )

    trigger = int_property(
        "trig",
        valid_set=range(0, 2),
        set_fmt="{}={}",
        doc="""
        Gets/sets the trigger source.

        0 for internal trigger, 1 for external trigger

        :type: `int`
        """
    )

    out_trigger = int_property(
        "xto",
        valid_set=range(0, 2),
        set_fmt="{}={}",
        doc="""
        Gets/sets the out trigger source.

        0 trigger out follows shutter output, 1 trigger out follows
        controller output

        :type: `int`
        """
    )

    open_time = unitful_property(
        "open",
        pq.ms,
        format_code="{:.0f}",
        set_fmt="{}={}",
        valid_range=(0, 999999),
        doc="""
        Gets/sets the amount of time that the shutter is open, in ms

        :units: As specified (if a `~quantities.quantity.Quantity`) or assumed
            to be of units milliseconds.
        :type: `~quantities.quantity.Quantity`
        """
    )

    shut_time = unitful_property(
        "shut",
        pq.ms,
        format_code="{:.0f}",
        set_fmt="{}={}",
        valid_range=(0, 999999),
        doc="""
        Gets/sets the amount of time that the shutter is closed, in ms

        :units: As specified (if a `~quantities.quantity.Quantity`) or assumed
            to be of units milliseconds.
        :type: `~quantities.quantity.Quantity`
        """
    )

    @property
    def baud_rate(self):
        """
        Gets/sets the instrument baud rate.

        Valid baud rates are 9600 and 115200.

        :type: `int`
        """
        response = self.query("baud?")
        return 115200 if int(response) else 9600

    @baud_rate.setter
    def baud_rate(self, newval):
        if newval != 9600 and newval != 115200:
            raise ValueError("Invalid baud rate mode")
        else:
            self.sendcmd("baud={}".format(0 if newval == 9600 else 1))

    closed = bool_property(
        "closed",
        "1",
        "0",
        readonly=True,
        doc="""
        Gets the shutter closed status.

        `True` represents the shutter is closed, and `False` for the shutter is
        open.

        :rtype: `bool`
        """
    )

    interlock = bool_property(
        "interlock",
        "1",
        "0",
        readonly=True,
        doc="""
        Gets the interlock tripped status.

        Returns `True` if the interlock is tripped, and `False` otherwise.

        :rtype: `bool`
        """
    )

    # Methods #

    def default(self):
        """
        Restores instrument to factory settings.

        Returns 1 if successful, zero otherwise.

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
        response = self.query("savp")
        return check_cmd(response)

    def save_mode(self):
        """
        Stores output trigger mode and baud rate settings in memory.

        Returns 1 if successful, zero otherwise.

        :rtype: `int`
        """
        response = self.query("save")
        return check_cmd(response)

    def restore(self):
        """
        Loads the settings from memory.

        Returns 1 if successful, zero otherwise.

        :rtype: `int`
        """
        response = self.query("resp")
        return check_cmd(response)
