#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# tektds5xx.py: Driver for the Tektronix TDS 5xx series oscilloscope.
##
# © 2014 Chris Schimp (silverchris@gmail.com)
#
# Modified from tektds224.py
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

from time import sleep
import operator
import struct

from instruments.abstract_instruments import (
    OscilloscopeChannel,
    OscilloscopeDataSource,
    Oscilloscope,
)
from instruments.generic_scpi import SCPIInstrument
from instruments.util_fns import assume_units, ProxyList

## CLASSES #####################################################################

class _TekTDS5XXMeasurement(object):
    '''
    Class representing a measurement channel on the Tektronix TDS5xx
    '''
    
    def __init__(self, tek, idx):
        self._tek = tek
        self._id = idx+1
        resp = self._tek.query('MEASU:MEAS{}?'.format(self._id))
        self._data = dict(zip(['enabled', 'type', 'units', 'src1', 'src2',
                              'edge1','edge2', 'dir'], resp.split(';')))
    
    def read(self):
        '''
        Gets the current measurement value of the channel, and returns a dict
        of all relevent informatio
		:rtype: `dict` of measurement parameters
        '''
        if int(self.data['enabled']):
            resp = self._tek.query('MEASU:MEAS{}:VAL?'.format(self._id))
            self._data['value'] = float(resp)
            return self._data
        else:
            return self._data
    
    def set(self):
        raise NotImplementedError
    

class _TekTDS5XXDataSource(OscilloscopeDataSource):
    '''
    Class representing a data source (channel, math, or ref) on the Tektronix 
    TDS 5XX.
    
    .. warning:: This class should NOT be manually created by the user. It is 
        designed to be initialized by the `TekTDS5XX` class.
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
            
            xincr = self._tek.query('WFMP:{}:XIN?'.format(self.name)) # Retrieve X incr
            ptcnt = self._tek.query('WFMP:{}:NR_P?'.format(self.name)) # Retrieve number 
                                                                  # of data points
            x = np.arange(float(ptcnt)) * float(xincr)
            
            
            return (x, y)
            
class _TekTDS5XXChannel(_TekTDS5XXDataSource, OscilloscopeChannel):
    '''
    Class representing a channel on the Tektronix TDS 5XX.
    
    This class inherits from `_TekTDS5XXDataSource`.
    
    .. warning:: This class should NOT be manually created by the user. It is 
        designed to be initialized by the `TekTDS5XX` class.
    '''
    
    def __init__(self, parent, idx):
        super(_TekTDS5XXChannel, self).__init__(parent, "CH{}".format(idx + 1))
        self._idx = idx + 1

    @property
    def coupling(self):
        """
        Gets/sets the coupling setting for this channel.

        :type: `TekTDS5XX.Coupling`
        """
        return TekTDS5XX.Coupling[self._tek.query("CH{}:COUPL?".format(
                                                                self._idx)
                                                                )]
    @coupling.setter
    def coupling(self, newval):
        if (not isinstance(newval, EnumValue)) or (newval.enum is not 
                                                           TekTDS5XX.Coupling):
            raise TypeError("Coupling setting must be a `TekTDS5XX.Coupling`"
                " value, got {} instead.".format(type(newval)))

        self._tek.sendcmd("CH{}:COUPL {}".format(self._idx, newval.value))
        
    @property
    def bandwidth(self):
        """
        Gets/sets the Bandwidth setting for this channel.

        :type: `TekTDS5XX.Bandwidth`
        """
        return TekTDS5XX.Bandwidth[self._tek.query("CH{}:BAND?".format(
                                                                self._idx)
                                                                )]
    @bandwidth.setter
    def bandwidth(self, newval):
        if (not isinstance(newval, EnumValue)) or (newval.enum is not 
                                                           TekTDS5XX.Bandwidth):
            raise TypeError("Bandwidth setting must be a `TekTDS5XX.Bandwidth`"
                " value, got {} instead.".format(type(newval)))

        self._tek.sendcmd("CH{}:BAND {}".format(self._idx, newval.value))
        
    @property
    def impedance(self):
        """
        Gets/sets the impedance setting for this channel.

        :type: `TekTDS5XX.Impedance`
        """
        return TekTDS5XX.Impedance[self._tek.query("CH{}:IMP?".format(
                                                                self._idx)
                                                                )]
    @impedance.setter
    def impedance(self, newval):
        if (not isinstance(newval, EnumValue)) or (newval.enum is not 
                                                           TekTDS5XX.Impedance):
            raise TypeError("Impedance setting must be a `TekTDS5XX.Impedance`"
                " value, got {} instead.".format(type(newval)))

        self._tek.sendcmd("CH{}:IMP {}".format(self._idx, newval.value))
        
    @property
    def probe(self):
        """
        Gets the connected probe value for this channel

        :type: `float`
        """
        return round(1/float(self._tek.query("CH{}:PRO?".format(self._idx))), 0)
    
    @property
    def scale(self):
        """
        Gets/sets the scale setting for this channel.

        :type: `TekTDS5XX.Impedance`
        """
        print(self._tek.query("CH{}:SCA?".format(self._idx)))
        return float(self._tek.query("CH{}:SCA?".format(self._idx)))
    
    @scale.setter
    def scale(self, newval):
        self._tek.sendcmd("CH{0}:SCA {1:.3E}".format(self._idx, newval))
        resp = float(self._tek.query("CH{}:SCA?".format(self._idx)))
        if newval != resp:
            raise ValueError("Tried to set CH{0} Scale to {1} but got {2}"
                " instead".format(self._idx, newval, resp))
        
        
class TekTDS5XX(SCPIInstrument, Oscilloscope):

    ## ENUMS ##
    
    class Coupling(Enum):
        ac = "AC"
        dc = "DC"
        ground = "GND"
        
    class Bandwidth(Enum):
        Twenty = "TWE"
        OneHundred = "HUN"
        TwoHundred = "TWO"
        FULL = "FUL"
    
    class Impedance(Enum):
        Fifty = "FIF"
        OneM = "MEG"
        
    class Edge(Enum):
        Rising = 'RIS'
        Falling = 'FALL'
        
    class Trigger(Enum):
        CH1 = 'CH1'
        CH2 = 'CH2'
        CH3 = 'CH3'
        CH4 = 'CH4'
        AUX = 'AUX'
        LINE = 'LINE'
    
    ## PROPERTIES ##
    @property
    def measurement(self):
        '''
        Gets a specific oscilloscope measurement object. The desired channel is
        specified like one would access a list.
        '''
        return ProxyList(self, _TekTDS5XXMeasurement, xrange(3))
    
    
    @property
    def channel(self):
        '''
        Gets a specific oscilloscope channel object. The desired channel is 
        specified like one would access a list.
        
        For instance, this would transfer the waveform from the first channel::
        
        >>> tek = ik.tektronix.TekTDS5XX.open_tcpip('192.168.0.2', 8888)
        >>> [x, y] = tek.channel[0].read_waveform()
        
        :rtype: `_TekTDS5XXChannel`
        '''
        return ProxyList(self, _TekTDS5XXChannel, xrange(4))
        
    @property
    def ref(self):
        '''
        Gets a specific oscilloscope reference channel object. The desired 
        channel is specified like one would access a list.
        
        For instance, this would transfer the waveform from the first channel::
        
        >>> tek = ik.tektronix.TekTDS5XX.open_tcpip('192.168.0.2', 8888)
        >>> [x, y] = tek.ref[0].read_waveform()
        
        :rtype: `_TekTDS5XXDataSource`
        '''
        return ProxyList(self,
            lambda s, idx: _TekTDS5XXDataSource(s, "REF{}".format(idx  + 1)),
            xrange(4))
        
    @property
    def math(self):
        '''
        Gets a data source object corresponding to the MATH channel.
        
        :rtype: `_TekTDS5XXDataSource`
        '''
        return ProxyList(self,
            lambda s, idx: _TekTDS5XXDataSource(s, "MATH{}".format(idx  + 1)),
            xrange(3))
    @property
    def sources(self):
        '''
        Returns list of all active sources
        '''
        active = []
        channels = map(int, self.query('SEL?').split(';')[0:11])
        for idx in range(0, 4):
            if channels[idx]:
                active.append(_TekTDS5XXChannel(self, idx))
        for idx in range(4, 7):
            if channels[idx]:
                active.append(_TekTDS5XXDataSource(self, "MATH{}".format(
                                                                        idx-3)))
        for idx in range(7, 11):
            if channels[idx]:
                active.append(_TekTDS5XXDataSource(self, "REF{}".format(idx-6)))
        return active
		
    @property
    def data_source(self):
        '''
        Gets/sets the the data source for waveform transfer.
        '''
        name = self.query("DAT:SOU?")
        if name.startswith("CH"):
            return _TekTDS5XXChannel(self, int(name[2:]) - 1)
        else:
            return _TekTDS5XXDataSource(self, name)
        
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
    
    @property
    def horizontal_scale(self):
        '''
        Get/Set Horizontal Scale
        '''
        return float(self.query('HOR:MAI:SCA?'))
    
    @horizontal_scale.setter
    def horizontal_scale(self, newval):
        self.sendcmd("HOR:MAI:SCA {0:.3E}".format(newval))
        resp = float(self.query('HOR:MAI:SCA?'))
        if newval != resp:
            raise ValueError("Tried to set Horizontal Scale to {} but got {}"
                " instead".format(newval, resp))
    @property
    def trigger_level(self):
        '''
        Get/Set trigger level
		:type: `float`
        '''
        return float(self.query('TRIG:MAI:LEV?'))
    
    @trigger_level.setter
    def trigger_level(self, newval):
        self.sendcmd("TRIG:MAI:LEV {0:.3E}".format(newval))
        resp = float(self.query('TRIG:MAI:LEV?'))
        if newval != resp:
            raise ValueError("Tried to set trigger level to {} but got {}"
                " instead".format(newval, resp))
        
    @property
    def trigger_coupling(self):
        '''
        Get/Set trigger coupling
		:type: `TekTDS5XX.Coupling`
        '''
        return TekTDS5XX.Coupling[self.query("TRIG:MAI:EDGE:COUP?")]
    
    @trigger_coupling.setter
    def trigger_coupling(self, newval):
        if (not isinstance(newval, EnumValue)) or (newval.enum is not 
                                                   TekTDS5XX.Coupling):
            raise TypeError("Coupling setting must be a `TekTDS5XX.Coupling`"
                " value, got {} instead.".format(type(newval)))

        self.sendcmd("TRIG:MAI:EDGE:COUP {}".format(newval.value))
    
    @property
    def trigger_slope(self):
        '''
        Get/Set trigger slope
		:type: `TekTDS5XX.Edge`
        '''
        return TekTDS5XX.Edge[self.query("TRIG:MAI:EDGE:SLO?")]
    
    @trigger_slope.setter
    def trigger_slope(self, newval):
        if (not isinstance(newval, EnumValue)) or (newval.enum is not 
                                                   TekTDS5XX.Edge):
            raise TypeError("Edge setting must be a `TekTDS5XX.Edge`"
                " value, got {} instead.".format(type(newval)))

        self.sendcmd("TRIG:MAI:EDGE:SLO {}".format(newval.value))
    
    @property
    def trigger_source(self):
        '''
        Get/Set trigger source
		:type: `TekTDS5XX.Trigger`
        '''
        return TekTDS5XX.Trigger[self.query("TRIG:MAI:EDGE:SOU?")]
    
    @trigger_source.setter
    def trigger_source(self, newval):
        if (not isinstance(newval, EnumValue)) or (newval.enum is not 
                                                   TekTDS5XX.Trigger):
            raise TypeError("Trigger source setting must be a `TekTDS5XX.source`"
                " value, got {} instead.".format(type(newval)))

        self.sendcmd("TRIG:MAI:EDGE:SOU {}".format(newval.value))
    
    def get_hardcopy(self):
        '''
        Gets a screenshot of the display
		:rtype: `string`
        '''
        self.sendcmd('HARDC:PORT GPI;HARDC:LAY PORT;:HARDC:FORM BMP')
        self.sendcmd('HARDC START')
        sleep(1)
        header = self.query(msg="", size=54)
        print(header)
        print(len(header))
        #Get BMP Length  in kilobytes from DIB header, because file header is bad
        length = reduce(operator.mul, struct.unpack('<iihh', header[18:30]))/8
        length = int(length)+8#Add 8 bytes for our monochrome colour table
        print(length)
        data = header+self.query(msg="", size=length)
        #print(len(self._file.read(10)))
        return data
        
