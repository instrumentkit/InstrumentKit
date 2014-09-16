#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# multimeter.py: Python class for electrometers
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

class Electrometer(Instrument):
    __metaclass__ = abc.ABCMeta

    ## PROPERTIES ##
    
    def _getmode(self):
        """
        Read measurement mode the electrometer is currently in.
        """
        raise NotImplementedError
    def _setmode(self, newval):
        """
        Change the mode the electrometer is in.
        """
        raise NotImplementedError
    mode = abc.abstractproperty(_getmode, _setmode)

    @abc.abstractproperty
    def unit(self):
        """
        Returns the unit corresponding to the current mode.
        """
        raise NotImplementedError
    
    def _gettrigger_mode(self):
        """
        Get the current trigger mode the electrometer is set to.
        """
        raise NotImplementedError
    def _settrigger_mode(self, newval):
        """
        Set the electrometer triggering mode.
        """
        raise NotImplementedError
    trigger_mode = abc.abstractproperty(_gettrigger_mode, _settrigger_mode)
    
   
    def _getinput_range(self):
        """
        Get the current input range setting of the electrometer.
        """
        raise NotImplementedError
    def _setinput_range(self, newval):
        """
        Set the input range setting of the electrometer.
        """
        raise NotImplementedError
    input_range = abc.abstractproperty(_getinput_range, _setinput_range)

    
    def _getzero_check(self):
        """
        Get the current zero check status.
        """
        raise NotImplementedError
    def _setzero_check(self, newval):
        """
        Set the current zero check status.
        """
        raise NotImplementedError
    zero_check = abc.abstractproperty(_getzero_check, _setzero_check)

    def _getzero_correct(self):
        """
        Get the current zero correct status.
        """
        raise NotImplementedError
    def _setzero_correct(self, newval):
        """
        Set the current zero correct status.
        """
        raise NotImplementedError
    zero_correct = abc.abstractproperty(_getzero_correct, _setzero_correct)
    
    
    ## METHODS ##

    @abc.abstractmethod
    def fetch(self):
        '''
        Request the latest post-processed readings using the current mode. 
        (So does not issue a trigger)
        '''
        raise NotImplementedError

    @abc.abstractmethod
    def read(self):
        '''
        Trigger and acquire readings using the current mode.
        '''
        raise NotImplementedError
        
        
