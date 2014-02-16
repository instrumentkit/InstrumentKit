#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# axis_list.py: A ProxyList-type class used to generate lists of Axis.
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
                            'but received type {}.'.format(type(proxy_cls)))
        super(AxisList, self).__init__(parent, proxy_cls, valid_set)
        
        # Make sure we store the indices for this axis list as a tuple, such
        # that the order is predictible.
        self._valid_set = tuple(valid_set)
        
    ## PROPERTIES ##
    
    @property
    def is_hardware_scannable(self):
        return False
    @property
    def finest_axes(self):
        return self
        
    @property
    def limits(self):
        return [axis.limits for axis in self]
        
    @property
    def position(self):
        """
        Gets/sets the position of each Axis attached to this AxisList.
        """
        return tuple(axis.position for axis in self)
    @position.setter
    def position(self, newval):
        if not isinstance(newval, tuple) or not isinstance(newval, list):
            raise TypeError('AxisList position must be specified as a tuple or'
                            ' as a list, got {}.'.format(type(newval)))
        if len(self._valid_set) is not len(newval):
            raise ValueError('Wrong number of positions specified. Expected {} '
                             'got {}.'.format(len(self._valid_set), len(newval)))
        for axis, newpos in zip(self, newval):
            axis.position = newpos
    
    ## METHODS ##
    
    # TODO!
    
    def _move(self, position, absolute=True):
        for axis, axis_pos in zip(self, position):
            axis.move(axis_pos, absolute)
        
    def _raster(self):
        raise NotImplementedError
        
    def _scan(self, coords, dwell_time=None):
        raise NotImplementedError
    
