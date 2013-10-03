#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# axis_collection.py: Represents a collection of axis-devices.
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

from instruments.util_fns import ProxyList
from axis_collection import AxisCollection
from axis import Axis

## CLASSES #####################################################################

class AxisList(ProxyList, AxisCollection):
    
    def __init__(self, parent, proxy_cls, valid_set):
        if not isinstance(proxy_cls, Axis):
            raise TypeError('Only Axis classes are allowed in AxisList, '
                            'received type {}.'.format(type(proxy_cls)))
        super(AxisList, self).__init__(parent, proxy_cls, valid_set)
        self._is_rasterable = False
        self._valid_set = valid_set
        
    ## PROPERTIES ##
    
    @property
    def is_hardware_rasterable(self):
        return self._is_rasterable
    @is_hardware_rasterable.setter
    def is_hardware_rasterable(self, newval):
        if newval:
            self._is_rasterable = True
        else:
            self._is_rasterable = False
            
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
        """
        Gets/sets the position of each Axis attached to this AxisList.
        """
        pos = []
        for i in self._valid_set:
            pos.append(self[i].position)
        return tuple(pos)
    @position.setter
    def position(self, newval):
        if not isinstance(newval, tuple) or not isinstance(newval, list):
            raise TypeError('AxisList position must be specified as a tuple or'
                            ' as a list, got {}.'.format(type(newval)))
        if len(self._valid_set) is not len(newval):
            raise ValueError('Not enough positions specified. Expected {} '
                             'got {}.'.format(len(self._valid_set), len(newval)))
        for i in xrange(len(newval)):
            self[self._valid_set[i]].position = newval[i]
    
    ## METHODS ##
    
    def move(self, *args, absolute=True):
        raise NotImplementedError
        
    def raster(self):
        raise NotImplementedError
