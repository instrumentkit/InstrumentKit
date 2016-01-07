#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# channel.py: Python ABC for Signal Generators output channels
##
# © 2013-2014 Steven Casagrande (scasagrande@galvant.ca).
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

class SGChannel(object):
    """
    Python abstract base class representing a single channel for a signal 
    generator. 
    
    .. warning:: This class should NOT be manually created by the user. It is 
        designed to be initialized by the `~instruments.SignalGenerator` class.
    """
    __metaclass__ = abc.ABCMeta
    
    ## PROPERTIES ##
    
    def getfreq(self):
        """
        Gets/sets the output frequency of the SG channel
        """
        raise NotImplementedError
    def setfreq(self):
        raise NotImplementedError
    freq = abc.abstractproperty(getfreq, setfreq)
    
    def getpower(self):
        """
        Gets/sets the output power of the SG channel
        """
        raise NotImplementedError
    def setpower(self):
        raise NotImplementedError
    power = abc.abstractproperty(getpower, setpower)
    
    def getphase(self):
        """
        Gets/sets the output phase of the SG channel
        """
        raise NotImplementedError
    def setphase(self):
        raise NotImplementedError
    phase = abc.abstractproperty(getphase, setphase)
    
    def getoutput(self):
        """
        Gets/sets the output status of the device. IE enabling output turns on
        the RF connector.
        """
        raise NotImplementedError
    def setoutput(self):
        raise NotImplementedError
    output = abc.abstractproperty(getoutput, setoutput)
