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
from axis_controller import Axis

## CLASSES #####################################################################

class AxisCollection(object):
    __metaclass__ = abc.ABCMeta
        
    ## PROPERTIES ##
    
    @abc.abstractproperty
    def is_hardware_rasterable(self):
        raise NotImplementedError
    
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
    def move(self, *args, absolute=True):
        raise NotImplementedError
    
    @abc.abstractmethod
    def raster(self):
        raise NotImplementedError
