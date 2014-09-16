#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# oscilloscope.py: Python ABC for oscilloscopes
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

class OscilloscopeDataSource(object):
    __metaclass__ = abc.ABCMeta
    
    ## PROPERTIES ##
    
    @abc.abstractproperty
    def name(self):
        raise NotImplementedError
    
    ## METHODS ##
    
    @abc.abstractmethod
    def read_waveform(self, bin_format=True):
        raise NotImplementedError

class OscilloscopeChannel(object):
    __metaclass__ = abc.ABCMeta
    
    ## PROPERTIES ##
    
    def getcoupling(self):
        '''
        Gets the coupling settings for this channel
        '''
        raise NotImplementedError
    def setcoupling(self, newval):
        '''
        Sets the coupling settings for this channel
        '''
        raise NotImplementedError
    coupling = abc.abstractproperty(getcoupling, setcoupling)
        

class Oscilloscope(Instrument):
    __metaclass__ = abc.ABCMeta

    ## PROPERTIES ##
    
    @abc.abstractproperty
    def channel(self):
        raise NotImplementedError
        
    @abc.abstractproperty
    def ref(self):
        raise NotImplementedError
    
    @abc.abstractproperty
    def math(self):
        raise NotImplementedError
    
    ## METHODS ##
    
    @abc.abstractmethod
    def force_trigger(self):
        '''
        Forces a trigger event to occur on the attached oscilloscope.
        '''
        raise NotImplementedError
        
