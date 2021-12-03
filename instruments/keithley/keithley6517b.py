#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# keithley6517b.py: Driver for the Keithley 6517b Electrometer
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
Provides support for the Keithley 6517b electrometer.

Originally contributed and copyright held by Francois Drielsma
(francois.drielsma@gmail.com).

An unrestricted license has been provided to the maintainers of the Instrument
Kit project.
"""

# IMPORTS #####################################################################

from enum import Enum

from instruments.abstract_instruments import Electrometer
from instruments.generic_scpi import SCPIInstrument
from instruments.units import ureg as u
from instruments.util_fns import bool_property, enum_property

# CLASSES #####################################################################


class Keithley6517b(SCPIInstrument, Electrometer):

    """
    The `Keithley 6517b` is an electrometer capable of doing sensitive current,
    charge, voltage and resistance measurements.

    Example usage:

    >>> import instruments as ik
    >>> import instruments.units as u
    >>> dmm = ik.keithley.Keithley6517b.open_serial('/dev/ttyUSB0', baud=115200)
    >>> dmm.measure(dmm.Mode.current)
    <Quantity(0.123, 'ampere')>
    """

    def __init__(self, filelike):
        """
        Auto configs the instrument in to the current readout mode
        (sets the trigger and communication types rights)
        """
        super(Keithley6517b, self).__init__(filelike)
        self.auto_config(self.mode)

    # ENUMS ##

    class Mode(Enum):
        """
        Enum containing valid measurement modes for the Keithley 6517b
        """
        voltage_dc = 'VOLT:DC'
        current_dc = 'CURR:DC'
        resistance = 'RES'
        charge = 'CHAR'

    class TriggerMode(Enum):
        """
        Enum containing valid trigger modes for the Keithley 6517b
        """
        immediate = 'IMM'
        tlink = 'TLINK'

    class ArmSource(Enum):
        """
        Enum containing valid trigger arming sources for the Keithley 6517b
        """
        immediate = 'IMM'
        timer = 'TIM'
        bus = 'BUS'
        tlink = 'TLIN'
        stest = 'STES'
        pstest = 'PST'
        nstest = 'NST'
        manual = 'MAN'

    class ValidRange(Enum):
        """
        Enum containing valid measurement ranges for the Keithley 6517b
        """
        voltage_dc = (2, 20, 200)
        current_dc = (20e-12, 200e-12, 2e-9, 20e-9,
                      200e-9, 2e-6, 20e-6, 200e-6, 2e-3, 20e-3)
        resistance = (2e6, 20e6, 200e6, 2e9, 20e9, 200e9, 2e12, 20e12, 200e12)
        charge = (2e-9, 20e-9, 200e-9, 2e-6)

    # PROPERTIES ##

    mode = enum_property(
        'FUNCTION',
        Mode,
        input_decoration=lambda val: val[1:-1],
        # output_decoration=lambda val: '"{}"'.format(val),
        set_fmt='{} "{}"',
        doc="""
        Gets/sets the measurement mode of the Keithley 6517b.
        """
    )

    trigger_mode = enum_property(
        'TRIGGER:SOURCE',
        TriggerMode,
        doc="""
        Gets/sets the trigger mode of the Keithley 6517b.
        """
    )

    arm_source = enum_property(
        'ARM:SOURCE',
        ArmSource,
        doc="""
        Gets/sets the arm source of the Keithley 6517b.
        """
    )

    zero_check = bool_property(
        'SYST:ZCH',
        inst_true='ON',
        inst_false='OFF',
        doc="""
        Gets/sets the zero checking status of the Keithley 6517b.
        """
    )

    zero_correct = bool_property(
        'SYST:ZCOR',
        inst_true='ON',
        inst_false='OFF',
        doc="""
        Gets/sets the zero correcting status of the Keithley 6517b.
        """
    )

    @property
    def unit(self):
        return UNITS[self.mode]

    @property
    def auto_range(self):
        """
        Gets/sets the auto range setting

        :type: `bool`
        """
        # pylint: disable=no-member
        out = self.query('{}:RANGE:AUTO?'.format(self.mode.value))
        return out == '1'

    @auto_range.setter
    def auto_range(self, newval):
        # pylint: disable=no-member
        self.sendcmd('{}:RANGE:AUTO {}'.format(
            self.mode.value, '1' if newval else '0'))

    @property
    def input_range(self):
        """
        Gets/sets the upper limit of the current range.

        :type: `~pint.Quantity`
        """
        # pylint: disable=no-member
        mode = self.mode
        out = self.query('{}:RANGE:UPPER?'.format(mode.value))
        return float(out) * UNITS[mode]

    @input_range.setter
    def input_range(self, newval):
        # pylint: disable=no-member
        mode = self.mode
        val = newval.to(UNITS[mode]).magnitude
        if val not in self._valid_range(mode).value:
            raise ValueError(
                'Unexpected range limit for currently selected mode.')
        self.sendcmd('{}:RANGE:UPPER {:e}'.format(mode.value, val))

    # METHODS ##

    def auto_config(self, mode):
        """
        This command causes the device to do the following:
            - Switch to the specified mode
            - Reset all related controls to default values
            - Set trigger and arm to the 'immediate' setting
            - Set arm and trigger counts to 1
            - Set trigger delays to 0
            - Place unit in idle state
            - Disable all math calculations
            - Disable buffer operation
            - Enable autozero
        """
        self.sendcmd('CONF:{}'.format(mode.value))

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
        Trigger and acquire readings using the requested mode.
        Returns the measurement reading only.
        """
        # Check the current mode, change if necessary
        if mode is not None:
            if mode != self.mode:
                self.auto_config(mode)

        return self.read_measurements()[0]

    # PRIVATE METHODS ##

    def _valid_range(self, mode):
        if mode == self.Mode.voltage_dc:
            return self.ValidRange.voltage_dc
        if mode == self.Mode.current_dc:
            return self.ValidRange.current_dc
        if mode == self.Mode.resistance:
            return self.ValidRange.resistance
        if mode == self.Mode.charge:
            return self.ValidRange.charge

        raise ValueError('Invalid mode.')

    def _parse_measurement(self, ascii):
        # Split the string in three comma-separated parts (value, time, number of triggers)
        vals = ascii.split(',')
        reading = float(vals[0].split('N')[0]) * self.unit
        timestamp = float(vals[1].split('s')[0]) * u.second
        trigger_count = int(vals[2][:-5].split('R')[0])
        return reading, timestamp, trigger_count

# UNITS #######################################################################

UNITS = {
    Keithley6517b.Mode.voltage_dc:  u.volt,
    Keithley6517b.Mode.current_dc:  u.amp,
    Keithley6517b.Mode.resistance:  u.ohm,
    Keithley6517b.Mode.charge:      u.coulomb
}
