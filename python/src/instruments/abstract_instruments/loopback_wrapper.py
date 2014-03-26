#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# loopback_wrappper.py: Loopback wrapper, just prints what it receives or 
#                       queries return empty string
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
from instruments.abstract_instruments import WrapperABC

## CLASSES #####################################################################

class LoopbackWrapper(io.IOBase, WrapperABC):
    """
    Used for testing various controllers
    """
    
    def __init__(self, stdin=None, stdout=None):
        self._terminator = '\n'
        self._stdout = stdout
        self._stdin = stdin
        
    def __repr__(self):
        return "<LoopbackWrapper object at 0x{:X} "\
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
            raise ValueError('Terminator for LoopbackWrapper must only be 1 '
                                'character long.')
        self._terminator = newval
        
    @property
    def timeout(self):
        return 0
    @timeout.setter
    def timeout(self, newval):
        pass

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
        """
        Gets desired response command from user
        :rtype: `str`
        """
        if self._stdin is not None:
            input_var = self._stdin.read(size)
        else:
            input_var = raw_input("Desired Response: ")
        return input_var
        
    def write(self, msg):
        if self._stdout is not None:
            self._stdout.write(msg)
        else:
            print " <- {} ".format(repr(msg))
        
        
    def seek(self, offset):
        return NotImplemented
        
    def tell(self):
        return NotImplemented
        
    def flush_input(self):
        pass
        
    ## METHODS ##
    
    def sendcmd(self, msg):
        '''
        Receives a command and passes off to write function
        :param str msg: The command to be received
        '''
        msg = msg + self._terminator
        self.write(msg)
        
    def query(self, msg, size=-1):
        '''
        Receives a query and returns the generated Response
        :param str msg: The message to received
        :rtype: `str`
        '''
        self.sendcmd(msg)
        resp = self.read(size)
        return resp
