#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# function_generator.py: Python ABC class for function generators
##
# © 2013 Steven Casagrande (scasagrande@galvant.ca).
#
# This file is a part of the GPIBUSB adapter project.
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

class FunctionGenerator(Instrument):
    __metaclass__ = abc.ABCMeta
    
    ## PROPERTIES ##
    
    def getamplitude(self):
        raise NotImplementedError('')
    def setamplitude(self, newval):
        raise NotImplementedError('')
    amplitude = abc.abstractproperty(getamplitude, setamplitude)
    
    def getfrequency(self):
        raise NotImplementedError('')
    def setfrequency(self, newval):
        raise NotImplementedError('')
    frequency = abc.abstractproperty(getfrequency, setfrequency)
    
    def getfunction(self):
        raise NotImplementedError('')
    def setfunction(self, newval):
        raise NotImplementedError('')
    function = abc.abstractproperty(getfunction, setfunction)
    
    def getoffset(self):
        raise NotImplementedError('')
    def setoffset(self, newval):
        raise NotImplementedError('')
    offset = abc.abstractproperty(getoffset, setoffset)
    
    def getphase(self):
        raise NotImplementedError('')
    def setphase(self, newval):
        raise NotImplementedError('')
    phase = abc.abstractproperty(getphase, setphase)
