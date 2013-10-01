#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# axis.py: Provides base class axis-objects.
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

## CLASSES #####################################################################

class _Axis(object):
    """
    Axis representing a single physical axis-object such as a stepper motor,
    galvos, piezo stages, etc.
    
    .. warning:: This class shoult NOT be manually created by the user.
    """
    __metaclass__ = abc.ABCMeta
        
    def __init__(self, parent, idx):
        self._parent = parent
        self._idx = idx
        
    ## PROPERTIES ##
    
    def getposition(self):
        raise NotImplementedError
    def setposition(self, newval):
        raise NotImplementedError
    position = abc.abstractproperty(getposition, setposition)
    
    def getvelocity(self):
        raise NotImplementedError
    def setvelocity(self):
        raise NotImplementedError
    velocity = abc.abstractproperty(getvelocity, setvelocity)
