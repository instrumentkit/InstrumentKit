#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# lakeshore340.py: Driver for the Lakeshore 340 cryogenic temp controller.
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

from instruments.generic_scpi import SCPIInstrument

## CLASSES #####################################################################

class Lakeshore340(SCPIInstrument):
        
    def temperature(self, sensor):
        '''
        Read temperature of specified sensor.
        
        :param int sensor: Sensor number to query.
        
        :rtype: `float`
        '''
        if not isinstance(sensor, int):
            raise TypeError('Sensor must be specified as an int.')
        return float(self.query('KRDG?{}'.format(sensor)))
