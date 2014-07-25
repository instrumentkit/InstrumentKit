#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# tektds224.py: Driver for the Tektronix TDS 224 oscilloscope.
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

import time
import numpy as np
import quantities as pq
from flufl.enum import Enum
from flufl.enum._enum import EnumValue

from instruments.abstract_instruments import (
    OscilloscopeChannel,
    OscilloscopeDataSource,
    Oscilloscope,
)
from instruments.generic_scpi import SCPIInstrument
from instruments.util_fns import assume_units, ProxyList

## CLASSES #####################################################################

class _TekTDS224DataSource(OscilloscopeDataSource):
    '''
    Class representing a data source (channel, math, or ref) on the Tektronix 
    TDS 224.
    
    .. warning:: This class should NOT be manually created by the user. It is 
        designed to be initialized by the `TekTDS224` class.
    '''
    
    def __init__(self, tek, name):
        self._tek = tek
        self._name = name
        self._old_dsrc = None
        
    @property
    def name(self):
        '''
        Gets the name of this data source, as identified over SCPI.
        
        :type: `str`
        '''
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
    
    def read_waveform(self, bin_format=True):
        '''
        Read waveform from the oscilloscope.
        This function is all inclusive. After reading the data from the 
        oscilloscope, it unpacks the data and scales it accordingly.
        
        Supports both ASCII and binary waveform transfer. For 2500 data 
        points, with a width of 2 bytes, transfer takes approx 2 seconds for 
        binary, and 7 seconds for ASCII over Galvant Industries' GPIBUSB 
        adapter.
        
        Function returns a tuple (x,y), where both x and y are numpy arrays.
        
        :param bool bin_format: If `True`, data is transfered
            in a binary format. Otherwise, data is transferred in ASCII.
        
        :rtype: two item `tuple` of `numpy.ndarray`
        '''
        with self:
            
            if not bin_format:
                self._tek.sendcmd('DAT:ENC ASCI') # Set the data encoding format to ASCII
                raw = self._tek.query('CURVE?')
                raw = raw.split(',') # Break up comma delimited string
                raw = map(float, raw) # Convert each list element to int
                raw = np.array(raw) # Convert into numpy array
            else:
                self._tek.sendcmd('DAT:ENC RIB') # Set encoding to signed, big-endian
                data_width = self._tek.data_width
                self._tek.sendcmd('CURVE?')
                raw = self._tek.binblockread(data_width) # Read in the binary block, 
                                                    # data width of 2 bytes

                self._tek._file.flush_input() # Flush input buffer
            
            yoffs = self._tek.query('WFMP:{}:YOF?'.format(self.name)) # Retrieve Y offset
            ymult = self._tek.query('WFMP:{}:YMU?'.format(self.name)) # Retrieve Y multiply
            yzero = self._tek.query('WFMP:{}:YZE?'.format(self.name)) # Retrieve Y zero
            
            y = ((raw - float(yoffs)) * float(ymult)) + float(yzero)
            
            xzero = self._tek.query('WFMP:XZE?') # Retrieve X zero
            xincr = self._tek.query('WFMP:XIN?') # Retrieve X incr
            ptcnt = self._tek.query('WFMP:{}:NR_P?'.format(self.name)) # Retrieve number 
                                                                  # of data points
            
            x = np.arange(float(ptcnt)) * float(xincr) + float(xzero)
            
            return (x,y)
            
class _TekTDS224Channel(_TekTDS224DataSource, OscilloscopeChannel):
    '''
    Class representing a channel on the Tektronix TDS 224.
    
    This class inherits from `_TekTDS224DataSource`.
    
    .. warning:: This class should NOT be manually created by the user. It is 
        designed to be initialized by the `TekTDS224` class.
    '''
    
    def __init__(self, parent, idx):
        super(_TekTDS224Channel, self).__init__(parent, "CH{}".format(idx + 1))
        self._idx = idx + 1

    @property
    def coupling(self):
        """
        Gets/sets the coupling setting for this channel.

        :type: `TekTDS224.Coupling`
        """
        return TekTDS224.Coupling[self._tek.query("CH{}:COUPL?".format(
                                                                self._idx)
                                                                )]
    @coupling.setter
    def coupling(self, newval):
        if (not isinstance(newval, EnumValue)) or (newval.enum is not 
                                                           TekTDS224.Coupling):
            raise TypeError("Coupling setting must be a `TekTDS224.Coupling`"
                " value, got {} instead.".format(type(newval)))

        self._tek.sendcmd("CH{}:COUPL {}".format(self._idx, newval.value))
        
class TekTDS224(SCPIInstrument, Oscilloscope):

    ## ENUMS ##
    
    class Coupling(Enum):
        ac = "AC"
        dc = "DC"
        ground = "GND"
        
    ## PROPERTIES ##
      
    @property
    def channel(self):
        '''
        Gets a specific oscilloscope channel object. The desired channel is 
        specified like one would access a list.
        
        For instance, this would transfer the waveform from the first channel::
        
        >>> tek = ik.tektronix.TekTDS224.open_tcpip('192.168.0.2', 8888)
        >>> [x, y] = tek.channel[0].read_waveform()
        
        :rtype: `_TekTDS224Channel`
        '''
        return ProxyList(self, _TekTDS224Channel, xrange(4))
        
    @property
    def ref(self):
        '''
        Gets a specific oscilloscope reference channel object. The desired 
        channel is specified like one would access a list.
        
        For instance, this would transfer the waveform from the first channel::
        
        >>> tek = ik.tektronix.TekTDS224.open_tcpip('192.168.0.2', 8888)
        >>> [x, y] = tek.ref[0].read_waveform()
        
        :rtype: `_TekTDS224DataSource`
        '''
        return ProxyList(self,
            lambda s, idx: _TekTDS224DataSource(s, "REF{}".format(idx  + 1)),
            xrange(4))
        
    @property
    def math(self):
        '''
        Gets a data source object corresponding to the MATH channel.
        
        :rtype: `_TekTDS224DataSource`
        '''
        return _TekTDS224DataSource(self, "MATH")
        
    @property
    def data_source(self):
        '''
        Gets/sets the the data source for waveform transfer.
        '''
        name = self.query("DAT:SOU?")
        if name.startswith("CH"):
            return _TekTDS224Channel(self, int(name[2:]) - 1)
        else:
            return _TekTDS224DataSource(self, name)
    @data_source.setter
    def data_source(self, newval):
        # TODO: clean up type-checking here.
        if not isinstance(newval, str):
            if hasattr(newval, "value"): # Is an enum with a value.
                newval = newval.value
            elif hasattr(newval, "name"): # Is a datasource with a name.
                newval = newval.name
        self.sendcmd("DAT:SOU {}".format(newval))
        time.sleep(0.01) # Let the instrument catch up.
        
    @property
    def data_width(self):
        return int(self.query("DATA:WIDTH?"))
    @data_width.setter
    def data_width(self, newval):
        if int(newval) not in [1, 2]:
            raise ValueError("Only one or two byte-width is supported.")
        
        self.sendcmd("DATA:WIDTH {}".format(newval))

    @property
    def force_trigger(self):
        raise NotImplementedError
    
        
