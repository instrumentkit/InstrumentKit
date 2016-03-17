#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# keithley580.py: Driver for the Keithley 580 micro-ohmmeter.
#
# © 2013 Willem Dijkstra (wpd@xs4all.nl).
#   2014 Steven Casagrande (scasagrande@galvant.ca)
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
Driver for the HP6632b DC power supply

Originally contributed and copyright held by Willem Dijkstra (wpd@xs4all.nl)

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


class Keithley580(Instrument):

    """
    The Keithley Model 580 is a 4 1/2 digit resolution autoranging
    micro-ohmmeter with a +- 20,000 count LCD. It is designed for low
    resistance measurement requirements from 10uΩ to 200kΩ.

    The device needs some processing time (manual reports 300-500ms) after a
    command has been transmitted.
    """

    def __init__(self, filelike):
        """
        Initialise the instrument and remove CRLF line termination
        """
        super(Keithley580, self).__init__(filelike)
        self.sendcmd('Y:X')  # Removes the termination CRLF characters

    # ENUMS #

    class Polarity(IntEnum):
        """
        Enum containing valid polarity modes for the Keithley 580
        """
        positive = 0
        negative = 1

    class Drive(IntEnum):
        """
        Enum containing valid drive modes for the Keithley 580
        """
        pulsed = 0
        dc = 1

    class TriggerMode(IntEnum):
        """
        Enum containing valid trigger modes for the Keithley 580
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
        >>> keithley = ik.keithley.Keithley580.open_gpibusb('/dev/ttyUSB0', 1)
        >>> keithley.polarity = keithley.Polarity.positive

        :type: `Keithley580.Polarity`
        """
        value = self.parse_status_word(self.get_status_word())['polarity']
        if value == '+':
            return Keithley580.Polarity.positive
        elif value == '-':
            return Keithley580.Polarity.negative
        else:
            raise ValueError('Not a valid polarity returned from '
                             'instrument, got {}'.format(value))

    @polarity.setter
    def polarity(self, newval):
        if isinstance(newval, str):
            newval = Keithley580.Polarity[newval]
        if not isinstance(newval, Keithley580.Polarity):
            raise TypeError('Polarity must be specified as a '
                            'Keithley580.Polarity, got {} '
                            'instead.'.format(newval))

        self.sendcmd('P{}X'.format(newval.value))

    @property
    def drive(self):
        """
        Gets/sets the instrument drive to either pulsed or DC.

        Example use:

        >>> import instruments as ik
        >>> keithley = ik.keithley.Keithley580.open_gpibusb('/dev/ttyUSB0', 1)
        >>> keithley.drive = keithley.Drive.pulsed

        :type: `Keithley580.Drive`
        """
        value = self.parse_status_word(self.get_status_word())['drive']
        return Keithley580.Drive[value]

    @drive.setter
    def drive(self, newval):
        if isinstance(newval, str):
            newval = Keithley580.Drive[newval]
        if not isinstance(newval, Keithley580.Drive):
            raise TypeError('Drive must be specified as a '
                            'Keithley580.Drive, got {} '
                            'instead.'.format(newval))

        self.sendcmd('D{}X'.format(newval.value))

    @property
    def dry_circuit_test(self):
        """
        Gets/sets the 'dry circuit test' mode of the Keithley 580.

        This mode is used to minimize any physical and electrical changes in
        the contact junction by limiting the maximum source voltage to 20mV.
        By limiting the voltage, the measuring circuit will leave the resistive
        surface films built up on the contacts undisturbed. This allows for
        measurement of the resistance of these films.

        See the Keithley 580 manual for more information.

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
        Gets/sets the operating mode of the Keithley 580. If set to true, the
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
        Gets/sets the relative measurement mode of the Keithley 580.

        As stated in the manual: The relative function is used to establish a
        baseline reading. This reading is subtracted from all subsequent
        readings. The purpose of making relative measurements is to cancel test
        lead and offset resistances or to store an input as a reference level.

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
        Gets/sets the trigger mode of the Keithley 580.

        There are two different trigger settings for three different sources.
        This means there are six different settings for the trigger mode.

        The two types are continuous and one-shot. Continuous has the instrument
        continuously sample the resistance. One-shot performs a single
        resistance measurement.

        The three trigger sources are on talk, on GET, and on "X". On talk
        refers to addressing the instrument to talk over GPIB. On GET is when
        the instrument receives the GPIB command byte for "group execute
        trigger". Last, on "X" is when one sends the ASCII character "X" to the
        instrument. This character is used as a general execute to confirm
        commands send to the instrument. In InstrumentKit, "X" is sent after
        each command so it is not suggested that one uses on "X" triggering.

        :type: `Keithley580.TriggerMode`
        """
        raise NotImplementedError

    @trigger_mode.setter
    def trigger_mode(self, newval):
        if isinstance(newval, str):
            newval = Keithley580.TriggerMode[newval]
        if newval not in Keithley580.TriggerMode:
            raise TypeError('Drive must be specified as a '
                            'Keithley580.TriggerMode, got {} '
                            'instead.'.format(newval))
        self.sendcmd('T{}X'.format(newval.value))

    @property
    def input_range(self):
        """
        Gets/sets the range of the Keithley 580 input terminals. The valid
        ranges are one of ``{AUTO|2e-1|2|20|200|2000|2e4|2e5}``

        :type: `~quantities.quantity.Quantity` or `str`
        """
        value = float(self.parse_status_word(self.get_status_word())['range'])
        return value * pq.ohm

    @input_range.setter
    def input_range(self, newval):
        valid = ('auto', 2e-1, 2e0, 2e1, 2e2, 2e3, 2e4, 2e5)
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
        Tell the Keithley 580 to execute all commands that it has received.

        Do note that this is different from the standard SCPI ``*TRG`` command
        (which is not supported by the 580 anyways).
        """
        self.sendcmd('X')

    def auto_range(self):
        """
        Turn on auto range for the Keithley 580.

        This is the same as calling the `Keithley580.set_resistance_range`
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
        while statusword[:3] != '580' and tries != 0:
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
        `~Keithley580.get_status_word`.

        Returns a `dict` with the following keys:
        ``{drive,polarity,drycircuit,operate,range,relative,eoi,trigger,
        sqrondata,sqronerror,linefreq,terminator}``

        :param statusword: Byte string to be unpacked and parsed
        :type: `str`

        :rtype: `dict`
        """
        if statusword[:3] != '580':
            raise ValueError('Status word starts with wrong '
                             'prefix: {}'.format(statusword))

        (drive, polarity, drycircuit, operate, rng,
         relative, eoi, trigger, sqrondata, sqronerror,
         linefreq) = struct.unpack('@8c2s2s2', statusword[3:])

        valid = {'drive': {'0': 'pulsed',
                           '1': 'dc'},
                 'polarity': {'0': '+',
                              '1': '-'},
                 'range': {'0': 'auto',
                           '1': 0.2,
                           '2': 2,
                           '3': 20,
                           '4': 2e2,
                           '5': 2e3,
                           '6': 2e4,
                           '7': 2e5},
                 'linefreq': {'0': '60Hz',
                              '1': '50Hz'}}

        try:
            drive = valid['drive'][drive]
            polarity = valid['polarity'][polarity]
            rng = valid['range'][rng]
            linefreq = valid['linefreq'][linefreq]
        except:
            raise RuntimeError('Cannot parse status '
                               'word: {}'.format(statusword))

        return {'drive': drive,
                'polarity': polarity,
                'drycircuit': (drycircuit == '1'),
                'operate': (operate == '1'),
                'range': rng,
                'relative': (relative == '1'),
                'eoi': eoi,
                'trigger': (trigger == '1'),
                'sqrondata': sqrondata,
                'sqronerror': sqronerror,
                'linefreq': linefreq,
                'terminator': self.terminator}

    def measure(self):
        """
        Perform a measurement with the Keithley 580.

        The usual mode parameter is ignored for the Keithley 580 as the only
        valid mode is resistance.

        :rtype: `~quantities.quantity.Quantity`
        """
        self.trigger()
        return self.parse_measurement(self.query(''))['resistance']

    @staticmethod
    def parse_measurement(measurement):
        """
        Parse the measurement string returned by the instrument.

        Returns a dict with the following keys:
        ``{status,polarity,drycircuit,drive,resistance}``

        :param measurement: String to be unpacked and parsed
        :type: `str`

        :rtype: `dict`
        """
        (status, polarity, drycircuit, drive, resistance) = \
            struct.unpack('@4c11s', measurement)

        valid = {'status': {'S': 'standby',
                            'N': 'normal',
                            'O': 'overflow',
                            'Z': 'relative'},
                 'polarity': {'+': '+',
                              '-': '-'},
                 'drycircuit': {'N': False,
                                'D': True},
                 'drive': {'P': 'pulsed',
                           'D': 'dc'}}
        try:
            status = valid['status'][status]
            polarity = valid['polarity'][polarity]
            drycircuit = valid['drycircuit'][drycircuit]
            drive = valid['drive'][drive]
            resistance = float(resistance) * pq.ohm
        except:
            raise Exception('Cannot parse measurement: {}'.format(measurement))

        return {'status': status,
                'polarity': polarity,
                'drycircuit': drycircuit,
                'drive': drive,
                'resistance': resistance}

    # COMMUNICATOR METHODS #

    def sendcmd(self, msg):
        super(Keithley580, self).sendcmd(msg + ':')

    def query(self, msg, size=-1):
        return super(Keithley580, self).query(msg + ':', size)[:-1]
