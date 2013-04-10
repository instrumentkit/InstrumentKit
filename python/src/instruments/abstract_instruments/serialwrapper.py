#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# socketwrapper.py: Wraps sockets into a filelike object.
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
import serial

import numpy as np

from instruments.abstract_instruments import WrapperABC

## CLASSES #####################################################################

class SerialWrapper(io.IOBase, WrapperABC):
    """
    Wraps a pyserial Serial object to add a few properties as well as
    handling of termination characters.
    """
    
    def __init__(self, conn):
        if isinstance(conn, serial.Serial):
            self._conn = conn
            self._terminator = '\n'
        else:
            raise TypeError('SerialWrapper must wrap a serial.Serial object.')
    
    def __repr__(self):
        return "<SerialWrapper object at 0x{:X} "\
                "connected to {}>".format(id(self), self._conn.port)
    
    ## PROPERTIES ##
    
    @property
    def address(self):
        return self._conn.port
    @address.setter
    def address(self, newval):
        # TODO: Input checking on Serial port newval
        # TODO: Add port changing capability to serialmanager
        # self._conn.port = newval
        raise NotImplementedError
        
    @property
    def terminator(self):
        return self._terminator
    @terminator.setter
    def terminator(self, newval):
        if not isinstance(newval, str):
            raise TypeError('Terminator for SerialWrapper must be specified '
                              'as a single character string.')
        if len(newval) > 1:
            raise ValueError('Terminator for SerialWrapper must only be 1 '
                                'character long.')
        self._terminator = newval
        
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
            result = np.bytearray()
            c = 0
            while c != self._terminator:
                c = self._file.read(1)
                result += c
            return bytes(result)
        else:
            raise ValueError('Must read a positive value of characters.')
        
    def write(self, string):
        self._conn.sendall(string + self._terminator)
        
    def seek(self, offset):
        return NotImplemented
        
    def tell(self):
        return NotImplemented
