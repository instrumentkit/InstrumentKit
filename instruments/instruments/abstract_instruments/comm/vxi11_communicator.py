#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# vxi11_communicator.py: Communicator that uses python-vxi11 to interface 
#     with VXI11 devices.
##
# © 2016 Steven Casagrande (scasagrande@galvant.ca).
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
    import vxi11
except ImportError:
    vxi11 = None

## CLASSES #####################################################################

class VXI11Communicator(io.IOBase, AbstractCommunicator):
    """
    Wraps a VXI-11 device. Arguments are all essentially just passed
    to `vxi11.Instrument`.
    
    VXI-11 is an RPC-based communication protocol over ethernet primarily used 
    for connecting test and measurement equipment to controller hardware.
    VXI-11 allows for improved communication speeds and reduced latency over 
    that of communicating using TCP over a socket connection.
    
    VXI-11 is developed and maintained by the IVI Foundation. More information
    can be found on their website, as well as that of the LXI standard website.
    
    VXI-11 has since been superseeded by HiSLIP, which features fixes, improved
    performance, and new features such as IPv6 support.
    """
    
    def __init__(self, *args, **kwargs):
        if vxi11 is None:
            raise ImportError("Packge python-vxi11 is required for XVI11 "
                              "connected instruments.")
        AbstractCommunicator.__init__(self)
            
        self._inst = vxi11.Instrument(*args, **kwargs)
    
    ## PROPERTIES ##
    
    @property
    def address(self):
        return [self._inst.host, self._inst.name]
        
    @property
    def terminator(self):
        return self._inst.term_char
    @terminator.setter
    def terminator(self, newval):
        self._inst.term_char = newval
        
    @property
    def timeout(self):
        return self._inst.timeout
    @timeout.setter
    def timeout(self, newval):
        self._inst.timeout = newval # In seconds

    ## FILE-LIKE METHODS ##
    
    def close(self):
        try:
            self._inst.close()
        except:
            pass
        
    def read(self, size=-1):
        msg = self._inst.read(num=size)
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
        self.write(msg)
        
    def _query(self, msg, size=-1):
        return self._inst.ask(msg, num=size)
        
