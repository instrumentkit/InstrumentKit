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

from instruments.abstract_instruments import Instrument
from instruments.events import Event, event_property
from .axis import Axis

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
    
    def get_is_hardware_scannable(self):
        raise NotImplementedError
    def set_is_hardware_scannable(self):
        raise NotImplementedError
    is_hardware_scannable = abc.abstractproperty(get_is_hardware_scannable,
                                                  set_is_hardware_scannable)
    
    def getlimits(self):
        raise NotImplementedError
    def setlimits(self, newval):
        raise NotImplementedError
    limits = abc.abstractproperty(getlimits, setlimits)
    
    def getposition(self):
        raise NotImplementedError
    def setposition(self, newval):
        raise NotImplementedError
    position = abc.abstractproperty(getposition, setposition)
       
    ## METHODS ##
    
    @abc.abstractmethod
    def move(self, *args, **kwargs):
        # NOTE: (*args, absolute=True) causes a syntax error, so unfortunately
        #       we have to hade absolute in **kwargs.
        raise NotImplementedError
    
    @abc.abstractmethod
    def scan(self, dwell_time, *coords):
        # This method should be called by derived classes to ensure that the
        # event is fired correctly.
        self.on_start_scan(coords)
        
    # Require implementors to say how long they are (that is, how many axes).
    @abc.abstractmethod
    def __len__(self):
        pass
        
    def raster(self, start, stop, num):
        # TODO: arange over start:end:step to generate arguments to scan.
        raise NotImplementedError
    
