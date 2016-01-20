#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# sc10.py: Class for the thorlabs sc10 Shutter Controller
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
# SC10 Class contributed by Catherine Holloway
#
# IMPORTS #####################################################################

import quantities as pq
from flufl.enum import IntEnum

from instruments.abstract_instruments import Instrument
from instruments.util_fns import assume_units
from instruments.thorlabs import check_cmd


def trigger_check(newval):
    """
    Validate the trigger
    :param newval: trigger
    :type newval: int
    :return:
    """
    if newval != 0 and newval != 1:
        raise ValueError("Not a valid value for trigger mode")


def check_time(newval):
    """
    Validate the shutter time
    :param newval: the new time
    :type newval: int
    :return:
    """
    if newval < 0:
        raise ValueError("Duration cannot be negative")
    if newval > 999999:
        raise ValueError("Duration is too long")


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
        self.echo = True

    def _ack_expected(self, msg=""):
        return msg

    # ENUMS ##

    class Mode(IntEnum):
        manual = 1
        auto = 2
        single = 3
        repeat = 4
        external = 5

    # PROPERTIES ##

    def name(self):
        """
        Gets the name and version number of the device.
        """
        response = self.query("id?")
        return response

    @property
    def enable(self):
        """
        Gets/sets the shutter enable status, 0 for disabled, 1 if enabled

        :type: `int`
        """
        response = self.query("ens?")
        return int(response)

    @enable.setter
    def enable(self, newval):
        if newval == 0 or newval == 1:
            self.sendcmd("ens={}".format(newval))
        else:
            raise ValueError("Invalid value for enable, must be 0 or 1")

    @property
    def repeat(self):
        """
        Gets/sets the repeat count for repeat mode. Valid range is [1,99]
        inclusive.

        :type: `int`
        """
        response = self.query("rep?")
        return int(response)

    @repeat.setter
    def repeat(self, newval):
        if 0 < newval < 100:
            self.sendcmd("rep={}".format(newval))
            self.read()
        else:
            raise ValueError("Invalid value for repeat count, must be "
                             "between 1 and 99")

    @property
    def mode(self):
        """
        Gets/sets the output mode of the SC10.

        :type: `SC10.Mode`
        """
        response = self.query("mode?")
        return SC10.Mode[int(response)]

    @mode.setter
    def mode(self, newval):
        if not hasattr(newval, 'enum'):
            raise TypeError("Mode setting must be a `SC10.Mode` value, "
                            "got {} instead.".format(type(newval)))
        if newval.enum is not SC10.Mode:
            raise TypeError("Mode setting must be a `SC10.Mode` value, "
                            "got {} instead.".format(type(newval)))

        self.sendcmd("mode={}".format(newval.value))

    @property
    def trigger(self):
        """
        Gets/sets the trigger source.

        0 for internal trigger, 1 for external trigger

        :type: `int`
        """
        response = self.query("trig?")
        return int(response)

    @trigger.setter
    def trigger(self, newval):
        trigger_check(newval)
        self.sendcmd("trig={}".format(newval))

    @property
    def out_trigger(self):
        """
        Gets/sets the out trigger source.

        0 trigger out follows shutter output, 1 trigger out follows
        controller output

        :type: `int`
        """
        response = self.query("xto?")
        return int(response)

    @out_trigger.setter
    def out_trigger(self, newval):
        trigger_check(newval)
        self.sendcmd("xto={}".format(newval))

    # I'm not sure how to handle checking for the number of digits yet.
    @property
    def open_time(self):
        """
        Gets/sets the amount of time that the shutter is open, in ms

        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of units milliseconds.
        :type: `~quantities.Quantity`
        """
        response = self.query("open?")
        return float(response) * pq.ms

    @open_time.setter
    def open_time(self, newval):
        newval = int(assume_units(newval, pq.ms).rescale(pq.ms).magnitude)
        check_time(newval)
        self.sendcmd("open={}".format(newval))

    @property
    def shut_time(self):
        """
        Gets/sets the amount of time that the shutter is closed, in ms

        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of units milliseconds.
        :rtype: `~quantities.Quantity`
        """
        response = self.query("shut?")
        return float(response) * pq.ms

    @shut_time.setter
    def shut_time(self, newval):
        newval = int(assume_units(newval, pq.ms).rescale(pq.ms).magnitude)
        check_time(newval)
        self.sendcmd("shut={}".format(newval))

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

    @property
    def closed(self):
        """
        Gets the shutter closed status.

        `True` represents the shutter is closed, and `False` for the shutter is
        open.

        :rtype: `bool`
        """
        response = self.query("closed?")
        return True if int(response) is 1 else False

    @property
    def interlock(self):
        """
        Gets the interlock tripped status.

        Returns `True` if the interlock is tripped, and `False` otherwise.

        :rtype: `bool`
        """
        response = self.query("interlock?")
        return True if int(response) is 1 else False

    # Methods ##

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
