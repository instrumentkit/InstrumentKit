#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# single_channel_sg.py: Python class for Signal Generators with only 1 channel.
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

## FEATURES ####################################################################

from __future__ import division

## IMPORTS #####################################################################

import abc

from instruments.abstract_instruments import Instrument
from signal_generator import SignalGenerator
from channel import SGChannel
from instruments.util_fns import ProxyList

## CLASSES #####################################################################

class SingleChannelSG(SignalGenerator, SGChannel):
    """
    Class for representing a Signal Generator that only has a single output
    channel. The sole property in this class allows for the user to use the API
    for SGs with multiple channels and a more compact form since it only has 
    one output.
    
    For example, both of the following calls would work the same:
    
    >>> print sg.channel[0].freq # Multi-channel style
    >>> print sg.freq # Compact style
    
    """
    
    ## PROPERTIES ##
    
    @property
    def channel(self):
        return (self,)
