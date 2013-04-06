#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# gi_gpib.py: Wrapper for Galvant Industries GPIB adapters.
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

import io
import time

import numpy as np

import serialManager

## CLASSES #####################################################################

class GPIBWrapper(io.IOBase):
    '''
    Wraps a SocketWrapper or PySerial.Serial connection for use with
    Galvant Industries GPIBUSB or GPIBETHERNET adapters.
    
    This wrapper is designed to wrap the SocketWrapper and SerialWrapper
    classes.
    '''
    def __init__(self, filelike, gpib_address):
        self._file = filelike
        self._address = gpib_address
    
    def __repr__(self):
        return "<GPIBWrapper object at 0x{:X} "\
                "wrapping {}>".format(id(self), self._file)
                
    ## PROPERTIES ##
    
    @property
    def address(self):
        return self._address
    @address.setter
    def address(self, newval):
        # TODO: Should take a hardware connection address to pass on, as well
        # as the currently implemented GPIB address
        if not isinstance(newval, int):
            raise TypeError("New GPIB address must be specified as "
                                "an integer.")
        if (newval < 1) or (newval > 30):
            raise ValueError("GPIB address must be between 1 and 30.")
            
    @property
    def timeout(self):
        raise NotImplementedError
    @timeout.setter
    def timeout(self, newval):
        raise NotImplementedError
    
    ## FILE-LIKE METHODS ##
    
    def close(self):
        self._file.close()
        
    def read(self, size):
        '''
        Read characters from wrapped class (ie SocketWrapper or 
        PySerial.Serial).
        
        If size = 0, characters will be read until termination character
        is found.
        
        GI GPIB adapters always terminate serial connections with a CR.
        Function will read until a CR is found.
        '''
        if (size > 0):
            return self._file.read(size)
        elif (size == 0):
            result = np.bytearray()
            c = 0
            while c != '\r':
                c = self._file.read(1)
                result += c
            return bytes(result)
        else:
            raise ValueError('Must read a positive value of characters.')
    
    def write(self, msg):
        '''
        Write data string to GPIB connected instrument.
        This function sends all the necessary GI-GPIB adapter internal commands
        that are required for the specified instrument.  
        '''
        # TODO: include other internal flags such as +eoi
        self._file.write('+a:' + str(self._address) + '\r')
        time.sleep(0.02)
        self._file.write(msg + '\r')
        time.sleep(0.02)
    
    
