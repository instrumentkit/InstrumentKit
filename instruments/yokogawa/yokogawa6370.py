#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides support for the Yokogawa 6370 optical spectrum analyzer.
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division

from enum import IntEnum,Enum

import quantities as pq

from instruments.abstract_instruments import (
    OpticalSpectrumAnalyzer,
    OSAChannel,
)
from instruments.abstract_instruments import Instrument
from instruments.util_fns import (
    enum_property, string_property, int_property, unitful_property,
    unitless_property, bounded_unitful_property, ProxyList, assume_units
)

# CLASSES #####################################################################


# import instruments as ik
# import quantities as pq
# 
# 
# 
# 
# inst = ik.yokogawa.Yokogawa6370.open_tcpip('192.168.0.35',10001)
# inst.start_wl = 1030e-9 * pq.m
# inst.sendcmd(':FORMat:DATA REAL,64')
# a = inst.channel[1].data()

class Yokogawa6370(OpticalSpectrumAnalyzer, Instrument):

    """
    The Yokogawa 6370 is a optical spectrum analyzer.

    Example usage:

    >>> import instruments as ik
    >>> import quantities as pq
    >>> inst = ik.yokogawa.Yokogawa6370.open_visa('TCPIP0:192.168.0.35')
    >>> inst.start_wl = 1030e-9 * pq.m
    """



 ####       def __init__(self):
    #     # super(Yokogawa6370, self).__init__()
    #     # Set data Format to binary
    #     self.sendcmd(':FORMat:DATA REAL,64')
        
    # INNER CLASSES #

    class Channel(OSAChannel):

        """
        Class representing the channels on the Yokogawa 6370.

        This class inherits from `OSAChannel`.

        .. warning:: This class should NOT be manually created by the user. It
            is designed to be initialized by the `Yokogawa6370` class.
        """
        _trace_names = ['TRA','TRB','TRC','TRD','TRE','TRF','TRG']
        
        def __init__(self, parent, idx):
            self._parent = parent
            self._name = self._trace_names[idx]

        # METHODS #
        
        def data(self, bin_format=True):
            cmd = ':TRAC:Y? '+self._name  
            self._parent.sendcmd(cmd)
            data = self._parent.binblockread(data_width = 4,fmt = '<d')
            self._parent._file.read_raw(1)
            return data
            
        def wavelength(self, bin_format=True):
            cmd = ':TRAC:X? '+self._name  
            self._parent.sendcmd(cmd)
            data = self._parent.binblockread(data_width = 4,fmt = '<d')
            self._parent._file.read_raw(1)
            return data

    

    # ENUMS #

    class SweepModes(IntEnum):
        """
        Enum containing valid output modes for the Yokogawa 7651
        """
        AUTO   = 3
        SINGLE = 1
        REPEAT = 2
        
    class Traces(Enum):
        """
        Enum containing valid Traces for the Yokogawa 7651
        """
        A = 'TRA'
        B = 'TRB'
        C = 'TRC'
        D = 'TRD'
        E = 'TRE'
        F = 'TRF'
        G = 'TRG'
        
        
    # PROPERTIES #

    @property
    def channel(self):
        """
        Gets the specific channel object.
        This channel is accessed as a list in the following manner::

        >>> import instruments as ik
        >>> yoko = ik.yokogawa.Yokogawa7630.open_gpibusb('/dev/ttyUSB0')
        >>> dat = yoko.channel[0].data # Gets the data of channel 0

        :rtype: `~Yokogawa6370.Channel`
        """
        return ProxyList(self, Yokogawa6370.Channel, range(6))



    start_wl, start_wl_min, start_wl_max = bounded_unitful_property(
        ":SENS:WAV:STAR",
        pq.meter,
        doc="""
        The start wavelength in m.
        """,
        valid_range = (600e-9,1700e-9)
    )
    
    stop_wl, stop_wl_min, stop_wl_max = bounded_unitful_property(
        ":SENS:WAV:STOP",
        pq.meter,
        doc="""
        The stop wavelength in m.
        """,
        valid_range = (600e-9,1700e-9)
    )
    
    bandwidth = unitful_property(
        ":SENS:BAND:RES",
        pq.meter,
        doc="""
        The bandwidth in m.
        """
    )
    
    span = unitful_property(
        ":SENS:WAV:SPAN",
        pq.meter,
        doc="""
        A floating point property that controls the wavelength span in m.
        """)
   
    center_wl = unitful_property(
        ":SENS:WAV:CENT",
        pq.meter,
        doc="""
         A floating point property that controls the center wavelength m.
        """)
    
    points = unitless_property( 
       ":SENS:SWE:POIN",
       doc="""
        An integer property that controls the number of points in a trace.
        """)
        
    sweep_mode = enum_property(
        ":INIT:SMOD",
        SweepModes,
        input_decoration = lambda val: int(val),
        doc = """
        A property to control the Sweep Mode as oe of Yokogawa6370.SweepMode. 
        Effective only after a self.start_sweep()."""
        )
    
    active_trace = enum_property(
    ":TRAC:ACTIVE",
    Traces,
    doc = """
    The active trace of the OSA of enum Yokogawa6370.Traces. Determines the 
    result of Yokogawa6370.data() and Yokogawa6370.wavelength()."""
    )
    

    # METHODS #
    
    
    
    def data(self):
        """
        Function to query the active Trace data of the OSA.
        """
        cmd = ':TRAC:Y? '+ self.active_trace.value
        self.sendcmd(cmd)
        data = self.binblockread(data_width = 4,fmt = '<d')
        self._file.read_raw(1)
        return data
        
    def wavelength(self):
        """
        Query the wavelength axis of the active trace.
        """
        cmd = ':TRAC:X? '+  self.active_trace.value    
        self.sendcmd(cmd)
        data = self.binblockread(data_width = 4,fmt = '<d')
        self._file.read_raw(1)
        return data

    def start_sweep(self):
        """
        Triggering function for the Yokogawa 7630.

        After changing the sweep mode, the device needs to be triggered before it will update.
        """
        self.sendcmd('*CLS;:init')
