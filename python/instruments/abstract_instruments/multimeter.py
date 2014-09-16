#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# multimeter.py: Python class for multimeters
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

## CLASSES #####################################################################

class Multimeter(Instrument):
    __metaclass__ = abc.ABCMeta

    ## PROPERTIES ##
    
    def getmode(self):
        """
        Read measurement mode the multimeter is currently in.
        """
        raise NotImplementedError
    def setmode(self, newval):
        """
        Change the mode the multimeter is in.
        """
        raise NotImplementedError
    mode = abc.abstractproperty(getmode, setmode)
    
    def gettrigger_mode(self):
        """
        Get the current trigger mode the multimeter is set to.
        """
        raise NotImplementedError
    def settrigger_mode(self, newval):
        """
        Set the multimeter triggering mode.
        """
        raise NotImplementedError
    trigger_mode = abc.abstractproperty(gettrigger_mode, settrigger_mode)
    
    def getrelative(self):
        """
        Get the status of relative measuring mode (usually on or off).
        """
        raise NotImplementedError
    def setrelative(self, newval):
        """
        Set (enable/disable) the relative measuring mode of the multimeter.
        """
        raise NotImplementedError
    relative = abc.abstractproperty(getrelative, setrelative)
    
    def getinput_range(self):
        """
        Get the current input range setting of the multimeter.
        """
        raise NotImplementedError
    def setinput_range(self, newval):
        """
        Set the input range setting of the multimeter.
        """
        raise NotImplementedError
    input_range = abc.abstractproperty(getinput_range, setinput_range)
    
    
    
    ## METHODS ##
    
    @abc.abstractmethod
    def measure(self, mode):
        '''
        Perform a measurement as specified by mode parameter.
        '''
        raise NotImplementedError
        
