#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# keithley485.py: Driver for the Keithley 485 pico-ampmeter.
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
Driver for the Keithley 485 pico-ampmeter.

Originally contributed and copyright held by Francois Drielsma
(francois.drielsma@gmail.com).

An unrestricted license has been provided to the maintainers of the Instrument
Kit project.
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division
import time
import struct

from enum import IntEnum, Enum

import quantities as pq

from instruments.abstract_instruments import Instrument

# CLASSES #####################################################################


class Keithley485(Instrument):

    """
    The Keithley Model 485 is a 4 1/2 digit resolution autoranging
    pico-ampmeter with a +- 20000 count LCD. It is designed for low
    current measurement requirements from 0.1pA to 2mA.

    The device needs some processing time (manual reports 300-500ms) after a
    command has been transmitted.
    """

    # ENUMS #

    class Trigger(IntEnum):
        """
        Enum containing valid trigger modes for the Keithley 485
        """
        continuous_ontalk = 0
        oneshot_ontalk = 1
        continuous_onget = 2
        oneshot_onget = 3
        continuous_onx = 4
        oneshot_onx = 5

    class SRQDataMask(IntEnum):
        """
        Enum containing valid SRQ data masks for the Keithley 485
        """
        srq_disabled = 0
        read_ovf = 1
        read_done = 8
        read_done_ovf = 9
        busy = 16
        busy_read_ovf = 17
        busy_read_done = 24
        busy_read_done_ovf = 25

    class SRQErrorMask(IntEnum):
        """
        Enum containing valid SRQ error masks for the Keithley 485
        """
        srq_disabled = 0
        idcco = 1
        idcc = 2
        idcco_idcc = 3
        not_remote = 4
        not_remote_idcco = 5
        not_remote_idcc = 6
        not_remote_idcco_idcc = 7

    class Status(Enum):
        """
        Enum containing valid status keys in the measurement string
        """
        normal = b'N'
        zerocheck = b'C'
        overflow = b'O'
        relative = b'Z'

    # PROPERTIES #

    @property
    def zero_check(self):
        """
        Gets/sets the 'zero check' mode (C) of the Keithley 485.

        Once zero check is enabled (C1 sent), the display can be
        zeroed with the REL feature or the front panel pot.

        See the Keithley 485 manual for more information.

        :type: `bool`
        """
        return self.parse_status_word(self.get_status_word())['zerocheck']

    @zero_check.setter
    def zero_check(self, newval):
        if not isinstance(newval, bool):
            raise TypeError('Zero Check mode must be a boolean.')
        self.query('C{}X'.format(int(newval)))

    @property
    def log(self):
        """
        Gets/sets the 'log' mode (D) of the Keithley 485.

        Once log is enabled (D1 sent), the device will return
        the logarithm of the current readings.

        See the Keithley 485 manual for more information.

        :type: `bool`
        """
        return self.parse_status_word(self.get_status_word())['log']

    @log.setter
    def log(self, newval):
        if not isinstance(newval, bool):
            raise TypeError('Log mode must be a boolean.')
        self.query('D{}X'.format(int(newval)))

    @property
    def range(self):
        """
        Gets/sets the range (R) of the Keithley 485 input terminals. The valid
        ranges are one of ``{AUTO|2e-9|2e-8|2e-7|2e-6|2e-5|2e-4|2e-3}``

        :type: `~quantities.quantity.Quantity` or `str`
        """
        value = float(self.parse_status_word(self.get_status_word())['range'])
        return value * pq.amp

    @range.setter
    def range(self, newval):
        valid = ('auto', 2e-9, 2e-8, 2e-7, 2e-6, 2e-5, 2e-4, 2e-3)
        if isinstance(newval, str):
            newval = newval.lower()
            if newval == 'auto':
                self.sendcmd('R0X')
                return
            else:
                raise ValueError('Only "auto" is acceptable when specifying '
                                 'the range as a string.')
        if isinstance(newval, pq.quantity.Quantity):
            newval = float(newval)

        if isinstance(newval, (float, int)):
            if newval in valid:
                newval = valid.index(newval)
            else:
                raise ValueError('Valid range settings are: {}'.format(valid))
        else:
            raise TypeError('Range setting must be specified as a float, int, '
                            'or the string "auto", got {}'.format(type(newval)))
        self.query('R{}X'.format(newval))

    @property
    def relative(self):
        """
        Gets/sets the relative measurement mode (Z) of the Keithley 485.

        As stated in the manual: The relative function is used to establish a
        baseline reading. This reading is subtracted from all subsequent
        readings. The purpose of making relative measurements is to cancel test
        lead and offset currents or to store an input as a reference level.

        Once a relative level is established, it remains in effect until another
        relative level is set. The relative value is only good for the range the
        value was taken on and higher ranges. If a lower range is selected than
        that on which the relative was taken, inaccurate results may occur.
        Relative cannot be activated when "OL" is displayed.

        See the manual for more information.

        :type: `bool`
        """
        return self.parse_status_word(self.get_status_word())['relative']

    @relative.setter
    def relative(self, newval):
        if not isinstance(newval, bool):
            raise TypeError('Relative mode must be a boolean.')
        self.query('Z{}X'.format(int(newval)))

    @property
    def trigger(self):
        """
        Gets/sets the trigger mode (T) of the Keithley 485.

        There are two different trigger settings for three different sources.
        This means there are six different settings for the trigger mode.

        The two types are continuous and one-shot. Continuous has the instrument
        continuously sample the current. One-shot performs a single
        current measurement.

        The three trigger sources are on talk, on GET, and on "X". On talk
        refers to addressing the instrument to talk over GPIB. On GET is when
        the instrument receives the GPIB command byte for "group execute
        trigger". Last, on "X" is when one sends the ASCII character "X" to the
        instrument. This character is used as a general execute to confirm
        commands send to the instrument. In InstrumentKit, "X" is sent after
        each command so it is not suggested that one uses on "X" triggering.

        It is recommended to leave it in the default mode (T0, continuous on talk),
        and simply ignore the output when other commands are called.

        :type: `Keithley485.Trigger`
        """
        return self.parse_status_word(self.get_status_word())['trigger']

    @trigger.setter
    def trigger(self, newval):
        if isinstance(newval, str):
            newval = Keithley485.Trigger[newval]
        if newval not in Keithley485.Trigger:
            raise TypeError('Drive must be specified as a '
                            'Keithley485.Trigger, got {} '
                            'instead.'.format(newval))
        self.query('T{}X'.format(newval.value))

    @property
    def eoi(self):
        """
        Gets/sets the 'eoi' mode (K) of the Keithley 485.

        The model 485 will normally send an end of interrupt (EOI)
        during the last byte of its data string or status word.
        The EOI reponse of the instrument may be included or omitted.
        Warning: the default setting (K0) includes it.

        See the Keithley 485 manual for more information.

        :type: `bool`
        """
        return not self.parse_status_word(self.get_status_word())['eoi']

    @eoi.setter
    def eoi(self, newval):
        if not isinstance(newval, bool):
            raise TypeError('EOI mode must be a boolean.')
        self.query('K{}X'.format(1-int(newval)))

    # METHODS #

    def auto_range(self):
        """
        Turn on auto range for the Keithley 485.

        This is the same as calling the `Keithley485.set_current_range`
        method and setting the parameter to "AUTO".
        """
        self.sendcmd('R0X')

    def get_status_word(self):
        """
        The device will not always respond with the statusword when asked. We
        use a simple heuristic here: request it up to 5 times, using a 1s
        delay to allow the keithley some thinking time.

        :rtype: `str`
        """
        tries = 5
        statusword = ''
        while statusword[:3] != '485' and tries != 0:
            statusword = self.query('U0X')
            tries -= 1

        if statusword is None:
            raise IOError('could not retrieve status word')

        return statusword[:-1]

    def parse_status_word(self, statusword):
        """
        Parse the status word returned by the function
        `~Keithley485.get_status_word`.

        Returns a `dict` with the following keys:
        ``{zerocheck,log,range,relative,eoi,relative,
        trigger,datamask,errormask,terminator}``

        :param statusword: Byte string to be unpacked and parsed
        :type: `str`

        :rtype: `dict`
        """
        if statusword[:3] != '485':
            raise ValueError('Status word starts with wrong '
                             'prefix: {}'.format(statusword))

        (zerocheck, log, range, relative, eoi,
         trigger, datamask, errormask) = \
            struct.unpack('@6c2s2s', bytes(statusword[3:], 'utf-8'))

        valid_range = {b'0': 'auto',
                       b'1': 2e-9,
                       b'2': 2e-8,
                       b'3': 2e-7,
                       b'4': 2e-6,
                       b'5': 2e-5,
                       b'6': 2e-4,
                       b'7': 2e-3}

        try:
            range = valid_range[range]
            trigger = self.Trigger(int(trigger)).name
            datamask = self.SRQDataMask(int(datamask)).name
            errormask = self.SRQErrorMask(int(errormask)).name
        except:
            raise RuntimeError('Cannot parse status '
                               'word: {}'.format(statusword))

        return {'zerocheck': zerocheck == b'1',
                'log': log == b'1',
                'range': range,
                'relative': relative == b'1',
                'eoi': eoi == b'0',
                'trigger': trigger,
                'datamask': datamask,
                'errormask': errormask,
                'terminator': self.terminator}

    def measure(self):
        """
        Perform a current measurement with the Keithley 485.

        :rtype: `~quantities.quantity.Quantity`
        """
        return self.parse_measurement(self.query('X'))

    def parse_measurement(self, measurement):
        """
        Parse the measurement string returned by the instrument.

        Returns the current formatted as a Quantity.

        :param measurement: String to be unpacked and parsed
        :type: `str`

        :rtype: `dict`
        """
        (status, function, base, current) = \
            struct.unpack('@1c2s1c10s', bytes(measurement, 'utf-8'))

        try:
            status = self.Status(status)
            if status != self.Status.normal:
                raise ValueError('Instrument not in normal mode: {}'.format(status.name))
            current = float(current) * pq.amp if base == b'A' else 10**(float(current)) * pq.amp
        except:
            raise Exception('Cannot parse measurement: {}'.format(measurement))

        return current
