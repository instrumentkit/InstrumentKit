#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# axis_collection.py: Represents a collection of axis-devices.
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

## FEATURES ###################################################################

from __future__ import division

## IMPORTS ####################################################################

import abc
import functools
from itertools import izip

from instruments.events import Event, event_property

## DECORATORS #################################################################

def update_history(fn):
    """
    Decorates the input function so that the date_modified property of the 
    first argument (usually called 'self') is set to the current timestamp.
    """
    @functools.wraps(fn)
    def move_wrapper(self, coords, absolute=True):
        self._move_history = [coords] + self._move_history
        self._move_history = self._move_history[:self._max_history_length]
        return fn(self, coords, absolute=absolute)
    return move_wrapper

## CLASSES ####################################################################

class AxisCollection(object):
    """
    Abstract class whose derived classes represent collections of axes. 
    Instances of these derived classes can be nested in powerful ways to 
    allow for the creation of complicated axis systems with a simple 
    interface.    
    """
    __metaclass__ = abc.ABCMeta
    
    ## INITIALIZER ##
    
    def __init__(self):
        # Setup events.
        self._on_scan_start = Event(self)
        self._on_scan_complete = Event(self)
        self._on_scan_step = Event(self)
        # Useful to have the startup position in the history
        self._move_history = [self.position]
        
    ## PROPERTIES ##
    
    # By default, remember the last 100 move coordinates
    _max_history_length = 100
    
    # Events publicly exposed
    on_scan_start = event_property('_on_scan_start', doc="""
        Event fired just before a scan/raster across this axis collection is started.
    """)
    on_scan_complete = event_property('_on_scan_complete', doc="""
        Event fired just after a scan/raster across this axis collection is completed.
    """)
    on_scan_step = event_property('_on_scan_step', doc="""
        Event fired just after a step in a scan/raster is taken.
        (If applicable - won't be possible whenever is_hardware_scannable 
        is True, for example.)
    """)
    
    @abc.abstractproperty
    def finest_axes(self):
        """
        The subset of axes that are finest with respect to rastering/
        scanning. If this collection is the finest, then this is just `self`.
        """
        pass
    
    @abc.abstractproperty
    def is_hardware_scannable(self): 
        """
        Tuple specifying which of the constituent axes can perform a sequence 
        of movements in hardware without software intervention.
        """        
        pass
    
    @abc.abstractproperty
    def limits(self): 
        """
        Tuple of range limits for each constituent axis. Each range limit 
        should be of the form (min_pos, max_pos).
        """        
        pass
    
    @abc.abstractproperty
    def position(self): 
        """
        The current position of each constituent axis.
        """        
        pass

    @property
    def move_history(self):
        """
        A list of the latest coordinates coordinates issued to the 
        `move` command. The most recent is the 0th element of the list.
        """
        return self._move_history

    # should return a quantities.quantity.Quantity
    @abc.abstractproperty
    def units(self): 
        """
        A tuple of the native units of each constituent axis.
        """        
        pass

    ## PRIVATE METHODS ##
    
    def _within_limits(self, coord):
        each_axis_within = [lim[0] <= c and c <= lim[1] for c, lim in izip(coord, self.limits)]
        return all(each_axis_within)

    ## METHODS ##
    
    # We abstract the underscore versions of the following functions to 
    # force certain actions like logging movement history, and enforcing
    # software limits.
    
    @abc.abstractmethod
    def _move(self, position, absolute=True): pass
    @update_history
    def move(self, position, absolute=True):
        """
        Moves the axis to the given position.
        
        :param position: An iterable specifying the position of each axis to 
            move to. Position can be unitful,
        :param bool absolute: Absolute movement if True, relative movement 
            if false.
        """
        if not self._within_limits(position):
            raise ValueError('Position {} not within software limits {}.'.format(position, self.limits))
        self._move(position, absolute=absolute)
    
    @abc.abstractmethod
    def _scan(self, coords, dwell_time=None): pass
    def scan(self, coords, dwell_time=None):
        """
        Scans the axes through a parametric path.
        
        :param coords: An iterable (whose length is equal to the number of 
            axes) where each element is an iterable specifying the path of 
            the respective axis.
        :param dwell_time: The amount of time to wait between each point in 
            the scan. Can be set to None to wait for no time.
        """
        for coord in coords:
            if not self._within_limits(coord):
                raise ValueError('Scan coordinate {} not within software limits {}.'.format(coord, self.limits))
        self._scan(coords, dwell_time=dwell_time)
        
    @abc.abstractmethod
    def _raster(self, start, stop, num, dwell_time=None, strict=True): pass
    def raster(self, start, stop, num, dwell_time=None, strict=True):
        """
        Makes the axes trace a path that fills a (hyper)-rectangle of
        the axes parameter space. Whether this path is constructed snake-style 
        or typerwriter-style or else is decided by the particular 
        implementation of axes in question.
        
        :param start: An iterable specifying the start position of each axis.
        :param stop: An iterable specifying the stop position of each axis.
        :param num: An iterable specifying how many steps to take to get from
            start to stop for each axis.
        :param dwell_time: The amount of time to wait between each point in 
            the scan. Can be set to None to wait for no time.
        :param bool strict: Whether or not the rastering pattern should be 
            strict about following the start, stop, num parameters to the 
            letter. (In some cases, like with parallel axes, when strict=False,
            the raster algorithm can optimize the parameters a bit to 
            fill space without overlapping.)
        """
        if not self._within_limits(start):
            raise ValueError('Start coordinate {} not within software limits {}.'.format(start, self.limits))
        if not self._within_limits(stop):
            raise ValueError('Stop coordinate {} not within software limits {}.'.format(stop, self.limits))
        self._raster(start, stop, num, dwell_time=dwell_time, strict=strict)
    
    # Require implementors to say how long they are (that is, how many axes).
    @abc.abstractmethod
    def __len__(self):
        pass