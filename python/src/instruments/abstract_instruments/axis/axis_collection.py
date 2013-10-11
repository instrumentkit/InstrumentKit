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

import abc

from instruments.events import Event, event_property

## CLASSES #####################################################################

class AxisCollection(object):
    __metaclass__ = abc.ABCMeta
    
    ## INITIALIZER ##
    
    def __init__(self):
        # Setup events.
        self._on_start_scan = Event()
        
    ## PROPERTIES ##
    
    on_start_scan = event_property('_on_start_scan', doc="""
        Event fired whenever a scan across this axis collection is started.
    """)
    
    @abc.abstractproperty
    def is_hardware_scannable(self): pass
    
    @abc.abstractproperty
    def limits(self): pass
    
    @abc.abstractproperty
    def get_position(self): pass

    # should return a quantities.quantity.Quantity
    @abc.abstractproperty
    def units(self): pass
       
    ## METHODS ##
    
    @abc.abstractmethod
    def move(self, position, absulote=True):
        """
        Moves the axis to the given position.
        
        :param position: An iterable specifying the position of each axis to 
            move to. Position can be unitful,
        :param bool absolute: Absolute movement if True, relative movement 
            if false.
        """
        pass
    
    @abc.abstractmethod
    def scan(self, coords, dwell_time=None):
        """
        Scans the axes through a parametric path.
        
        :param coords: An iterable (whose length is equal to the number of 
            axes) where each element is an iterable specifying the path of 
            the respective axis.
        :param dwell_time: The amount of time to wait between each point in 
            the scan. Can be set to None to wait for no time.
        """
        # This method should be called by derived classes to ensure that the
        # event is fired correctly.
        self.on_start_scan(coords)
        
    @abc.abstractmethod
    def raster(self, start, stop, num, dwell_time=None):
        """
        Sets up the scan method with a path that fills a (hyper)-rectangle of
        the axes parameter space. Whether this path is constructed snake-style 
        or typerwriter-style or else is decided by the particular 
        implementation of axes in question.
        
        :param start: An iterable specifying the start position of each axis.
        :param stop: An iterable specifying the stop position of each axis.
        :param num: An iterable specifying how many steps to take to get from
            start to stop for each axis.
        :param dwell_time: The amount of time to wait between each point in 
            the scan. Can be set to None to wait for no time.
        """
        pass
    
    # Require implementors to say how long they are (that is, how many axes).
    @abc.abstractmethod
    def __len__(self):
        pass