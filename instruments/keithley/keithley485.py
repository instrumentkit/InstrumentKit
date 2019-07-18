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

from enum import IntEnum

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

    class Mode(IntEnum):
        """
        Enum containing the supported mode codes
        """
        #: DC Current
        current_dc = 0

    class Polarity(IntEnum):
        """
        Enum containing valid polarity modes for the Keithley 485
        """
        positive = 0
        negative = 1

    class Drive(IntEnum):
        """
        Enum containing valid drive modes for the Keithley 485
        """
        pulsed = 0
        dc = 1

    class TriggerMode(IntEnum):
        """
        Enum containing valid trigger modes for the Keithley 485
        """
        talk_continuous = 0
        talk_one_shot = 1
        get_continuous = 2
        get_one_shot = 3
        trigger_continuous = 4
        trigger_one_shot = 5

    # PROPERTIES #

    @property
    def polarity(self):
        """
        Gets/sets instrument polarity.

        Example use:

        >>> import instruments as ik
        >>> keithley = ik.keithley.Keithley485.open_gpibusb('/dev/ttyUSB0', 1)
        >>> keithley.polarity = keithley.Polarity.positive

        :type: `Keithley485.Polarity`
        """
        value = self.parse_status_word(self.get_status_word())['polarity']
        if value == '+':
            return Keithley485.Polarity.positive
        elif value == '-':
            return Keithley485.Polarity.negative
        else:
            raise ValueError('Not a valid polarity returned from '
                             'instrument, got {}'.format(value))

    @polarity.setter
    def polarity(self, newval):
        if isinstance(newval, str):
            newval = Keithley485.Polarity[newval]
        if not isinstance(newval, Keithley485.Polarity):
            raise TypeError('Polarity must be specified as a '
                            'Keithley485.Polarity, got {} '
                            'instead.'.format(newval))

        self.sendcmd('P{}X'.format(newval.value))

    @property
    def drive(self):
        """
        Gets/sets the instrument drive to either pulsed or DC.

        Example use:

        >>> import instruments as ik
        >>> keithley = ik.keithley.Keithley485.open_gpibusb('/dev/ttyUSB0', 1)
        >>> keithley.drive = keithley.Drive.pulsed

        :type: `Keithley485.Drive`
        """
        value = self.parse_status_word(self.get_status_word())['drive']
        return Keithley485.Drive[value]

    @drive.setter
    def drive(self, newval):
        if isinstance(newval, str):
            newval = Keithley485.Drive[newval]
        if not isinstance(newval, Keithley485.Drive):
            raise TypeError('Drive must be specified as a '
                            'Keithley485.Drive, got {} '
                            'instead.'.format(newval))

        self.sendcmd('D{}X'.format(newval.value))

    @property
    def dry_circuit_test(self):
        """
        Gets/sets the 'dry circuit test' mode of the Keithley 485.

        This mode is used to minimize any physical and electrical changes in
        the contact junction by limiting the maximum source voltage to 20mV.
        By limiting the voltage, the measuring circuit will leave the resistive
        surface films built up on the contacts undisturbed. This allows for
        measurement of the resistance of these films.

        See the Keithley 485 manual for more information.

        :type: `bool`
        """
        return self.parse_status_word(self.get_status_word())['drycircuit']

    @dry_circuit_test.setter
    def dry_circuit_test(self, newval):
        if not isinstance(newval, bool):
            raise TypeError('DryCircuitTest mode must be a boolean.')
        self.sendcmd('C{}X'.format(int(newval)))

    @property
    def operate(self):
        """
        Gets/sets the operating mode of the Keithley 485. If set to true, the
        instrument will be in operate mode, while false sets the instruments
        into standby mode.

        :type: `bool`
        """
        return self.parse_status_word(self.get_status_word())['operate']

    @operate.setter
    def operate(self, newval):
        if not isinstance(newval, bool):
            raise TypeError('Operate mode must be a boolean.')
        self.sendcmd('O{}X'.format(int(newval)))

    @property
    def relative(self):
        """
        Gets/sets the relative measurement mode of the Keithley 485.

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
        self.sendcmd('Z{}X'.format(int(newval)))

    @property
    def trigger_mode(self):
        """
        Gets/sets the trigger mode of the Keithley 485.

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

        :type: `Keithley485.TriggerMode`
        """
        raise NotImplementedError

    @trigger_mode.setter
    def trigger_mode(self, newval):
        if isinstance(newval, str):
            newval = Keithley485.TriggerMode[newval]
        if newval not in Keithley485.TriggerMode:
            raise TypeError('Drive must be specified as a '
                            'Keithley485.TriggerMode, got {} '
                            'instead.'.format(newval))
        self.sendcmd('T{}X'.format(newval.value))

    @property
    def input_range(self):
        """
        Gets/sets the range of the Keithley 485 input terminals. The valid
        ranges are one of ``{AUTO|2e-9|2e-8|2e-7|2e-6|2e-5|2e-4|2e-3}``

        :type: `~quantities.quantity.Quantity` or `str`
        """
        value = float(self.parse_status_word(self.get_status_word())['range'])
        return value * pq.amp

    @input_range.setter
    def input_range(self, newval):
        valid = ('auto', 2e-9, 2e-8, 2e-7, 2e-6, 2e-5, 2e-4, 2e-3)
        if isinstance(newval, str):
            newval = newval.lower()
            if newval == 'auto':
                self.sendcmd('R0X')
                return
            else:
                raise ValueError('Only "auto" is acceptable when specifying '
                                 'the input range as a string.')
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
        self.sendcmd('R{}X'.format(newval))

    # METHODS #

    def trigger(self):
        """
        Tell the Keithley 485 to execute all commands that it has received.

        Do note that this is different from the standard SCPI ``*TRG`` command
        (which is not supported by the 485 anyways).
        """
        self.sendcmd('X')

    def auto_range(self):
        """
        Turn on auto range for the Keithley 485.

        This is the same as calling the `Keithley485.set_current_range`
        method and setting the parameter to "AUTO".
        """
        self.sendcmd('R0X')

    def set_calibration_value(self, value):
        """
        Sets the calibration value. This is not currently implemented.

        :param value: Calibration value to write
        """
        # self.write('V+n.nnnnE+nn')
        raise NotImplementedError('setCalibrationValue not implemented')

    def store_calibration_constants(self):
        """
        Instructs the instrument to store the calibration constants. This is
        not currently implemented.
        """
        # self.write('L0X')
        raise NotImplementedError('setCalibrationConstants not implemented')

    def get_status_word(self):
        """
        The keithley will not always respond with the statusword when asked. We
        use a simple heuristic here: request it up to 5 times, using a 1s
        delay to allow the keithley some thinking time.

        :rtype: `str`
        """
        tries = 5
        statusword = ''
        while statusword[:3] != '485' and tries != 0:
            tries -= 1
            self.sendcmd('U0X')
            time.sleep(1)
            statusword = self.query('')

        if statusword is None:
            raise IOError('could not retrieve status word')

        return statusword[:-1]

    def parse_status_word(self, statusword):
        """
        Parse the status word returned by the function
        `~Keithley485.get_status_word`.

        Returns a `dict` with the following keys:
        ``{drive,polarity,drycircuit,operate,range,relative,eoi,trigger,
        sqrondata,sqronerror,linefreq,terminator}``

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

        valid = {'range':       {b'0': 'auto',
                                 b'1': 2e-9,
                                 b'2': 2e-8,
                                 b'3': 2e-7,
                                 b'4': 2e-6,
                                 b'5': 2e-5,
                                 b'6': 2e-4,
                                 b'7': 2e-3},
                 'eoi':         {b'0': 'send',
                                 b'1': 'omit'},
                 'trigger':     {b'0': 'continuous_ontalk',
                                 b'1': 'oneshot_ontalk',
                                 b'2': 'continuous_onget',
                                 b'3': 'oneshot_onget',
                                 b'4': 'continuous_onx',
                                 b'5': 'oneshot_onx'},
                 'datamask':    {b'00': 'srq_disabled',
                                 b'01': 'read_of',
                                 b'08': 'read_done',
                                 b'09': 'read_done_of',
                                 b'16': 'busy',
                                 b'17': 'busy_read_of',
                                 b'24': 'busy_read_done',
                                 b'25': 'busy_read_done_of'},
                 'errormask':   {b'00': 'srq_disabled',
                                 b'01': 'idcc0',
                                 b'02': 'idcc',
                                 b'03': 'idcc0_idcc',
                                 b'04': 'not_remote',
                                 b'05': 'not_remote_iddc0',
                                 b'06': 'not_remote_idcc',
                                 b'07': 'not_remote_idcc0_idcc'}
                }

        try:
            range = valid['range'][range]
            eoi = valid['eoi'][eoi]
            trigger = valid['trigger'][trigger]
            datamask = valid['datamask'][datamask]
            errormask = valid['errormask'][errormask]
        except:
            raise RuntimeError('Cannot parse status '
                               'word: {}'.format(statusword))

        return {'zerocheck': zerocheck == 1,
                'log': log == 1,
                'range': range,
                'relative': relative == 1,
                'eoi': eoi,
                'trigger': trigger,
                'datamask': datamask,
                'errormask': errormask,
                'terminator':self.terminator}

    def measure(self, mode=Mode.current_dc):
        """
        Perform a measurement with the Keithley 485.

        The usual mode parameter is defaulted for the Keithley 485 as the only
        valid mode is current.

        :rtype: `~quantities.quantity.Quantity`
        """
        if not isinstance(mode, Keithley485.Mode):
            raise ValueError('This mode is not supported: {}'.format(mode.name))

        self.trigger()
        return self.parse_measurement(self.query(''))['current']

    @staticmethod
    def parse_measurement(measurement):
        """
        Parse the measurement string returned by the instrument.

        Returns a dict with the following keys:
        ``{status,polarity,drycircuit,drive,current}``

        :param measurement: String to be unpacked and parsed
        :type: `str`

        :rtype: `dict`
        """
        (status, function, base, current) = \
            struct.unpack('@1c2s1c10s', bytes(measurement, 'utf-8'))

        valid = {'status':    {b'N': 'normal',
                               b'C': 'zerocheck',
                               b'O': 'overflow',
                               b'Z': 'relative'},
                 'function':  {b'DC': 'dc-current'},
                 'base':      {b'A': '10',
                               b'L': 'log10'}}
        try:
            status = valid['status'][status]
            function = valid['function'][function]
            base = valid['base'][base]
            current = float(current) * pq.amp
        except:
            raise Exception('Cannot parse measurement: {}'.format(measurement))

        return {'status': status,
                'function': function,
                'base': base,
                'current': current}
