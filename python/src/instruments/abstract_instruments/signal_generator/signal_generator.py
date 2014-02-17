#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# signal_generator.py: Python ABC for Signal Generators (eg microwave sources)
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

## CLASSES #####################################################################

class SignalGenerator(Instrument):
    """
    Python abstract base class for signal generators (eg microwave sources).
    
    This ABC is not for function generators, which have their own separate ABC.
    
    .. seealso::
        `~instruments.FunctionGenerator`
    """
    __metaclass__ = abc.ABCMeta
    
    ## PROPERTIES ##
    
    @abc.abstractproperty
    def channel(self):
        """
        Gets a specific channel object for the SignalGenerator.
        
        :rtype: A class inherited from `~instruments.SGChannel`
        """
        raise NotImplementedError
        
