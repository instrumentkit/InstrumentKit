#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# function_generator.py: Python ABC class for function generators
##
# © 2013 Steven Casagrande (scasagrande@galvant.ca).
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
##

## FEATURES ####################################################################

from __future__ import division

## IMPORTS #####################################################################

import abc

from instruments.abstract_instruments import Instrument
import instruments.units as u
from instruments.util_fns import assume_units

import quantities as pq

from flufl.enum import Enum

## CLASSES #####################################################################

class FunctionGenerator(Instrument):
    __metaclass__ = abc.ABCMeta

    ## ENUMS ##
    
    class VoltageMode(Enum):
        peak_to_peak = 'VPP'
        rms = 'VRMS'
        dBm = 'DBM'
    
    class Function(Enum):
        sinusoid = 'SIN'
        square = 'SQU'
        triangle = 'TRI'
        ramp = 'RAMP'
        noise = 'NOIS'
        arbitrary = 'ARB'
    
    ## ABSTRACT METHODS ##
    
    @abc.abstractmethod
    def _get_amplitude_(self):
        pass
    @abc.abstractmethod
    def _set_amplitude_(self, magnitude, units):
        pass
    
    ## ABSTRACT PROPERTIES ##
 
    """   
    def getamplitude(self):
        raise NotImplementedError('')
    def setamplitude(self, newval):
        raise NotImplementedError('')
    amplitude = abc.abstractproperty(getamplitude, setamplitude)
    """
    
    def getfrequency(self):
        raise NotImplementedError('')
    def setfrequency(self, newval):
        raise NotImplementedError('')
    frequency = abc.abstractproperty(getfrequency, setfrequency)
    
    def getfunction(self):
        raise NotImplementedError('')
    def setfunction(self, newval):
        raise NotImplementedError('')
    function = abc.abstractproperty(getfunction, setfunction)
    
    def getoffset(self):
        raise NotImplementedError('')
    def setoffset(self, newval):
        raise NotImplementedError('')
    offset = abc.abstractproperty(getoffset, setoffset)
    
    def getphase(self):
        raise NotImplementedError('')
    def setphase(self, newval):
        raise NotImplementedError('')
    phase = abc.abstractproperty(getphase, setphase)
    
    ## CONCRETE PROPERTIES ##
    
    @property
    def amplitude(self):
        '''
        Gets/sets the output amplitude of the function generator.
        
        If set with units of :math:`\\text{dBm}`, then no voltage mode can
        be passed.
        
        If set with units of :math:`\\text{V}` as a `~quantities.Quantity` or a
        `float` without a voltage mode, then the voltage mode is assumed to be
        peak-to-peak.
        
        :units: As specified, or assumed to be :math:`\\text{V}` if not
            specified.        
        :type: Either a `tuple` of a `~quantities.Quantity` and a
            `FunctionGenerator.VoltageMode`, or a `~quantities.Quantity` 
            if no voltage mode applies.
        '''
        mag, units = self._get_amplitude_()
                
        if units == self.VoltageMode.dBm:
            return pq.Quantity(mag, u.dBm)
        else:
            return pq.Quantity(mag, pq.V), units
    @amplitude.setter
    def amplitude(self, newval):
        # Try and rescale to dBm... if it succeeds, set the magnitude
        # and units accordingly, otherwise handle as a voltage.
        try:
            newval_dBm = newval.rescale(u.dBm)
            mag = float(newval_dBm.magnitude)
            units = self.VoltageMode.dBm
        except (AttributeError, ValueError):
            # OK, we have volts. Now, do we have a tuple? If not, assume Vpp.
            if not isinstance(newval, tuple):
                mag = newval
                units = self.VoltageMode.peak_to_peak
            else:
                mag, units = newval
                
            # Finally, convert the magnitude out to a float.
            mag = float(assume_units(mag, pq.V).rescale(pq.V).magnitude)
        
        self._set_amplitude_(mag, units)
        
