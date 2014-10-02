#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# socketwrapper.py: Wraps sockets into a filelike object.
##
# © 2013-2014 Steven Casagrande (scasagrande@galvant.ca).
#        Chris Granade (cgranade@cgranade.com).
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
import socket

import numpy as np
import quantities as pq

from instruments.abstract_instruments.comm import AbstractCommunicator
from instruments.util_fns import assume_units

## CLASSES #####################################################################

class SocketWrapper(io.IOBase, AbstractCommunicator):
    """
    Wraps a socket to make it look like a `file`. Note that this is used instead
    of `socket.makefile`, as that method does not support timeouts. We do not
    support all features of `file`-like objects here, but enough to make
    `~instrument.Instrument` happy.
    """
    
    def __init__(self, conn):
        AbstractCommunicator.__init__(self)
        if isinstance(conn, socket.socket):
            self._conn = conn
            self._terminator = '\n'
        else:
            raise TypeError('SocketWrapper must wrap a socket.socket object.')
        
    ## PROPERTIES ##
    
    @property
    def address(self):
        '''
        Returns the socket peer address information as a tuple.
        '''
        return self._conn.getpeername()
    @address.setter
    def address(self, newval):
        raise NotImplementedError('Unable to change address of sockets.')
        
    @property
    def terminator(self):
        return self._terminator
    @terminator.setter
    def terminator(self, newval):
        if not isinstance(newval, str):
            raise TypeError('Terminator for SocketWrapper must be specified '
                              'as a single character string.')
        if len(newval) > 1:
            raise ValueError('Terminator for SocketWrapper must only be 1 '
                                'character long.')
        self._terminator = newval
        
    @property
    def timeout(self):
        return self._conn.gettimeout() * pq.second
    @timeout.setter
    def timeout(self, newval):
        newval = assume_units(newval, pq.second).rescale(pq.second).magnitude
        self._conn.settimeout(newval)
        
    ## FILE-LIKE METHODS ##
    
    def close(self):
        try:
            self._conn.shutdown()
        finally:
            self._conn.close()
        
    def read(self, size):
        if (size >= 0):
            return self._conn.recv(size)
        elif (size == -1):
            result = bytearray()
            c = 0
            while c != self._terminator:
                c = self._conn.recv(1)
                result += c
            return bytes(result)
        else:
            raise ValueError('Must read a positive value of characters.')
        
    def write(self, string):
        self._conn.sendall(string)
        
    def seek(self, offset):
        return NotImplemented
        
    def tell(self):
        return NotImplemented
        
    def flush_input(self):
        '''
        Instruct the wrapper to flush the input buffer, discarding the entirety
        of its contents.
        '''
        _ = self.read(-1) # Read in everything in the buffer and trash it
        
    ## METHODS ##
    
    def _sendcmd(self, msg):
        '''
        '''
        msg = msg + self._terminator
        self._conn.sendall(msg)
        
    def _query(self, msg, size=-1):
        '''
        '''
        self.sendcmd(msg)
        resp = self.read(size)
        return resp
    
