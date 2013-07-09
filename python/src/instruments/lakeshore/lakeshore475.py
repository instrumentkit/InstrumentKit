#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# lakeshore475.py: Python class for the Lakeshore 475 Gaussmeter
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

import quantities as pq

from instruments.generic_scpi import SCPIInstrument

## CONSTANTS ###################################################################

LAKESHORE_FIELD_UNITS = {
    1: pq.gauss,
    2: pq.tesla,
    3: pq.oersted,
    4: pq.CompoundUnit('A/m')
}

LAKESHORE_TEMP_UNITS = {
    1: pq.celsius,
    2: pq.kelvin
}

LAKESHORE_FIELD_UNITS_INV = dict((v,k) for k,v in 
                                       LAKESHORE_FIELD_UNITS.items())
LAKESHORE_FIELD_UNITS_STR = dict((k.name,v) for k,v in 
                                            LAKESHORE_FIELD_UNITS_INV.items())
LAKESHORE_TEMP_UNITS_INV = dict((v,k) for k,v in 
                                       LAKESHORE_TEMP_UNITS.items())
LAKESHORE_TEMP_UNITS_STR = dict((k.name,v) for k,v in 
                                            LAKESHORE_TEMP_UNITS_INV.items())

## CLASSES #####################################################################

class Lakeshore475(SCPIInstrument):

    ## PROPERTIES ##

    @property
    def field(self):
        '''
        Read field from connected probe.
        
        :type: `~quantities.Quantity`
        '''
        return float(self.query('RDGFIELD?')) * self.field_units
        
    @property
    def field_units(self):
        '''
        Gets or sets the units of the Gaussmeter.
        If specified as a `str`, must be one of ``{Gauss|Tesla|Oersted|A/m}``.
        If specified as an `int`, must be in ``xrange(1, 5)``.
        
        :type: `~quantities.UnitQuantity`, `str` or `int`
        '''
        value = int(self.query('UNIT?'))
        return LAKESHORE_FIELD_UNITS[value]
    @field_units.setter
    def field_units(self, newval):
        if isinstance(newval, pq.unitquantity.UnitQuantity):
            if newval in LAKESHORE_FIELD_UNITS_INV:
                self.sendcmd('UNIT ' + LAKESHORE_FIELD_UNITS_INV[newval])
            else:
                raise ValueError('Not an acceptable Python quantities object')
        elif isinstance(newval, str):
            newval = newval.lower()
            if newval in LAKESHORE_FIELD_UNITS_STR:
                self.sendcmd('UNIT ' + LAKESHORE_FIELD_UNITS_STR[newval])
            else:
                raise ValueError('Field unit strings must be gauss, tesla, '
                                    'oersted or A/m')
        elif isinstance(newval, int):
            if newval in LAKESHORE_FIELD_UNITS:
                self.sendcmd('UNIT ' + newval)
            else:
                raise ValueError('Invalid field unit integer.')
        else:
            raise TypeError('Field units must be a string, integer, or '
                              'Python quantity')
        
    @property
    def temp_units(self):
        '''
        Gets or sets the temperature units of the Gaussmeter.
        If specified as a `str`, must be one of ``"Celsius"``
        or ``"Kelvin"``. If specified as an `int`, must be
        in ``xrange(1,3)``.
        
        :type: `~quantities.UnitQuantity`, `int` or `str`
        '''
        value = int(self.query('TUNIT?'))
        return LAKESHORE_TEMP_UNITS[value]
    @temp_units.setter
    def temp_units(self, newval):
        if isinstance(newval, pq.unitquantity.UnitQuantity):
            if newval in LAKESHORE_TEMP_UNITS_INV:
                self.sendcmd('TUNIT ' + LAKESHORE_TEMP_UNITS_INV[newval])
            else:
                raise ValueError('Not an acceptable Python quantities object')
        elif isinstance(newval, str):
            newval = newval.lower()
            if newval in LAKESHORE_TEMP_UNITS_STR:
                self.sendcmd('TUNIT ' + LAKESHORE_TEMP_UNITS_STR[newval])
            else:
                raise ValueError('Temperature unit strings must be celcius '
                                    'or kelvin')
        elif isinstance(newval, int):
            if newval in LAKESHORE_TEMP_UNITS:
                self.sendcmd('TUNIT ' + newval)
            else:
                raise ValueError('Invalid temperature unit integer.')
        else:
            raise TypeError('Temperature units must be a string, integer, '
                              'or Python quantity')

    
    ## METHODS ##

    def change_measurement_mode(self,mode,resolution,
                                filterType,peakMode,peakDisp):
        # TODO: almost all of this method is checking types
        #       and validity; absorb this into an enum, perhaps?
        '''
        Change the measurement mode of the Gaussmeter.
        
        mode: The desired measurement mode type
        mode = {DC|RMS|PEAK},string
        
        resolution: Digit resolution of the measured field.
        resolution = {3|4|5},integer
        
        filterType: Specify the signal filter used by the instrument. 
                    Available types include wide band, narrow band,
                    and low pass.
        filterType = {WIDE|NARROW|LOW PASS},string
        
        peakMode: Peak measurement mode to be used.
        peakMode = {PERIODIC|PULSE},string
        
        peakDisp: Peak display mode to be used.
        peakDisp = {POSITIVE|NEGATIVE|BOTH},string
        '''
        if not isinstance(mode, str):
            raise ValueError('Parameter "mode" must be a string.')
        if not isinstance(resolution, int):
            raise ValueError('Parameter "resolution" must be an integer.')
        if not isinstance(filterType, str):
            raise ValueError('Parameter "filterType" must be a string.')
        if not isinstance(peakMode, str):
            raise ValueError('Parameter "peakMode" must be a string.')
        if not isinstance(peakDisp, str):
            raise ValueError('Parameter "peakDisp" must be a string.')
        
        mode = mode.upper()
        filterType = filterType.upper()
        peakMode = peakMode.upper()
        peakDisp = peakDisp.upper()

        # Parse the measurement mode
        valid = ['DC','RMS','PEAK']
        if mode not in valid:
            raise ValueError('Only "DC", "RMS", and "PEAK" are '
                               'valid measurement modes.')
        else:
            mode = valid.index(mode) + 1

        # Parse the resolution
        if resolution in xrange(3, 6):
            resolution = resolution - 2
        else:
            raise ValueError('Only 3,4,5 are valid resolutions '
                               '(must be type int).')
        
        # Parse the filter type
        valid = ['WIDE','NARROW','LOW PASS']
        if filterType not in valid:
            raise ValueError('Only "WIDE", "NARROW", and "LOW PASS" '
                               'are valid filter types.')
        else:
            filterType = valid.index(filterType) + 1
        
        # Parse the peak measurement mode
        valid = ['PERIODIC','PULSE']
        if peakMode not in valid:
            raise ValueError('Only "PERIODIC" and "PULSE" peak '
                               'measurement modes are supported.')
        else:
            peakMode = valid.index(peakMode) + 1
            
        # Parse the peak display mode
        valid = ['POSITIVE','NEGATIVE','BOTH']
        if peakDisp not in valid:
            raise ValueError('Only "POSITIVE","NEGATIVE", and "BOTH" '
                               'are supported for display of peak reading.')
        else:
            peakDisp = valid.index(peakDisp) + 1
            
        self.sendcmd( 'RDGMODE %s,%s,%s,%s,%s' % (mode,resolution,filterType,
                                                peakMode,peakDisp) )
    

