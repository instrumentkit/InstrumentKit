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

## IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division
from future.utils import with_metaclass

import abc

from instruments.abstract_instruments import Instrument

## CLASSES #####################################################################

class OscilloscopeDataSource(with_metaclass(abc.ABCMeta, object)):

    def __enter__(self):
        self._old_dsrc = self._tek.data_source
        if self._old_dsrc != self:
            # Set the new data source, and let __exit__ cleanup.
            self._tek.data_source = self
        else:
            # There's nothing to do or undo in this case.
            self._old_dsrc = None

    def __exit__(self, type, value, traceback):
        if self._old_dsrc is not None:
            self._tek.data_source = self._old_dsrc

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        else:
            return other.name == self.name
    
    ## PROPERTIES ##
    
    @abc.abstractproperty
    def name(self):
        raise NotImplementedError
    
    ## METHODS ##
    
    @abc.abstractmethod
    def read_waveform(self, bin_format=True):
        raise NotImplementedError

class OscilloscopeChannel(with_metaclass(abc.ABCMeta, object)):
    
    ## PROPERTIES ##

    @property
    @abc.abstractmethod
    def coupling(self):
        """
        Gets/sets the coupling setting for the oscilloscope. This is an
        abstract method.

        :type: `~enum.Enum`
        """
        raise NotImplementedError

    @coupling.setter
    @abc.abstractmethod
    def coupling(self, newval):
        raise NotImplementedError
        

class Oscilloscope(with_metaclass(abc.ABCMeta, Instrument)):

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
