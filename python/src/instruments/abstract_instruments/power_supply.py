#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# power_supply.py: Python ABC for power supplies
##
# © 2014 Steven Casagrande (scasagrande@galvant.ca).
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

import abc

from instruments.abstract_instruments import Instrument

## CLASSES #####################################################################

class PowerSupplyChannel(object):
    __metaclass__ = abc.ABCMeta
    
    ## PROPERTIES ##
    
    def getmode(self):
        """
        Get/set the mode for this channel
        """
        raise NotImplementedError
    def setmode(self, newval):
        raise NotImplementedError
    mode = abc.abstractproperty(getmode, setmode)
    
    def getvoltage(self):
        """
        Get/set the voltage for this channel
        """
        raise NotImplementedError
    def setvoltage(self, newval):
        raise NotImplementedError
    voltage = abc.abstractproperty(getvoltage, setvoltage)
    
    def getcurrent(self):
        """
        Get/set the current for this channel
        """
        raise NotImplementedError
    def setcurrent(self, newval):
        raise NotImplementedError
    current = abc.abstractproperty(getcurrent, setcurrent)
    
    def getoutput(self):
        """
        Get/set the output state of this channel
        """
        raise NotImplementedError
    def setoutput(self, newval):
        raise NotImplementedError
    output = abc.abstractproperty(getoutput, setoutput)
    

class PowerSupply(Instrument):
    __metaclass__ = abc.ABCMeta
    
    ## PROPERTIES ##
    
    @abc.abstractproperty
    def channel(self):
        raise NotImplementedError
    
    def getvoltage(self):
        """
        Get/set the voltage for all channels
        """
        raise NotImplementedError
    def setvoltage(self, newval):
        raise NotImplementedError
    voltage = abc.abstractproperty(getvoltage, setvoltage)
    
    def getcurrent(self):
        """
        Get/set the current for all channels
        """
        raise NotImplementedError
    def setcurrent(self, newval):
        raise NotImplementedError
    current = abc.abstractproperty(getcurrent, setcurrent)
    
    
