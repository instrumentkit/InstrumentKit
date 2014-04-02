#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# usbtmc.py: Communicator that uses Python-USBTMC to communicate with TMC
#     devices.
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

## IMPORTS #####################################################################

import io

from instruments.abstract_instruments.comm.abstract_comm import AbstractCommunicator

try:
    import usbtmc
except ImportError:
    usbtmc = None

## CLASSES #####################################################################

class USBTMCCommunicator(io.IOBase, AbstractCommunicator):
    """
    Wraps a USBTMC device. Arguments are passed to `usbtmc.Instrument`.
    """
    
    def __init__(self, *args, **kwargs):
        if usbtmc is None:
            raise ImportError("usbtmc is required for TMC instruments.")
        AbstractCommunicator.__init__(self)
            
        self._inst = usbtmc.Instrument(*args, **kwargs)
        self._terminator = "\n" # Use the system default line ending by default.
    
    ## PROPERTIES ##
    
    @property
    def address(self):
        if hasattr(self._filelike, 'name'):
            return id(self._inst) # TODO: replace with something more useful.
        else:
            return None
        
    @property
    def terminator(self):
        return self._terminator
    @terminator.setter
    def terminator(self, newval):
        self._terminator = str(newval)
        
    @property
    def timeout(self):
        raise NotImplementedError
    @timeout.setter
    def timeout(self, newval):
        raise NotImplementedError

    ## FILE-LIKE METHODS ##
    
    def close(self):
        try:
            self._filelike.close()
        except:
            pass
        
    def read(self, size):
        msg = self._inst.read_raw(size)
        return msg
        
    def write(self, msg):
        self._inst.write(msg)
        
    def seek(self, offset):
        raise NotImplementedError
        
    def tell(self):
        raise NotImplementedError
        
    def flush(self):
        raise NotImplementedError
        
    ## METHODS ##
    
    def _sendcmd(self, msg):
        self._inst.write("{}{}".format(msg, self.terminator))
        
    def _query(self, msg, size=-1):
        return self._inst.ask(msg)
        
