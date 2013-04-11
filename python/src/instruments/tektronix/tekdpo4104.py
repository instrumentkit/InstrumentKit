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

from contextlib import contextmanager

import quantities as pq

from instruments.generic_scpi import SCPIInstrument
from instruments.util_fns import assume_units

import struct

## ENUMS #######################################################################

class TekDPO4104Coupling(Enum):
    ac = "AC"
    dc = "DC"
    ground = "GROUND"

## CLASSES #####################################################################

class TekDPO4104Channel(object):
    def __init__(self, tek, idx):
        self._tek = tek
        # Zero-based for pythonic convienence, so we need to convert to
        # Tektronix's one-based notation here.
        self._idx = idx + 1

    @property
    def coupling(self):
        """
        Gets/sets the coupling setting for this channel.

        :type: `TekDPO4104Coupling`
        """
        return TekDPO4104Coupling[self.query("CH{}:COUPL?".format(self._idx))]
    @coupling.setter
    def coupling(self, newval):
        if not isinstance(newval, TekDPO4104Coupling):
            raise TypeError("Coupling setting must be a TekDPO4104Coupling value.")

        self.sendcmd("CH{}:COUPL {}".format(self._idx, newval.value))

    
    # Read Waveform        
    def read_waveform(self, bin_format=False):
        '''
        Read waveform from the oscilloscope.
        This function is all inclusive. After reading the data from the oscilloscope, it unpacks the data and scales it accordingly.
        Supports both ASCII and binary waveform transfer. For 2500 data points, with a width of 2 bytes, transfer takes approx 2 seconds for binary, and 7 seconds for ASCII.
        
        Function returns a list [x,y], where both x and y are numpy arrays.

        :param bool bin_format: If `True, data is transfered
            in a binary format. Otherwise, data is transferred in ASCII.
        '''

        # FIXME: removed support for REFA, REFB, REFC, REFD and MATH.
        #        this is a regression that must be fixed, probably
        #        by identifying them as virtual channels.

        ch_id = "CH{}".format(self._idx)

        # Set the acquisition channel
        self.sendcmd('DAT:SOU {}'.format(ch_id))
        
        if not bin_format:
            self.sendcmd( 'DAT:ENC ASCI' ) # Set the data encoding format to ASCII
            raw = self.query( 'CURVE?' )
            raw = raw.split(",") # Break up comma delimited string
            raw = map(float, raw) # Convert each list element to int
            raw = np.array(raw) # Convert into numpy array
        else
            self.sendcmd( 'DAT:ENC RIB' ) # Set encoding to signed, big-endian
            self.sendcmd( 'CURVE?' )
            raw = self.binblockread(2) # Read in the binary block, data width of 2 bytes

            self._file.read(2) # Read in the two ending \n\r characters

        # FIXME: the following has not yet been converted.
        #        Needs to be fixed before it will even run.
        yoffs = self.query( 'WFMP:' + channel.upper() + ':YOF?' ) # Retrieve Y offset
        ymult = self.query( 'WFMP:' + channel.upper() + ':YMU?' ) # Retrieve Y multiplier
        yzero = self.query( 'WFMP:' + channel.upper() + ':YZE?' ) # Retrieve Y zero
        
        y = ( (raw - float(yoffs) ) * float(ymult) ) + float(yzero)
        
        xzero = self.query( 'WFMP:XZE?' ) # Retrieve X zero
        xincr = self.query( 'WFMP:XIN?' ) # Retrieve X incr
        ptcnt = self.query( 'WFMP:' + channel.upper() + ':NR_P?' ) # Retrieve number of data points
        
        x = arange( float(ptcnt) ) * float(xincr) + float(xzero)
        
        return [x,y]

class ChannelList(object):
    def __init__(self, tek):
        self._tek = tek
    def __getitem__(self, idx):
        if idx < 0 or idx > 3:
            raise IndexError("Channel index out of range. Must be in xrange(4).")
        return TekDPO4104Channel(self._tek, idx)

class TekDPO4104(SCPIInstrument):

    @property
    def channel(self):
        return ChannelList(self)

        
