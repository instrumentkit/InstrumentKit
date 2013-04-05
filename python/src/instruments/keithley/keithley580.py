#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# Filename: keithley580.py
#
# Copyright (c) 2012  Willem Dijkstra <wpd@xs4all.nl>
#
# This work is released under the Creative Commons Attribution-Sharealike 3.0
# license.  See http://creativecommons.org/licenses/by-sa/3.0/ or the included
# license/LICENSE.TXT file for more information.

from instruments.abstract_instruments import Instrument
import time
import struct

class Keithley580(Instrument):
    '''
    The Keithley Model 580 is a 4 1/2 digit resolution autoranging
    micro-ohmmeter with a +- 20,000 count LCD. It is designed for low
    resistance measurement requirements from 10uΩ to 200kΩ.

    The device needs some processing time (manual reports 300-500ms) after a
    command has been transmitted.
    '''

    def __init__(self, port, address, timeout_length):
        '''
        Initialise the instrument and replace CRLF line termination with ':'CR
        '''
        super(Keithley580, self).__init__(self, port, address, timeout_length)
        self.write('Y:X')


    def trigger(self):
        self.write('X')


    def setPolarity(self, func):
        if not isinstance(func, str):
            raise Exception('Polarity mode must be a string.')
        func = func.lower()

        valid = {'positive': 0, '+': 0,
                 'negative': 1, '-': 1}

        if valid.has_key(func):
            func = valid[func]
        else:
            raise Exception('Valid drive modes are: ' + ', '.join(valid.keys()))

        self.write('P' + str(func) + 'X')


    def setDrive(self, func):
        if not isinstance(func, str):
            raise Exception('Drive mode must be a string.')
        func = func.lower()

        valid = ['pulsed', 'dc']

        if func in valid:
            func = valid.index(func)
        else:
            raise Exception('Valid drive modes are: ' + str(valid))

        self.write('D' + str(func) + 'X')


    def setDryCircuitTest(self, dc):
        if not isinstance(dc, bool):
            raise Exception('DryCircuitTest mode must be a boolean.')

        self.write('C' + int(dc) + 'X')


    def setResistanceRange(self, res):
        if isinstance(res, str):
            res = res.lower()
            if res == 'auto':
                res = 0
            else:
                raise Exception('Only valid string for resistance range is "auto".')
        elif isinstance(res, float) or isinstance(res, int):
            valid = [2e-1, 2e0, 2e1, 2e2, 2e3, 2e4, 2e5]
            if res in valid:
                res = valid.index(res) + 1
            else:
                raise Exception('Valid resistance ranges are: ' + str(valid))
        else:
            raise Exception('Instrument resistance range must be specified as a float, integer, or string.')

        self.write('R' + res + 'X')


    def setAutoRange(self):
        self.write('R0X')


    def setOperate(self, dc):
        if not isinstance(dc, bool):
            raise Exception('Operate mode must be a boolean.')

        self.write('O' + int(dc) + 'X')


    def setRelative(self, dc):
        if not isinstance(dc, bool):
            raise Exception('Operate mode must be a boolean.')

        self.write('Z' + str(int(dc)) + 'X')


    def setCalibrationValue(self, value):
        # self.write('V+n.nnnnE+nn')
        raise Exception('setCalibrationValue not implemented')


    def storeCalibrationConstants(self):
        # self.write('L0X')
        raise Exception('setCalibrationConstants not implemented')


    def setTrigger(self, trigger):
        if not isinstance(func, str):
            raise Exception('Trigger mode must be a string.')
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
            raise Exception('Valid trigger modes are: ' + ', '.join(valid.keys()))

        self.write('T' + str(func) + 'X')


    def getStatusWord(self):
        '''
        The keithley will not always respond with the statusword when asked. We
        use a simple heuristic here: request it up to 5 times, using a 1s
        delay to allow the keithley some thinking time.
        '''
        tries = 5
        statusword = ''
        while statusword[:3] != '580' and tries != 0:
            tries -= 1
            self.write('U0X')
            time.sleep(1)
            self.write('+read')
            statusword = self.readline()[:-1]

        if statusword == None:
            raise Exception('could not retrieve status word')

        return statusword[:-1]


    def parseStatusWord(self, statusword):
        if statusword[:3] != '580':
            raise Exception('status word starts with wrong prefix: %s' % statusword)

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
            raise Exception('cannot parse status word: %s' % statusword)

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


    def getMeasurement(self):
        self.trigger()
        self.write('+read')
        return self.readline()[:-1]


    def parseMeasurement(self, measurement):
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
            raise Exception('cannot parse measurement: %s' % measurement)

        return { 'status': status,
                 'polarity': polarity,
                 'drycircuit': drycircuit,
                 'drive': drive,
                 'resistance': resistance }
