#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# keithley580.py: Driver for the Keithley 580 micro-ohmmeter.
##
# © 2013 Willem Dijkstra (wpd@xs4all.nl).
#   2014 Steven Casagrande (scasagrande@galvant.ca)
#
# This file is a part of the InstrumentKit project.
# Licensed under the AGPL version 3.
##
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
##

## FEATURES ####################################################################

from __future__ import division

## IMPORTS #####################################################################

import time
import struct
from flufl.enum import enum

import quantities as pq
import numpy as np

from instruments.abstract_instruments import Instrument

## CLASSES #####################################################################

class Keithley580(Instrument):
    '''
    The Keithley Model 580 is a 4 1/2 digit resolution autoranging
    micro-ohmmeter with a +- 20,000 count LCD. It is designed for low
    resistance measurement requirements from 10uΩ to 200kΩ.

    The device needs some processing time (manual reports 300-500ms) after a
    command has been transmitted.
    '''

    def __init__(self, filelike):
        '''
        Initialise the instrument and remove CRLF line termination
        '''
        super(Keithley580, self).__init__(self, filelike)
        self.sendcmd('YX') # Removes the termination CRLF characters
                           # from the instruments
                           
    ## ENUMS ##
    
    class Polarity(Enum):
        positive = 0
        negative = 1
        
    class Drive(Enum):
        pulsed = 0
        dc = 1
        
    ## PROPERTIES ##

    @property
    def polarity(self, func):
        """
        Sets instrument polarity.
        
        Example use:
        
        >>> import instruments as ik
        >>> keithley = ik.keithley.Keithley580.open_gpibusb('/dev/ttyUSB0', 1)
        >>> keithley.polarity = keithley.Polarity.positive
        
        :type: `Keithley580.Polarity`
        """
        raise NotImplementedError
    @polarity.setter
    def polarity(self, newval):
        if isinstance(newval, str):
            newval = Keithley580.Polarity[newval]
        if newval not in Keithley580.Polarity:
            raise TypeError('Polarity must be specified as a ' 
                            'Keithley580.Polarity, got {} '
                            'instead.'.format(newval))
        
        self.sendcmd('P{}X'.format(newval.value))

    @property
    def drive(self, func):
        """
        Sets the instrument drive to either pulsed or DC.
        
        Example use:
        
        >>> import instruments as ik
        >>> keithley = ik.keithley.Keithley580.open_gpibusb('/dev/ttyUSB0', 1)
        >>> keithley.drive = keithley.Drive.pulsed
        
        :type: `Keithley580.Drive`
        """
        raise NotImplementedError
    @drive.setter
    def drive(self, newval):
        if  isinstance(newval, str):
            newval = Keithley580.Drive[newval]
        if newval not in Keithley580.Drive:
            raise TypeError('Drive must be specified as a ' 
                            'Keithley580.Drive, got {} '
                            'instead.'.format(newval))

        self.sendcmd('D{}X'.format(newval.value))

    ## METHODS ## 

    def trigger(self):
        '''
        Tell the Keithley 580 to execute all commands that it has received.
        
        Do note that this is different from the standard SCPI \*TRG command
        (which is not supported by the 580 anyways).
        '''
        self.sendcmd('X')

    def dry_circuit_test(self, dc):
        if not isinstance(dc, bool):
            raise TypeError('DryCircuitTest mode must be a boolean.')

        self.sendcmd('C{}X'.format(int(dc)))


    def set_resistance_range(self, res):
        if isinstance(res, str):
            res = res.lower()
            if res == 'auto':
                res = 0
            else:
                raise ValueError('Only valid string for resistance '
                                 'range is "auto".')
        elif isinstance(res, float) or isinstance(res, int):
            valid = [2e-1, 2e0, 2e1, 2e2, 2e3, 2e4, 2e5]
            if res in valid:
                res = valid.index(res) + 1
            else:
                raise ValueError('Valid resistance ranges are: '
                                 '{}'.format(valid))
        else:
            raise TypeError('Instrument resistance range must be specified '
                            'as a float, integer, or string.')

        self.sendcmd('R{}X'.format(res))


    def set_auto_range(self):
        """
        Turn on auto range for the Keithley 580.
        
        This is the same as calling the `Keithley580.set_resistance_range`
        method and setting the parameter to "AUTO".
        """
        self.sendcmd('R0X')


    def set_operate(self, dc):
        if not isinstance(dc, bool):
            raise TypeError('Operate mode must be a boolean.')

        self.sendcmd('O{}X'.format(int(dc)))


    def set_relative(self, dc):
        if not isinstance(dc, bool):
            raise TypeError('Operate mode must be a boolean.')

        self.sendcmd('Z{}X'.fomrat(int(dc)))


    def set_calibration_value(self, value):
        # self.write('V+n.nnnnE+nn')
        raise NotImplementedError('setCalibrationValue not implemented')


    def store_calibration_constants(self):
        # self.write('L0X')
        raise NotImplementedError('setCalibrationConstants not implemented')


    def set_trigger(self, trigger):
        if not isinstance(func, str):
            raise TypeError('Trigger mode must be a string.')
        func = func.lower()

        valid = {'talk:continuous': 0,
                 'talk:one-shot' : 1,
                 'get:continuous': 2,
                 'get:one-shot' : 3,
                 'x:continuous': 4,
                 'x:one-shot' : 5 }

        if valid.has_key(func):
            func = valid[func]
        else:
            raise ValueError('Valid trigger modes '
                             'are: ' + ', '.join(valid.keys()))

        self.sendcmd('T{}X'.format(func))


    def get_status_word(self):
        '''
        The keithley will not always respond with the statusword when asked. We
        use a simple heuristic here: request it up to 5 times, using a 1s
        delay to allow the keithley some thinking time.
        '''
        tries = 5
        statusword = ''
        while statusword[:3] != '580' and tries != 0:
            tries -= 1
            self.sendcmd('U0X')
            time.sleep(1)
            self.sendcmd('+read')
            statusword = self._file.read(-1).strip() # Be sure to replace this
                                                     # during refactoring

        if statusword == None:
            raise IOError('could not retrieve status word')

        return statusword[:-1]


    def parse_status_word(self, statusword):
        if statusword[:3] != '580':
            raise ValueError('Status word starts with wrong '
                             'prefix: {}'.format(statusword))

        (drive, polarity, drycircuit, operate, rng, \
         relative, eoi, trigger, sqrondata, sqronerror, linefreq, \
         terminator) = struct.unpack('@8c2s2s2c', statusword[3:])

        valid = { 'drive'      : { '0': 'pulsed',
                                   '1': 'dc' },
                  'polarity'   : { '0': '+',
                                   '1': '-' },
                  'range'      : { '0': 'auto',
                                   '1': '0.2',
                                   '2': '2',
                                   '3': '20',
                                   '4': '200',
                                   '5': '2k',
                                   '6': '20k',
                                   '7': '200k' },
                  'linefreq'   : { '0': '60Hz',
                                   '1': '50Hz' }}

        try:
            drive = valid['drive'][drive]
            polarity = valid['polarity'][polarity]
            rng = valid['range'][rng]
            linefreq = valid['linefreq'][linefreq]
        except:
            raise RuntimeError('Cannot parse status '
                               'word: {}'.format(statusword))

        return { 'drive': drive,
                 'polarity': polarity,
                 'drycircuit': (drycircuit == '1'),
                 'operate': (operate == '1'),
                 'range': rng,
                 'relative': (relative == '1'),
                 'eoi': eoi,
                 'trigger': (trigger == '1'),
                 'sqrondata': sqrondata,
                 'sqronerror': sqronerror,
                 'linefreq' : linefreq,
                 'terminator' : terminator }


    def get_measurement(self):
        self.trigger()
        self.sendcmd('+read')
        return self._file.read(-1).strip() # Be sure to replace this 
                                           # during refactoring


    def parse_measurement(self, measurement):
        (status, polarity, drycircuit, drive, resistance, terminator) = \
            struct.unpack('@4c11sc', measurement)

        valid = { 'status'     : { 'S' : 'standby',
                                   'N' : 'normal',
                                   'O' : 'overflow',
                                   'Z' : 'relative' },
                  'polarity'   : { '+' : '+',
                                   '-' : '-' },
                  'drycircuit' : { 'N' : False,
                                   'D' : True },
                  'drive'      : { 'P' : 'pulsed',
                                   'D' : 'dc' }}
        try:
            status = valid['status'][status]
            polarity = valid['polarity'][polarity]
            drycircuit = valid['drycircuit'][drycircuit]
            drive = valid['drive'][drive]
            resistance = float(resistance)
        except:
            raise Exception('Cannot parse measurement: {}'.format(measurement))

        return { 'status': status,
                 'polarity': polarity,
                 'drycircuit': drycircuit,
                 'drive': drive,
                 'resistance': resistance }
