#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# perp_ac.py: AxisCollection (AC) that contains a list of perpendicular ACs
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

from axis_collection import AxisCollection

## CLASSES #####################################################################

class PerpendicularAC(AxisCollection):

    def __init__(self, parent_ac):
        if not isinstance(parent_ac, list):
            raise TypeError('PerpendicularAC must be given only a list of '
                            'AxisCollection objects, instead got '
                            '{}.'.format(type(parent_ac)))
        for i in parent_ac:
            if not isinstance(i, AxisCollection):
                raise TypeError('PerpendicularAC must be given only '
                                'AxisCollection objects in a list, instead '
                                ' got {}.'.format(type(i)))
        self._parent = parent_ac
        
    ## PROPERTIES ##
    
    @property
    def is_hardware_rasterable(self):
        is_raster = []
        for parent in self._parent:
            is_raster.append(parent.is_hardware_rasterable)
        return tuple(is_raster)
    @is_hardware_rasterable.setter
    def is_hardware_rasterable(self, newval):
        if not isinstance(newval, list):
            raise TypeError('PerpendicularAC.is_hardware_rasterable must be '
                            'given only as a list, instead got '
                            '{}.'.format(type(newval)))
        for i in xrange(len(newval)):
            self._parent[i].is_hardware_rasterable = newval[i]
            
    @property
    def limits(self):
        """
        Gets/sets the flag used to signify if the Axis within this AxisList
        are rasterable.
        """
        raise NotImplementedError
    @limits.setter
    def limits(self, newval):
        raise NotImplementedError
        
    @property
    def position(self):
        pos = []
        for parent in self._parent:
            pos.append(parent.position)
        return tuple(pos)
    @position.setter
    def position(self, newval):
        if not isinstance(newval, list):
            raise TypeError('PerpendicularAC.position must be given only as a '
                            'list, instead got {}.'.format(type(newval)))
        for i in xrange(len(newval)):
            self._parent[i].position = newval[i]
            
    ## METHODS ##
    
    def move(self, *args, absolute=True):
        raise NotImplementedError
        
    def raster(self):
        raise NotImplementedError
