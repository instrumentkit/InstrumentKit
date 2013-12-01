#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# gi_gpib.py: Wrapper for Galvant Industries GPIB adapters.
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

## IMPORTS #####################################################################

import io
import time

import numpy as np

import serialManager
from instruments.abstract_instruments import WrapperABC

## CLASSES #####################################################################

class GPIBWrapper(io.IOBase, WrapperABC):
    '''
    Wraps a SocketWrapper or PySerial.Serial connection for use with
    Galvant Industries GPIBUSB or GPIBETHERNET adapters.
    
    This wrapper is designed to wrap the SocketWrapper and SerialWrapper
    classes.
    '''
    def __init__(self, filelike, gpib_address):
        self._file = filelike
        self._gpib_address = gpib_address
        self._terminator = 10
        self._eoi = 1
        self._file.terminator = '\r'
        self._strip = 0
    
    def __repr__(self):
        return "<GPIBWrapper object at 0x{:X} "\
                "wrapping {}>".format(id(self), self._file)
                
    ## PROPERTIES ##
    
    @property
    def address(self):
        return (self._gpib_address, self._file.address)
    @address.setter
    def address(self, newval):
        '''
        Change GPIB address and downstream address associated with 
        the instrument.
        
        If specified as an integer, only changes the GPIB address. If specified
        as a list, the first element changes the GPIB address, while the second
        is passed downstream.
        
        Example: [<int>gpib_address, downstream_address]
        
        Where downstream_address needs to be formatted as appropriate for the
        connection (eg SerialWrapper, SocketWrapper, etc).
        '''
        if isinstance(newval, int):
            if (newval < 1) or (newval > 30):
                raise ValueError("GPIB address must be between 1 and 30.")
            self._gpib_address = newval
        elif isinstance(newval, list):
            self.address = newval[0] # Set GPIB address
            self._file.address = newval[1] # Send downstream address
        else:
            raise TypeError("Not a valid input type for Instrument address.")
        
            
    @property
    def timeout(self):
        return self._file.timeout
    @timeout.setter
    def timeout(self, newval):
        newval = int(newval)
        self._file.sendcmd('+t:{}'.format(newval))
        self._file.timeout = newval
    
    @property
    def terminator(self):
        if not self._eoi:
            return self._terminator
        else:
            return 'eoi'
    @terminator.setter
    def terminator(self, newval):
        if isinstance(newval, str):
            newval = newval.lower()
        if newval == 'eoi':
            self._eoi = 1
        elif not isinstance(newval, int):
            raise TypeError('GPIB termination must be integer 0-255 '
                                'represending decimal value of ASCII '
                                'termination character or a string containing' 
                                ' "eoi".')
        elif (newval < 0) or (newval > 255):
            raise ValueError('GPIB termination must be integer 0-255 '
                                'represending decimal value of ASCII '
                                'termination character.')
        else:
            self._eoi = 0
            self._terminator = str(newval)


    @property
    def strip(self):
        """
        Gets/sets the number of characters to strip from the end of
        responses from the instrument.

        :type: `int`
        """
        return self._strip
    @strip.setter
    def strip(self, newval):
        newval = int(newval)
        if newval < 0:
            raise ValueError("Cannot strip negative numbers of characters.")
        self._strip = newval
    
    
    ## FILE-LIKE METHODS ##
    
    def close(self):
        self._file.close()
        
    def read(self, size):
        '''
        Read characters from wrapped class (ie SocketWrapper or 
        PySerial.Serial).
        
        If size = -1, characters will be read until termination character
        is found.
        
        GI GPIB adapters always terminate serial connections with a CR.
        Function will read until a CR is found.
        '''
        msg = self._file.read(size)

        # Check for extra terminators added by the GI-GPIB adapter.
        #if msg[-1] == "\r":
        #    msg = msg[:-1]

        return msg
    
    def write(self, msg):
        '''
        Write data string to GPIB connected instrument.
        This function sends all the necessary GI-GPIB adapter internal commands
        that are required for the specified instrument.  
        '''
        self._file.write(msg)
        
    ## METHODS ##
    
    def sendcmd(self, msg):
        '''
        '''
        self._file.sendcmd('+a:' + str(self._gpib_address))
        time.sleep(0.02)
        self._file.sendcmd('+eoi:{}'.format(self._eoi))
        time.sleep(0.02)
        self._file.sendcmd('+strip:{}'.format(self._strip))
        time.sleep(0.02)
        if self._eoi is 0:
            self._file.sendcmd('+eos:{}'.format(self._terminator))
            time.sleep(0.02)
        self._file.sendcmd(msg)
        time.sleep(0.02)
        
    def query(self, msg, size=-1):
        '''
        '''
        self.sendcmd(msg)
        if '?' not in msg:
            self._file.sendcmd('+read')
        return self._file.read(size).strip()
        
        
    
    
