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
import socket

import serialManager as sm
import socketwrapper as sw
import gi_gpib
from instruments.abstract_instruments import WrapperABC

## CLASSES #####################################################################

class Instrument(object):

    # Set a default terminator.
    # This can and should be overriden in subclasses for instruments
    # that use different terminators.
    _terminator = "\n"
    
    def __init__(self, filelike):
        # Check to make sure filelike is a subclass of WrapperABC
        if isinstance(filelike, WrapperABC):
            self._file = filelike
        else:
            raise TypeError('Instrument must be initialized with a filelike '
                              'object that is a subclass of WrapperABC.')
    
    ## COMMAND-HANDLING METHODS ##
    
    def sendcmd(self, cmd):
        """
        Sends a command without waiting for a response. 
        
        :param str cmd: String containing the command to
            be sent.
        """
        self.write(str(cmd))
        
    def query(self, cmd, size=-1):
        """
        Executes the given query.
        
        :param str cmd: String containing the query to 
            execute.
        :param int size: Number of bytes to be read. Default is read until
            termination character is found.
        :return: The result of the query as returned by the
            connected instrument.
        :rtype: `str`
        """
        self.write(cmd)
        # TODO: Move the +read logic to GPIBWrapper
        #if '?' not in msg:
        #    self._file.write('+read')
        return self._file.read(size)
        
    ## PROPERTIES ##
    
    @property
    def timeout(self):
        return self._file.timeout
    @timeout.setter
    def timeout(self, newval):
        self._file.timeout = newval
    
    @property
    def address(self):
        return self._file.address
    @address.setter
    def address(self, newval):
        self._file.address = newval
            
    @property
    def terminator(self):
        return self._file.terminator
    @terminator.setter
    def terminator(self, newval):
        self._file.terminator = newval
        
    ## BASIC I/O METHODS ##
    
    def write(self, msg):
        '''
        Write data string to GPIB connected instrument.
        This function sends all the necessary GI-GPIB adapter internal commands
        that are required for the specified instrument.  
        '''
        self._file.write(msg)        
        
    def binblockread(self,dataWidth):
        '''
        Read a binary data block from attached instrument.
        This requires that the instrument respond in a particular manner
        as EOL terminators naturally can not be used in binary transfers.
        
        The format is as follows:
        #{number of following digits:1-9}{num of bytes to be read}{data bytes}
        
        '''
        if( dataWidth not in [1,2]):
            print 'Error: Data width must be 1 or 2.'
            return 0
        # This needs to be a # symbol for valid binary block
        symbol = self._file.read(1)
        if( symbol != '#' ): # Check to make sure block is valid
            raise ValueError('Not a valid binary block start. Binary blocks '
                                'require the first character to be #.')
            return 0
        else:
            # Read in the num of digits for next part
            digits = int( self.ser.read(1) )
            # Read in the num of bytes to be read
            num_of_bytes = int( self.ser.read(digits) )
            # Read in the data bytes
            temp = self.ser.read(num_of_bytes)
            
            # Create zero array
            raw = zeros(num_of_bytes/dataWidth)
            for i in range(0,num_of_bytes/dataWidth):
                # Parse binary string into ints
                raw[i] = struct.unpack(">h", temp[i*dataWidth:\
                                                  i*dataWidth+dataWidth])[0]
            del temp
        
            return raw
            
    ## CLASS METHODS ##
    
    @classmethod
    def open_tcpip(cls, host, port):
        conn = socket.socket()
        conn.connect((host, port))
        return cls(sw.SocketWrapper(conn))
        
    @classmethod
    def open_serial(cls, port, baud, timeout=3, writeTimeout=3):
        ser = sm.newSerialConnection(port, 
                                     baud,
                                     timeout, 
                                     writeTimeout)
        return cls(ser)
    
    @classmethod
    def open_gpibusb(cls, port, gpib_address, timeout=3, writeTimeout=3):
        ser = sm.newSerialConnection(port, timeout, writeTimeout)
        return cls(gi_gpib.GPIBWrapper(ser, gpib_address))
        
    @classmethod
    def open_gpibethernet(cls, host, port, gpib_address):
        conn = socket.socket()
        conn.connect((host, port))
        return cls(gi_gpib.GPIBWrapper(conn, gpib_address))
