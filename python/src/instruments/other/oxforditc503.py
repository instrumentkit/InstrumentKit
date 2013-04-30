#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# oxforditc503.py: Driver for the Oxford ITC 503 temperature controller.
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

from instruments.abstract_instruments import Instrument

## CLASSES #####################################################################

class OxfordITC503(Instrument):
    def __init__(self, filelike):
        super(OxfordITC503, self).__init__(filelike)
        self.sendcmd('C3') # Enable remote commands
        self.terminator = 13 # Set EOS char to CR
       
    def read_temp(self, probe_num):
        '''
        Read temperature of an attached probe to the Oxford ITC503.
        
        Returns a float containing the temperature of the specified probe 
        in Kelvin.
        
        :param int probe_num: Attached probe number that will be used for 
            reading the temperature. One of {1|2|3}.
        
        :rtype: `float`
        '''
        if(probe_num not in [1,2,3]):
            raise ValueError('Only 1,2,3 are valid probe numbers for '
                               'Oxford ITC 503')
        
        temp = self.query('R{}'.format(probe_num))
        temp = temp[1:len(temp)] # Remove the first character ('R')
        temp = float(temp) # Convert to float
        
        return temp
