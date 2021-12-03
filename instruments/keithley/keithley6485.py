#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# keithley6485.py: Driver for the Keithley 6485 picoammeter
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
Driver for the Keithley 6485 picoammeter.

Originally contributed and copyright held by Francois Drielsma
(francois.drielsma@gmail.com).

An unrestricted license has been provided to the maintainers of the Instrument
Kit project.
"""

# IMPORTS #####################################################################

from enum import Enum

from instruments.generic_scpi import SCPIInstrument
from instruments.units import ureg as u
from instruments.util_fns import bool_property, enum_property

# CLASSES #####################################################################


class Keithley6485(SCPIInstrument):

    """
    The `Keithley 6485` is an electrometer capable of doing sensitive current,
    charge, voltage and resistance measurements.

    WARNING: Must set the terminator to `LF` on the define for this to work.

    Example usage:

    >>> import instruments as ik
    >>> import instruments.units as u
    >>> dmm = ik.keithley.Keithley6485.open_serial('/dev/ttyUSB0', baud=9600)
    >>> dmm.measure()
    <Quantity(0.000123, 'ampere')>
    """

    def __init__(self, filelike):
        """
        Resets device to be read, disables zero check.
        """
        super(Keithley6485, self).__init__(filelike)
        self.reset()
        self.zero_check = False

    # PROPERTIES ##

    zero_check = bool_property(
        'SYST:ZCH',
        inst_true='ON',
        inst_false='OFF',
        doc="""
        Gets/sets the zero checking status of the Keithley 6485.
        """
    )

    zero_correct = bool_property(
        'SYST:ZCOR',
        inst_true='ON',
        inst_false='OFF',
        doc="""
        Gets/sets the zero correcting status of the Keithley 6485.
        """
    )

    @property
    def unit(self):
        return u.amp

    @property
    def auto_range(self):
        """
        Gets/sets the auto range setting

        :type: `bool`
        """
        # pylint: disable=no-member
        out = self.query('RANG:AUTO?')
        return out == '1'

    @auto_range.setter
    def auto_range(self, newval):
        # pylint: disable=no-member
        self.sendcmd('RANG:AUTO {}'.format('1' if newval else '0'))

    @property
    def input_range(self):
        """
        Gets/sets the upper limit of the current range.

        :type: `~pint.Quantity`
        """
        # pylint: disable=no-member
        out = self.query('RANG?')
        return float(out) * u.amp

    @input_range.setter
    def input_range(self, newval):
        # pylint: disable=no-member
        val = newval.to(u.amp).magnitude
        if val not in self._valid_range():
            raise ValueError(
                'Unexpected range limit for currently selected mode.')
        self.sendcmd('RANG {:e}'.format(val))

    # METHODS ##

    def fetch(self):
        """
        Request the latest post-processed readings using the current mode.
        (So does not issue a trigger)
        Returns a tuple of the form (reading, timestamp, trigger_count)
        """
        return self._parse_measurement(self.query('FETC?'))

    def read_measurements(self):
        """
        Trigger and acquire readings using the current mode.
        Returns a tuple of the form (reading, timestamp, trigger_count)
        """
        return self._parse_measurement(self.query('READ?'))

    def measure(self, mode=None):
        """
        Trigger and acquire readings.
        Returns the measurement reading only.
        """
        return self.read_measurements()[0]

    # PRIVATE METHODS ##

    def _valid_range(self):
        return (2e-9, 20e-9, 200e-9, 2e-6, 20e-6, 200e-6, 2e-3, 20e-3)

    def _parse_measurement(self, ascii):
        # Split the string in three comma-separated parts (value, time, number of triggers)
        vals = ascii.split(',')
        reading = float(vals[0][:-1]) * self.unit
        timestamp = float(vals[1]) * u.second
        trigger_count = int(float(vals[2]))
        return reading, timestamp, trigger_count
