#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# gi_gpib.py: Wrapper for Galvant Industries GPIB adapters.
##
# © 2013-2014 Steven Casagrande (scasagrande@galvant.ca).
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
import quantities as pq

from instruments.abstract_instruments.comm import serialManager, AbstractCommunicator
from instruments.util_fns import assume_units

## CLASSES #####################################################################

class GPIBWrapper(io.IOBase, AbstractCommunicator):
    '''
    Wraps a SocketWrapper or PySerial.Serial connection for use with
    Galvant Industries GPIBUSB or GPIBETHERNET adapters.
    
    This wrapper is designed to wrap the SocketWrapper and SerialWrapper
    classes.
    '''
    def __init__(self, filelike, gpib_address):
        AbstractCommunicator.__init__(self)
        
        self._file = filelike
        self._gpib_address = gpib_address
        self._file.terminator = '\r'
        self._version = int(self._file.query("+ver"))
        self.terminator = 10
        self._eoi = True
        self._timeout = 1000 * pq.millisecond
        
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
        return self._timeout
    @timeout.setter
    def timeout(self, newval):
        newval = assume_units(newval, pq.second)
        if self._version <= 4:
            newval = newval.rescale(pq.second)
            self._file.sendcmd('+t:{}'.format(newval.magnitude))
        elif self._version >= 5:
            newval = newval.rescale(pq.millisecond)
            self._file.sendcmd("++read_tmo_ms {}".format(newval.magnitude))
        self._file.timeout = newval.rescale(pq.second)
        self._timeout = newval.rescale(pq.second)
    
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
        
        if self._version <= 4:
            if newval == 'eoi':
                self._eoi = True
            elif not isinstance(newval, int):
                raise TypeError('GPIB termination must be integer 0-255 '
                                    'represending decimal value of ASCII '
                                    'termination character or a string' 
                                    'containing "eoi".')
            elif (newval < 0) or (newval > 255):
                raise ValueError('GPIB termination must be integer 0-255 '
                                    'represending decimal value of ASCII '
                                    'termination character.')
            else:
                self._eoi = False
                self._terminator = str(newval)
        elif self._version >= 5:
            if newval != "eoi":
                self.eos = newval
                self.eoi = False
                self._terminator = self.eos
            elif newval == "eoi":
                self.eos = None
                self._terminator = 'eoi'
                self.eoi = True
    
    @property
    def eoi(self):
        return self._eoi
    @eoi.setter
    def eoi(self, newval):
        if not isinstance(newval, bool):
            raise TypeError("EOI status must be specified as a boolean")
        self._eoi = newval
        if self._version >= 5:
            self._file.sendcmd("++eoi {}".format('1' if newval else '0'))
        else:
            self._file.sendcmd("+eoi:{}".format('1' if newval else '0'))
            
    @property
    def eos(self):
        return self._eos
    @eos.setter
    def eos(self, newval):
        if self._version <= 4:
            if isinstance(newval, str):
                newval = ord(newval)
            self._file.sendcmd("+eos:{}".format(newval))
            self._eos = newval
        elif self._version >= 5:
            if isinstance(newval, int):
                newval = str(unichr(newval))
            if newval == "\r\n":
                self._eos = newval
                newval = 0
            elif newval == "\r":
                self._eos = newval
                newval = 1
            elif newval == "\n":
                self._eos = newval
                newval = 2
            elif newval == None:
                self._eos = newval
                newval = 3
            else:
                raise ValueError("EOS must be CRLF, CR, LF, or None")
            self._file.sendcmd("++eos {}".format(newval))
    
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
        
    def flush_input(self):
        '''
        Instruct the wrapper to flush the input buffer, discarding the entirety
        of its contents.
        '''
        self._file.flush_input()
        
    ## METHODS ##
    
    def _sendcmd(self, msg):
        '''
        '''
        if msg == '':
            return
        self._file.sendcmd('+a:' + str(self._gpib_address))
        time.sleep(0.01)
        self.eoi = self.eoi
        time.sleep(0.01)
        self.timeout = self.timeout
        time.sleep(0.01)
        self.eos = self.eos
        time.sleep(0.01)
        self._file.sendcmd(msg)
        time.sleep(0.01)
        
    def _query(self, msg, size=-1):
        '''
        '''
        self.sendcmd(msg)
        if '?' not in msg:
            self._file.sendcmd('+read')
        return self._file.read(size).strip()
    
