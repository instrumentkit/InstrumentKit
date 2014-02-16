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

## FEATURES ####################################################################

from __future__ import division

## IMPORTS #####################################################################

import abc

## CLASSES #####################################################################

class Axis(object):
    """
    Axis representing a single physical axis-object such as a stepper motor,
    galvos, piezo stages, etc.
    
    At its most basic, an axis is something that has a position and that can be
    moved. By querying and setting the position, the origin for this axis
    can be defined, while the :meth:`~Axis.move` method instructs the device
    exposing this axis to move to a specified position.
    
    .. warning::
    
        This class shoult NOT be manually created by the user.
    """
    __metaclass__ = abc.ABCMeta
        
    def __init__(self, parent, idx):
        self._parent = parent
        self._idx = idx
        
    ## ABSTRACT PROPERTIES ##
    
    @abc.abstractproperty
    def position(self):
        raise NotImplementedError
    
    @abc.abstractproperty
    def velocity(self):
        raise NotImplementedError

    ## ABSTRACT METHODS ##
    
    @abc.abstractmethod
    def move(self, new_position, absolute=True):
        """
        Instructs the device exposing this axis to move to a given position.
        """
        pass
    
    ## CONCRETE PROPERTIES ##
    
    @property
    def limits(self):
        """
        Returns the limits to which this axis can travel as a tuple ``(lower,
        upper)``. If no limit is known or exists, then the relevant tuple
        element is `None`.
        """
        # TODO: enforce limits in move and position.
        # By default, there are no limits given.
        return (None, None)
        
