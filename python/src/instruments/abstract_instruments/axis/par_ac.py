#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# par_ac.py: AxisCollection (AC) that contains a list of parallel ACs
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

import time
import quantities as pq
import numpy as np
from itertools import izip
from math import ceil
from axis_collection import AxisCollection
from instruments.util_fns import assume_units, compatible_units

## CLASSES #####################################################################

class ParallelAC(AxisCollection):
    """
    Joins two sets of `AxisCollection` into a parallel axes system. In a 
    raster, the fine axis scans rapidly. Both sets of axes should be the same
    length. They are parallel in the sense that the first coarse axis is
    parallel to the first fine axis, the second to the second, and so on.
    As such, the units should be compatible from the first to  the first, etc.
    
    Note that this class could in principle be implemented so that 
    it exposes a single virtual axis collection, where the fact that there is
    a fine and coarse axis is completely hidden from the user -- that is
    to say, for example, if the coarse had XY and the fine had XY, then this
    class would expose a single XY system with only two coordinates. This 
    would be interesting and somewhat useful, but the huge problem would be
    losing credibility in bidirectional repeatability.
    As such this class exposes all coarse and fine axes separately, and is 
    only parallel in the sense that rastering is partially automated in a
    parallel sense.
    
    Note that `scan` cannot in general be implemented more cleverly then just 
    calling a whole bunch of `move` commands, whereas `raster` can be 
    implemented with calls to `raster` on the fine axis and `move` on the 
    coarse axis.    
    
    In all methods and properties, this combined axis system places the course 
    axes first, and the fine axes second.
    
    :param AxisCollection coarse_axes: The coarse axis collection. Should have
        the same number of axes as `fine_axes`.
    :param AxisCollection fine_axes: The fine axis collection. Should have 
        the same number of axes as `coarse_axes`.
    """

    def __init__(self, coarse_axes, fine_axes):
        
        super(ParallelAC, self).__init__()
        
        if len(coarse_axes) != len(fine_axes):
            raise ValueError('Course axis count, {}, must match fine axis count, {}.'.formate(len(coarse_axes), len(fine_axes)))
            
        for fine_unit, coarse_unit in izip(coarse_axes.units, fine_axes.units):
            if not compatible_units(fine_unit, coarse_unit):
                ValueError('Units {} and {} must match.'.format(fine_unit, coarse_unit))
        
        self._coarse_axes = coarse_axes
        self._fine_axes = fine_axes
        
        self._n_axes = len(coarse_axes)
        
    ## PROPERTIES ##
    
    @property
    def is_hardware_scannable(self):
        return self._coarse_axes.is_hardware_scannable + self._fine_axes.is_hardware_scannable
            
    @property
    def limits(self):
        return self._coarse_axes.limits + self._fine_axes.limits
        
    @property
    def position(self):
        return self._coarse_axes.position + self._fine_axes.position
        
    @property
    def units(self):
        return self._coarse_axes.units + self._fine_axes.units
            
    ## METHODS ##
    
    def _move(self, position, absolute=True):
        # separate the positions into the major and minor positions
        coarse_pos = position[:self._n_axes]
        fine_pos = position[self._n_axes:]
        self._coarse_axes.move(coarse_pos, absolute=absolute)
        self._fine_axes.move(fine_pos, absolute=absolute)
    
    def _scan(self, coords, dwell_time=None):
        # Unfortuneately, can't do this more efficiently in general
        for coord in izip(*coords):
            # Call _move so we don't bloat the move history
            self._move(coord)
            if dwell_time is not None:
                time.sleep(assume_units(dwell_time, pq.s).rescale(pq.s).magnitude)
    
    def _raster(self, start, stop, num, dwell_time=None, strict=True):
        
        # Separate the major from the minor arguments...
        coarse_start = start[:self._n_axes]
        coarse_stop = stop[:self._n_axes]
        coarse_num = num[:self._n_axes]
        
        fine_start = start[self._n_axes:]
        fine_stop = stop[self._n_axes:]
        fine_num = num[self._n_axes:]
        
        # At this point we decide whether or not to try and optimize the 
        # raster to make the fine and coarse axes fill space but not overlap
        # any region.
        
        if not strict:
            
            # Calculate total raster range of fine and coarse axes
            fine_size = [abs(f_stop - f_start) for f_start, f_stop in izip(fine_start, fine_stop)]
            coarse_size = [abs(c_stop - c_start) for c_start, c_stop in izip(coarse_start, coarse_stop)]
            
            # We of course don't have to scan from small to big, so we will need directions
            coarse_sign = [1 if c_stop > c_start else -1 for c_start, c_stop in izip(coarse_start, coarse_stop)]
            
            # We aim to make the coarse step the same as fine size
            coarse_step = fine_size
            
            # Resize the coarse number to find out how many steps we need 
            # to cover the specified coarse region given the fine volume
            coarse_num = [int(ceil((c_size / f_size).rescale(pq.dimensionless).magnitude[()])) + 1
                            for c_size, f_size in izip(coarse_size, fine_size)]
            
            # We purposely enlarged the coarse area above, so calculate how much
            # bigger we are              
            coarse_extra = [(c_num - 1) * c_step - c_size for c_size, c_num, c_step in izip(coarse_size, coarse_num, coarse_step)]
            
            # Now modify start and stop with this extra bit. At this point,
            # the coarse steps should be exactly the same size as the fine size
            coarse_start = [c_start - c_sign * c_extra/2 for c_start, c_extra, c_sign in izip(coarse_start, coarse_extra, coarse_sign)]
            coarse_stop = [c_stop + c_sign * c_extra/2 for c_stop, c_extra, c_sign in izip(coarse_stop, coarse_extra, coarse_sign)]
            
            # Annoying bit where we might have gone out of coarse limits...
            within = [False] * self._n_axes
            while not all(within):
                for idx in xrange(self._n_axes):
                    min_val = min(coarse_start[idx], coarse_stop[idx])
                    max_val = max(coarse_start[idx], coarse_stop[idx])
                    if min_val < self._coarse_axes.limits[idx][0]:
                        # reduce step by one and increase min_val by one step
                        coarse_num[idx] -= 1
                        coarse_start[idx] += (1 + coarse_sign[idx]) * coarse_step[idx]/2
                        coarse_stop[idx] += (1 - coarse_sign[idx]) * coarse_step[idx]/2
                    elif max_val > self._coarse_axes.limits[idx][1]:
                        # reduce step by one and decrease max_val by one step
                        coarse_num[idx] -= 1
                        coarse_start[idx] -= (1 - coarse_sign[idx]) * coarse_step[idx]/2
                        coarse_stop[idx] -= (1 + coarse_sign[idx]) * coarse_step[idx]/2
                    else:
                        # otherwise this axis is good
                        within[idx] = True
   
        # Start by discretizing along each major axis.
        coarse_axis_steps = [
            np.linspace(
                assume_units(m_start, unit),
                assume_units(m_stop, unit),
                num = m_num
            )
            for m_start, m_stop, m_num, unit in izip(coarse_start, coarse_stop, coarse_num, self._coarse_axes.units)
        ]

        # Now call meshgrid and flatten to make a list of coordinates
        # This will make a typewriter-like raster
        coarse_axes_grid = np.array(np.meshgrid(*coarse_axis_steps)).transpose()
        coarse_axes_grid = coarse_axes_grid.reshape((np.prod(coarse_num), self._n_axes))
        
        # Loop through the major axis coordinates and raster the minor axis.
        for coord in coarse_axes_grid:
            self._major_axis.move(coord)
            self._minor_axis.raster(fine_start, fine_stop, fine_num, dwell_time=dwell_time)
        
        
    def __repr__(self):
        return 'Parallel({}, {})'.format(self._coarse_axes.__repr__(), self._fine_axes.__repr__())
        
    def __len__(self):
        return 2 * self._n_axes
