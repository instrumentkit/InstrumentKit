#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# scpi_instrument.py: Provides base class for SCPI-controlled instruments.
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
##

## FEATURES ####################################################################

from __future__ import division

## IMPORTS #####################################################################

from instruments.abstract_instruments import Instrument

## CLASSES #####################################################################

class SCPIInstrument(Instrument):
    
    def __init__(self, filelike):
        super(SCPIInstrument, self).__init__(self, filelike)
    
    ## PROPERTIES ##
    
    @property
    def name(self):
        return self.query('*IDN?')
        
    @property
    def op_complete(self):
        result = self.query('OPC?')
        return int(result)
    
    @property
    def power_on_status(self):
        result = self.query('*PSC?')
    @power_on_status.setter
    def power_on_status(self, newval):
        on = ['on', '1', 1]
        off = ['off', '0', 0]
        if isinstance(newval, str):
            newval = newval.lower()
        if newval in on:
            self.write('*PSC 1')
        elif newval in off:
            self.write('*PSC 0')
        else:
            raise ValueError
    
    @property
    def self_test_ok(self):
        result = self.query('*TST?')
        try:
            result = int(result)
            return result == 0
        except:
            return False
    
    ## BASIC SCPI COMMANDS ##
    
    def reset(self):
        self.write('*RST')
        
    def clear(self):
        self.write('*CLS')
    
    def trigger(self):
        self.write('*TRG')
    
    def wait_to_continue(self):
        self.write('*WAI')
