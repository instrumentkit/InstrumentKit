#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# srs345.py: Implements a driver for the SRS 345 function generator.
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
from flufl.enum._enum import EnumValue

import quantities as pq

from instruments import FunctionGenerator
from instruments.generic_scpi import SCPIInstrument
from instruments.util_fns import assume_units

from instruments.units import dBm

## ENUMS #######################################################################

class SRS345Function(Enum):
    sinusoid = 0
    square = 1
    triangle = 2
    ramp = 3
    noise = 4
    arbitrary = 5
    

## FUNCTIONS ###################################################################

class SRS345(SCPIInstrument, FunctionGenerator):
    # TODO: docstring
    # FIXME: need to add OUTX 1 here, but doing so seems to cause a syntax
    #        error on the instrument.
        
    ## CONSTANTS ##
    
    _UNIT_MNEMONICS = {
        FunctionGenerator.VoltageMode.peak_to_peak: "VP",
        FunctionGenerator.VoltageMode.rms:          "VR",
        FunctionGenerator.VoltageMode.dBm:          "DB",
    }
    
    _MNEMONIC_UNITS = {mnem: unit for unit, mnem in _UNIT_MNEMONICS.iteritems()}
    
    ## FunctionGenerator CONTRACT ##
    
    def _get_amplitude_(self):
        """
        
        """
        resp = self.query("AMPL?").strip()
        
        return (
            float(resp[:-2]),
            self._MNEMONIC_UNITS[resp[-2:]]
        )
        
    def _set_amplitude_(self, magnitude, units):
        """
        
        """
        self.sendcmd("AMPL {}{}".format(magnitude, self._UNIT_MNEMONICS[units]))
        
    ## PROPERTIES ##
        
    @property
    def frequency(self):
        '''
        Gets/sets the output frequency.
        
        :units: As specified, or assumed to be :math:`\\text{Hz}` otherwise.
        :type: `float` or `~quantities.Quantity`
        '''
        return pq.Quantity(float(self.query('FREQ?')), pq.Hz)
    @frequency.setter
    def frequency(self, newval):
        self.sendcmd("FREQ {}".format(
            assume_units(newval, pq.Hz).rescale(pq.Hz).magnitude)
        )
        
    @property
    def function(self):
        """
        Gets/sets the output function of the function generator.
        
        :type: `SRS345Function`
        """
        return SRS345Function[int(self.query("FUNC?"))]
    @function.setter
    def function(self, newval):
        # TODO: add type checking here.
        self.sendcmd("FUNC {}".format(newval.value))
        
    @property
    def offset(self):
        '''
        Gets/sets the offset voltage for the output waveform.
        
        :units: As specified, or assumed to be :math:`\\text{V}` otherwise.
        :type: `float` or `~quantities.Quantity`
        '''
        return pq.Quantity(float(self.query("OFFS?")), pq.V)
    @offset.setter
    def offset(self, newval):
        self.sendcmd("OFFS {}".format(
            assume_units(newval, pq.V).rescale(pq.V).magnitude
        ))
        
    @property
    def phase(self):
        '''
        Gets/sets the phase for the output waveform.
        
        :units: As specified, or assumed to be degrees (:math:`{}^{\\circ}`)
            otherwise.
        :type: `float` or `~quantities.Quantity`
        '''
        return pq.Quantity(float(self.query("PHSE?")), "degrees")
    @phase.setter
    def phase(self, newval):
        self.sendcmd("PHSE {}".format(
            assume_units(newval, "degrees").rescale("degrees").magnitude
        ))
        
