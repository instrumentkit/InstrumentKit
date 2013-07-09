#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# testwrappper.py: Loopback wrapper, just prints what it receives or queries return empty string
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
from instruments.abstract_instruments import WrapperABC

## CLASSES #####################################################################

class LoopbackWrapper(io.IOBase, WrapperABC):
    """
    Used for testing various controllers
    """
    
    def __init__(self):
        self._terminator = '\n'
    def __repr__(self):
        return "<VisaWrapper object at 0x{:X} "\
                .format(id(self))
    
    ## PROPERTIES ##
    
    @property
    def address(self):
        raise NotImplementedError()
    @address.setter
    def address(self, newval):
        raise NotImplementedError()
        
    @property
    def terminator(self):
        return self._terminator
    @terminator.setter
    def terminator(self, newval):
        if not isinstance(newval, str):
            raise TypeError('Terminator must be specified '
                              'as a single character string.')
        if len(newval) > 1:
            raise ValueError('Terminator for VisaWrapper must only be 1 '
                                'character long.')
        self._terminator = newval
        
    @property
    def timeout(self):
        return 10
    @timeout.setter
    def timeout(self, newval):
        self._conn.timeout = newval

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
            self._conn.close()
        except:
            pass
        
    def read(self, size):
        print "Reading side: {0}".format(size)
        
    def write(self, msg):
        
        print " <- {} ".format(repr(msg))
        
        
    def seek(self, offset):
        return NotImplemented
        
    def tell(self):
        return NotImplemented
        
    ## METHODS ##
    
    def sendcmd(self, msg):
        '''
        '''
        msg = msg + self._terminator
        self.write(msg)
        
    def query(self, msg, size=-1):
        '''
        '''
        return msg
        