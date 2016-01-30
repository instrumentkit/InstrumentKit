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

## IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division
from future.utils import with_metaclass

import abc

from instruments.abstract_instruments import Instrument

## CLASSES #####################################################################

class Multimeter(with_metaclass(abc.ABCMeta, Instrument)):

    ## PROPERTIES ##

    @property
    @abc.abstractmethod
    def mode(self):
        raise NotImplementedError

    @mode.setter
    @abc.abstractmethod
    def mode(self, newval):
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def trigger_mode(self):
        raise NotImplementedError

    @trigger_mode.setter
    @abc.abstractmethod
    def trigger_mode(self, newval):
        raise NotImplementedError
    
    @property
    @abc.abstractmethod
    def relative(self):
        raise NotImplementedError

    @relative.setter
    @abc.abstractmethod
    def relative(self, newval):
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def input_range(self):
        raise NotImplementedError

    @input_range.setter
    @abc.abstractmethod
    def input_range(self, newval):
        raise NotImplementedError

    ## METHODS ##
    
    @abc.abstractmethod
    def measure(self, mode):
        '''
        Perform a measurement as specified by mode parameter.
        '''
        raise NotImplementedError
        
