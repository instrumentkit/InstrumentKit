#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# socketwrapper.py: Wraps sockets into a filelike object.
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

## IMPORTS #####################################################################

import io

# Trick to conditionally ignore the NameError caused by catching WindowsError.
# Needed as PyVISA causes a WindowsError on Windows when VISA is not installed.
try:
    WindowsError
except NameError:
    WindowsError = None
try:
    import visa
except (ImportError, WindowsError, OSError):
    visa = None

import numpy as np
import quantities as pq

from instruments.abstract_instruments.comm import AbstractCommunicator
from instruments.util_fns import assume_units

## CLASSES #####################################################################

class VisaWrapper(io.IOBase, AbstractCommunicator):
    """
    Wraps a connection exposed by the VISA library.
    """
    
    def __init__(self, conn):
        AbstractCommunicator.__init__(self)
    
        if visa is None:
            raise ImportError("PyVISA required for accessing VISA instruments.")
            
        if isinstance(conn, visa.Instrument):
            self._conn = conn
            self._terminator = '\n'
        else:
            raise TypeError('VisaWrapper must wrap a VISA Instrument.')

        # Make a bytearray for holding data read in from the device
        # so that we can buffer for two-argument read.
        self._buf = bytearray()
        
    ## PROPERTIES ##
    
    @property
    def address(self):
        return self._conn.resource_name
    @address.setter
    def address(self, newval):
        raise NotImplementedError("Changing addresses of a VISA Instrument "
                                     "is not supported.")
        
    @property
    def terminator(self):
        return self._terminator
    @terminator.setter
    def terminator(self, newval):
        if not isinstance(newval, str):
            raise TypeError('Terminator for VisaWrapper must be specified '
                              'as a single character string.')
        if len(newval) > 1:
            raise ValueError('Terminator for VisaWrapper must only be 1 '
                                'character long.')
        self._terminator = newval
        
    @property
    def timeout(self):
        return self._conn.timeout * pq.second
    @timeout.setter
    def timeout(self, newval):
        newval = assume_units(newval, pq.second).rescale(pq.second).magnitude
        self._conn.timeout = newval

    ## FILE-LIKE METHODS ##
    
    def close(self):
        try:
            self._conn.close()
        except:
            pass
        
    def read(self, size):
        if (size >= 0):
            while len(self._buf) < size:
                self._buf += self._conn.read()
            msg = self._buf[:size]
            # Remove the front of the buffer.
            del self._buf[:size]
        elif (size == -1):
            # Read the whole contents, appending the buffer we've already read.
            msg = self._buf + self._conn.read()
            # Reset the contents of the buffer.
            self._buf = bytearray()
        else:
            raise ValueError('Must read a positive value of characters, or -1 for all characters.')

        return msg
        
    def write(self, msg):
        self._conn.write(msg)
        
    def seek(self, offset):
        return NotImplemented
        
    def tell(self):
        return NotImplemented
        
    def flush_input(self):
        '''
        Instruct the wrapper to flush the input buffer, discarding the entirety
        of its contents.
        '''
        #TODO: Find out how to flush with pyvisa
        pass
        
    ## METHODS ##
    
    def _sendcmd(self, msg):
        '''
        '''
        msg = msg + self._terminator
        self.write(msg)
        
    def _query(self, msg, size=-1):
        '''
        '''
        msg += self._terminator
        return self._conn.ask(msg)
        
