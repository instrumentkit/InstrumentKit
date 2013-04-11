#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# usbwrapper.py: Wraps USB connections into a filelike object.
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

import numpy as np

from instruments.abstract_instruments import WrapperABC

## CLASSES #####################################################################

class USBWrapper(io.IOBase, WrapperABC):
    '''
    
    '''
    def __init__(self, conn):
        # TODO: Check to make sure this is a USB connection
        self._conn = conn
        self._terminator = '\n'
        self._debug = False
    
    def __repr__(self):
        # TODO: put in correct connection name
        return "<USBWrapper object at 0x{:X} "\
                "connected to {}>".format(id(self), 'placeholder')
    
    ## PROPERTIES ##
    
    @property
    def address(self):
        '''
        
        '''
        raise NotImplementedError
    @address.setter
    def address(self, newval):
        raise ValueError('Unable to change USB target address.')
    
    @property
    def terminator(self):
        reutrn self._terminator
    @terminator.setter
    def terminator(self, newval):
        if not isinstance(newval, str):
            raise TypeError('Terminator for USBWrapper must be specified '
                              'as a single character string.')
        if len(newval) > 1:
            raise ValueError('Terminator for USBWrapper must only be 1 '
                                'character long.')
        self._terminator = newval
    
    @property
    def debug(self):
        """
        Gets/sets whether debug mode is enabled for this connection.
        If `True`, all output is echoed to stdout.

        :type: `bool`
        """
        return self._debug
    @debug.setter
    def debug(self, newval):
        self._debug = bool(newval)
    
    ## FILE-LIKE METHODS ##
    
    def close(self):
        try:
            self._conn.shutdown()
        finally:
            self._conn.close()
            
    def read(self, size):
        raise NotImplementedError
    
    def write(self, string):
        self._conn.write(string)
        
    def seek(self, offset):
        return NotImplemented
        
    def tell(self):
        return NotImplemented
    
    ## METHODS ##
    
    def sendcmd(self, msg):
        '''
        '''
        msg = msg + self._terminator
        if self._debug:
            print " <- {} ".format(repr(msg))
        self._conn.sendall(msg)
        
    def query(self, msg, size=-1):
        '''
        '''
        self.sendcmd(msg)
        self.read(size)
