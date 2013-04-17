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

from instruments.generic_scpi import SCPIInstrument
from instruments.util_fns import assume_units

from instruments.units import dBm

## ENUMS #######################################################################

class SRS345VoltageMode(Enum):
    peak_to_peak = "VP"
    rms = "VR"

class SRS345Function(Enum):
    sinusoid = 0
    square = 1
    triangle = 2
    ramp = 3
    noise = 4
    arbitrary = 5
    

## FUNCTIONS ###################################################################

class SRS345(SCPIInstrument):
    # TODO: docstring
    # FIXME: need to add OUTX 1 here, but doing so seems to cause a syntax
    #        error on the instrument.
        
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
            `SRS345VoltageMode`, or a `~quantities.Quantity` if no voltage mode
            applies.
        '''
        resp = self.query("AMPL?").strip()
        mag = float(resp[:-2]) # Strip off units and convert to float.
        units = resp[-2:]
        if units == "DB":
            return pq.Quantity(mag, dBm)
        else:
            return pq.Quantity(mag, pq.V), SRS345VoltageMode[units]

    @amplitude.setter
    def amplitude(self, newval):
        
        # Try and rescale to dBm... if it succeeds, set the magnitude
        # and units accordingly, otherwise handle as a voltage.
        try:
            newval_dBm = newval.rescale(dBm)
            mag = float(newval_dBm.magnitude)
            units = "DB"
        except (AttributeError, ValueError):
            # OK, we have volts. Now, do we have a tuple? If not, assume Vpp.
            if not isinstance(newval, tuple):
                mag = newval
                units = SRS345VoltageMode.peak_to_peak
            else:
                mag, units = newval
                
            # Get the mneonic for the units.
            units = units.value
                
            # Finally, convert the magnitude out to a float.
            mag = float(assume_units(mag, pq.V).rescale(pq.V).magnitude)
        
        
        self.sendcmd("AMPL {mag}{units}".format(mag=mag, units=units))
                
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
        return pq.Quantity(float(self.query("OFFS?")), pq.V)
    @offset.setter
    def offset(self, newval):
        '''
        Gets/sets the offset voltage for the output waveform.
        
        :units: As specified, or assumed to be :math:`\\text{V}` otherwise.
        :type: `float` or `~quantities.Quantity`
        '''
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
        
        
