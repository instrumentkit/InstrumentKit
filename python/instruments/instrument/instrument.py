#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# instrument.py: Provides base class for all instruments.
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
##

## IMPORTS #####################################################################

import serial
import time
import struct

from numpy import *

import serialManager

## CLASSES #####################################################################

class Instrument(object):
    def __init__(self, port, address, timeout_length=5):
        self._port = port
        self.address = address
        self._timeout = timeout_length
        self._ser = serialManager.newSerialConnection(port,timeout_length) 
        
    ## PROPERTIES ##
    
    @property
    def timeout(self):
        return self._timeout
    @timeout.setter
    def timeout(self, newval):
        self._timeout = newval
        self._ser.timeout = newval
    
    @property
    def address(self):
        return self._address
    @address.setter
    def address(self, newval):
        if not isinstance(newval, int):
            raise TypeError("New GPIB address must be specified as an integer.")
        if (newval < 1) or (newval > 30):
            raise ValueError("GPIB address must be between 1 and 30."
        self._address = newval
    
    @property
    def port(self):
        return self._port
        
    ## BASIC I/O METHODS ##
    
    def write(self, msg):
        self._ser.write("+a:" + str(self.address) + "\r")
        time.sleep(0.02)
        self._ser.write(msg + "\r")
        time.sleep(0.02)
    
    def query(self, msg):
        self.write(msg)
        if '?' not in msg: # If a question mark is not in the query string
            self.write('+read') # Force controller to read response from instrument
        #result = self.ser.readline(self,size=None,eol='\r')
        return self.readline()
        
    def readline(self):
        # Following routine is manually implemented because pyserial changed how Serial.readline
        # worked in later versions. 
        result = bytearray()
        c = 0
        while c != '\r':
            c = self._ser.read(1)
            result += c
        return bytes(result)
        
    def binblockread(self,dataWidth):
        if( dataWidth not in [1,2]):
            print 'Error: Data width must be 1 or 2.'
            return 0
        symbol = self.ser.read(1) # This needs to be a # symbol for valid binary block
        if( symbol != '#' ): # Check to make sure block is valid
            print 'Error: Not a valid binary block start. Binary blocks require the first character to be #.'
            return 0
        else:
            digits = int( self.ser.read(1) ) # Read in the num of digits for next part
            num_of_bytes = int( self.ser.read(digits) ) # Read in the num of bytes to be read
            temp = self.ser.read(num_of_bytes) # Read in the data bytes
        
            raw = zeros(num_of_bytes/dataWidth) # Create zero array
            for i in range(0,num_of_bytes/dataWidth):
                # Parse binary string into ints
                raw[i] = struct.unpack(">h", temp[i*dataWidth:i*dataWidth+dataWidth])[0]
            del temp
        
            return raw
