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

from __future__ import absolute_import
from __future__ import division

from enum import Enum

import quantities as pq

from instruments.generic_scpi import SCPIInstrument
from instruments.util_fns import bool_property, enum_property

# CLASSES #####################################################################


class Keithley6485(SCPIInstrument):

    """
    The `Keithley 6485` is an electrometer capable of doing sensitive current,
    charge, voltage and resistance measurements.

    WARNING: Must set the terminator to `LF` on the define for this to work.

    Example usage:

    >>> import instruments as ik
    >>> import quantities as pq
    >>> dmm = ik.keithley.Keithley6485.open_serial('/dev/ttyUSB0', baud=9600)
    >>> dmm.measure()
    array(0.000123) * pq.amp
    """

    def __init__(self, filelike):
        """
        Resets device to be read.
        """
        super(Keithley6485, self).__init__(filelike)

    # ENUMS ##

    class TriggerMode(Enum):
        """
        Enum containing valid trigger modes for the Keithley 6485
        """
        immediate = 'IMM'
        tlink = 'TLINK'

    class ArmSource(Enum):
        """
        Enum containing valid trigger arming sources for the Keithley 6485
        """
        immediate = 'IMM'
        timer = 'TIM'
        bus = 'BUS'
        tlink = 'TLIN'
        stest = 'STES'
        pstest = 'PST'
        nstest = 'NST'
        manual = 'MAN'

    # PROPERTIES ##

    trigger_mode = enum_property(
        'TRIGGER:SOURCE',
        TriggerMode,
        doc="""
        Gets/sets the trigger mode of the Keithley 6485.
        """
    )

    arm_source = enum_property(
        'ARM:SOURCE',
        ArmSource,
        doc="""
        Gets/sets the arm source of the Keithley 6485.
        """
    )

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
        return pq.amp

    @property
    def auto_range(self):
        """
        Gets/sets the auto range setting

        :type: `bool`
        """
        # pylint: disable=no-member
        out = self.query('{CURR:RANGE:AUTO?')
        return out == '1'

    @auto_range.setter
    def auto_range(self, newval):
        # pylint: disable=no-member
        self.sendcmd('CUUR:RANGE:AUTO {}'.format('1' if newval else '0'))

    @property
    def input_range(self):
        """
        Gets/sets the upper limit of the current range.

        :type: `~quantities.Quantity`
        """
        # pylint: disable=no-member
        out = self.query('CUUR:RANGE:UPPER?')
        return float(out) * pq.amp

    @input_range.setter
    def input_range(self, newval):
        # pylint: disable=no-member
        val = newval.rescale(pq.amp).item()
        if val not in self._valid_range().value:
            raise ValueError(
                'Unexpected range limit for currently selected mode.')
        self.sendcmd('{}:RANGE:UPPER {:e}'.format(mode.value, val))

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
        timestamp = float(vals[1]) * pq.second
        trigger_count = int(float(vals[2]))
        return reading, timestamp, trigger_count
