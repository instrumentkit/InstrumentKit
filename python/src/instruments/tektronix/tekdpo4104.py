#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# tekdpo4104.py: Driver for the Tektronix DPO 4104 oscilloscope.
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

## FEATURES ####################################################################

from __future__ import division

## IMPORTS #####################################################################

from time import time, sleep

from flufl.enum import Enum
from flufl.enum._enum import EnumValue

from contextlib import contextmanager

import quantities as pq

from instruments.generic_scpi import SCPIInstrument
from instruments.util_fns import assume_units

import struct
import numpy as np

## FUNCTIONS ###################################################################

def _parent_property(prop_name, doc=""):
    
    def getter(self):
        with self:
            return getattr(self._tek, propname)
    
    def setter(self, newval):
        with self:
            setattr(self._tek, prop_name, doc)
            
    return property(getter, setter, doc=doc)

## ENUMS #######################################################################

class TekDPO4104Coupling(Enum):
    ac = "AC"
    dc = "DC"
    ground = "GND"

## CLASSES #####################################################################

class TekDPO4104DataSource(object):
    def __init__(self, tek, name):
        self._tek = tek
        # Zero-based for pythonic convienence, so we need to convert to
        # Tektronix's one-based notation here.
        self._name = name
        
        # Remember what the old data source was for use as a context manager.
        self._old_dsrc = None
        
    @property
    def name(self):
        """
        Gets the name of this data source, as identified over SCPI.
        
        :type: `str`
        """
        return self._name

    def __enter__(self):
        self._old_dsrc = self._tek.data_source
        if self._old_dsrc != self:
            # Set the new data source, and let __exit__ cleanup.
            self._tek.data_source = self
        else:
            # There's nothing to do or undo in this case.
            self._old_dsrc = None
        
    
    def __exit__(self, type, value, traceback):
        if self._old_dsrc is not None:
            self._tek.data_source = self._old_dsrc
        
    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        else:
            return other.name == self.name
        
    # Read Waveform        
    def read_waveform(self, bin_format=False):
        '''
        Read waveform from the oscilloscope.
        This function is all inclusive. After reading the data from the oscilloscope, it unpacks the data and scales it accordingly.
        Supports both ASCII and binary waveform transfer. For 2500 data points, with a width of 2 bytes, transfer takes approx 2 seconds for binary, and 7 seconds for ASCII.
        
        Function returns a list [x,y], where both x and y are numpy arrays.

        :param bool bin_format: If `True`, data is transfered
            in a binary format. Otherwise, data is transferred in ASCII.
        '''

        # Set the acquisition channel
        with self:
            if not bin_format:
                self._tek.sendcmd( 'DAT:ENC ASCI' ) # Set the data encoding format to ASCII
                raw = self._tek.query( 'CURVE?' )
                raw = raw.split(",") # Break up comma delimited string
                raw = map(float, raw) # Convert each list element to int
                raw = np.array(raw) # Convert into numpy array
            else:
                self._tek.sendcmd( 'DAT:ENC RIB' ) # Set encoding to signed, big-endian
                self._tek.sendcmd( 'CURVE?' )
                raw = self._tek.binblockread(2) # Read in the binary block, data width of 2 bytes

                self._tek._file.read(2) # Read in the two ending \n\r characters

            # FIXME: the following has not yet been converted.
            #        Needs to be fixed before it will even run.
            yoffs = self._tek.y_offset # Retrieve Y offset
            ymult = self._tek.query( 'WFMP:YMU?' ) # Retrieve Y multiplier
            yzero = self._tek.query( 'WFMP:YZE?' ) # Retrieve Y zero
            
            y = ( (raw - yoffs ) * float(ymult) ) + float(yzero)
            
            xzero = self._tek.query( 'WFMP:XZE?' ) # Retrieve X zero
            xincr = self._tek.query( 'WFMP:XIN?' ) # Retrieve X incr
            ptcnt = self._tek.query( 'WFMP:NR_P?') # Retrieve number of data points
            
            x = np.arange( float(ptcnt) ) * float(xincr) + float(xzero)
            
            return [x,y]
            
    y_offset = _parent_property('y_offset')
    

class TekDPO4104Channel(TekDPO4104DataSource):
    
    def __init__(self, parent, idx):
        super(TekDPO4104Channel, self).__init__(self, parent, "CH{}".format(idx))
        self._idx = idx + 1
    
    @property
    def coupling(self):
        """
        Gets/sets the coupling setting for this channel.

        :type: `TekDPO4104Coupling`
        """
        return TekDPO4104Coupling[self._tek.query("CH{}:COUPL?".format(self._idx))]
    @coupling.setter
    def coupling(self, newval):
        if not isinstance(newval, EnumValue) or newval.enum is not TekDPO4104Coupling:
            raise TypeError("Coupling setting must be a TekDPO4104Coupling value, got {} instead.".format(type(newval)))

        self._tek.sendcmd("CH{}:COUPL {}".format(self._idx, newval.value))

class TekDPO4104(SCPIInstrument):

    @property
    def channel(self):
        return ProxyList(self, TekDPO4104Channel, xrange(4))
        
    @property
    def data_source(self):
        name = self.query("DAT:SOU?")
        if name.startswith("CH"):
            return TekDPO4104Channel(int(name[2:] - 1))
        else:
            return TekDPO4104DataSource(name)
            
    @data_source.setter
    def data_source(self, newval):
        # TODO: clean up type-checking here.
        if not isinstance(newval, str):
            if hasattr(newval, "value"): # Is an enum with a value.
                newval = newval.value
            elif hasattr(newval, "name"): # Is a datasource with a name.
                newval = newval.name
        self.sendcmd("DAT:SOU {}".format(newval))
    
    # TODO: convert to read in unitful quantities.
    @property
    def y_offset(self):
        """
        Gets/sets the Y offset of the currently selected data source.
        """
        yoffs = float(self._tek.query( 'WFMP:YOF?' ))
    @y_offset.setter
    def y_offset(self, newval):
        self._tek.sendcmd("WFMP:YOF {}".format(newval))
    
