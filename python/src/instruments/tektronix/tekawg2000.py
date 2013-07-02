#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# tekawg2000.py: Driver for the Tektronix AWG2000 series.
##
# © 2013 Steven Casagrande (scasagrande@galvant.ca).
#
# This file is a part of the GPIBUSB adapter project.
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

from flufl.enum import Enum

import numpy as np
import quantities as pq

from instruments.generic_scpi import SCPIInstrument
from instruments.util_fns import assume_units, ProxyList

## CLASSES #####################################################################

class TekAWG2000Channel(object):
    def __init__(self, tek, idx):
        if not isinstance(tek, TekAWG2000):
            raise TypeError("Don't do that.")
        self._tek = tek
        # Zero-based for pythonic convienence, so we need to convert to
        # Tektronix's one-based notation here.
        self._name = 'CH{}'.format(idx + 1)
        
        # Remember what the old data source was for use as a context manager.
        self._old_dsrc = None
        
    ## PROPERTIES ##
    
    @property
    def name(self):
        '''
        Gets the name of this AWG channel
        
        :type: `str`
        '''
        return self._name
    
    @property
    def amplitude(self):
        '''
        Gets/sets the amplitude of the specified channel.
        
        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of units Volts.
        :type: `~quantities.Quantity` with units Volts peak-to-peak.
        '''
        return pq.Quantity(
            float(self._tek.query('FG:{}:AMPL?'.format(self._name)).strip()),
            pq.V
            )
    @amplitude.setter
    def amplitude(self, newval):
        self._tek.sendcmd('FG:{}:AMPL {}'.format(
            self._name,
            assume_units(newval, pq.V).rescale(pq.V).magnitude
        ))
    
    @property
    def offset(self):
        '''
        Gets/sets the offset of the specified channel.
        
        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of units Volts.
        :type: `~quantities.Quantity` with units Volts.
        '''
        return pq.Quantity(
            float(self._tek.query('FG:{}:OFFS?'.format(self._name)).strip()),
            pq.V
            )
    @offset.setter
    def offset(self, newval):
        self._tek.sendcmd('FG:{}:OFFS {}'.format(
            self._name,
            assume_units(newval, pq.V).rescale(pq.V).magnitude
        ))
    
    @property
    def frequency(self):
        '''
        Gets/sets the frequency of the specified channel when using the built-in
        function generator.
        
        ::units: As specified (if a `~quantities.Quantity`) or assumed to be
            of units Hertz.
        :type: `~quantities.Quantity` with units Hertz.
        '''
        return pq.Quantity(
            float(self._tek.query('FG:FREQ?').strip()),
            pq.Hz
            )
    @frequency.setter
    def frequency(self, newval):
        self._tek.sendcmd('FG:FREQ {}HZ'.format(
            assume_units(newval, pq.Hz).rescale(pq.Hz).magnitude
        ))
    
    @property
    def polarity(self):
        '''
        Gets/sets the polarity of the specified channel.
        
        :type: `TekAWG2000.Polarity`
        '''
        return TekAWG2000.Polarity[self._tek.query('FG:{}:POL?'.format(
                                                self._name)).strip()]
    @polarity.setter
    def polarity(self, newval):
        if newval.enum is not TekAWG2000.Polarity:
            raise TypeError('Polarity settings must be a `TekAWG2000.Polarity` '
                'value, got {} instead.'.format(type(newval)))
        
        self._tek.sendcmd('FG:{}:POL {}'.format(self._name, newval.value))
        
    @property
    def shape(self):
        '''
        Gets/sets the waveform shape of the specified channel. The AWG will use 
        the internal function generator for these shapes.
        
        :type: `TekAWG2000.Shape` 
        '''
        return TekAWG2000.Shape[self._tek.query('FG:{}:SHAP?'.format(
                                            self._name)).strip().split(',')[0]]
    @shape.setter
    def shape(self, newval):
        if newval.enum is not TekAWG2000.Shape:
            raise TypeError('Shape settings must be a `TekAWG2000.Shape` '
                'value, got {} instead.'.format(type(newval)))
        self._tek.sendcmd('FG:{}:SHAP {}'.format(self._name, newval.value))
        
class TekAWG2000(SCPIInstrument):
    '''
    Communicates with a Tektronix AWG2000 series instrument using the SCPI
    commands documented in the user's guide.
    '''
    
    ## ENUMS ##
    
    class Polarity(Enum):
        normal = 'NORMAL'
        inverted = 'INVERTED'
        
    class Shape(Enum):
        sine = 'SINUSOID'
        pulse = 'PULSE'
        ramp = 'RAMP'
        square = 'SQUARE'
        triangle = 'TRIANGLE'
    
    ## Properties ##
    
    @property
    def channel(self):
        return ProxyList(self, TekAWG2000Channel, xrange(2))
