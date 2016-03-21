#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides support for the Keithley 6514 electrometer
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division
from builtins import map

from enum import Enum

import quantities as pq

from instruments.abstract_instruments import Electrometer
from instruments.generic_scpi import SCPIInstrument
from instruments.util_fns import bool_property, enum_property

# CLASSES #####################################################################


class Keithley6514(SCPIInstrument, Electrometer):

    """
    The `Keithley 6514`_ is an electrometer capable of doing sensitive current,
    charge, voltage and resistance measurements.

    Example usage:

    >>> import instruments as ik
    >>> import quantities as pq
    >>> dmm = ik.keithley.Keithley6514.open_gpibusb('/dev/ttyUSB0', 12)
    """

    # ENUMS #

    class Mode(Enum):
        """
        Enum containing valid measurement modes for the Keithley 6514
        """
        voltage = 'VOLT:DC'
        current = 'CURR:DC'
        resistance = 'RES'
        charge = 'CHAR'

    class TriggerMode(Enum):
        """
        Enum containing valid trigger modes for the Keithley 6514
        """
        immediate = 'IMM'
        tlink = 'TLINK'

    class ArmSource(Enum):
        """
        Enum containing valid trigger arming sources for the Keithley 6514
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
        Enum containing valid measurement ranges for the Keithley 6514
        """
        voltage = (2, 20, 200)
        current = (20e-12, 200e-12, 2e-9, 20e-9,
                   200e-9, 2e-6, 20e-6, 200e-6, 2e-3, 20e-3)
        resistance = (2e3, 20e3, 200e3, 2e6, 20e6, 200e6, 2e9, 20e9, 200e9)
        charge = (20e-9, 200e-9, 2e-6, 20e-6)

    # CONSTANTS #

    _MODE_UNITS = {
        Mode.voltage: pq.volt,
        Mode.current: pq.amp,
        Mode.resistance: pq.ohm,
        Mode.charge: pq.coulomb
    }

    # PRIVATE METHODS #

    def _valid_range(self, mode):
        if mode == self.Mode.voltage:
            return self.ValidRange.voltage
        elif mode == self.Mode.current:
            return self.ValidRange.current
        elif mode == self.Mode.resistance:
            return self.ValidRange.resistance
        elif mode == self.Mode.charge:
            return self.ValidRange.charge
        else:
            raise ValueError('Invalid mode.')

    def _parse_measurement(self, ascii):
        # TODO: don't assume ASCII data format # pylint: disable=fixme
        vals = list(map(float, ascii.split(',')))
        reading = vals[0] * self.unit
        timestamp = vals[1]
        status = vals[2]
        return reading, timestamp, status

    # PROPERTIES #

    # The mode values have quotes around them for some annoying reason.
    mode = enum_property(
        'FUNCTION',
        Mode,
        input_decoration=lambda val: val[1:-1],
        # output_decoration=lambda val: '"{}"'.format(val),
        set_fmt='{} "{}"',
        doc="""
        Gets/sets the measurement mode of the Keithley 6514.
        """
    )

    trigger_mode = enum_property(
        'TRIGGER:SOURCE',
        TriggerMode,
        doc="""
        Gets/sets the trigger mode of the Keithley 6514.
        """
    )

    arm_source = enum_property(
        'ARM:SOURCE',
        ArmSource,
        doc="""
        Gets/sets the arm source of the Keithley 6514.
        """
    )

    zero_check = bool_property(
        'SYST:ZCH',
        inst_true='ON',
        inst_false='OFF',
        doc="""
        Gets/sets the zero checking status of the Keithley 6514.
        """
    )

    zero_correct = bool_property(
        'SYST:ZCOR',
        inst_true='ON',
        inst_false='OFF',
        doc="""
        Gets/sets the zero correcting status of the Keithley 6514.
        """
    )

    @property
    def unit(self):
        return self._MODE_UNITS[self.mode]

    @property
    def auto_range(self):
        """
        Gets/sets the auto range setting

        :type: `bool`
        """
        # pylint: disable=no-member
        out = self.query('{}:RANGE:AUTO?'.format(self.mode.value))
        return True if out == '1' else False

    @auto_range.setter
    def auto_range(self, newval):
        # pylint: disable=no-member
        self.sendcmd('{}:RANGE:AUTO {}'.format(
            self.mode.value, '1' if newval else '0'))

    @property
    def input_range(self):
        """
        Gets/sets the upper limit of the current range.

        :type: `~quantities.Quantity`
        """
        # pylint: disable=no-member
        mode = self.mode
        out = self.query('{}:RANGE:UPPER?'.format(mode.value))
        return float(out) * self._MODE_UNITS[mode]

    @input_range.setter
    def input_range(self, newval):
        # pylint: disable=no-member
        mode = self.mode
        val = newval.rescale(self._MODE_UNITS[mode]).item()
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
        Returns a tuple of the form (reading, timestamp)
        """
        raw = self.query('FETC?')
        reading, timestamp, _ = self._parse_measurement(raw)
        return reading, timestamp

    def read_measurements(self):
        """
        Trigger and acquire readings using the current mode.
        Returns a tuple of the form (reading, timestamp)
        """
        raw = self.query('READ?')
        reading, timestamp, _ = self._parse_measurement(raw)
        return reading, timestamp
