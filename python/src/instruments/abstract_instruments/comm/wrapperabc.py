#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# wrapperabc.py: Python ABC for file-like wrappers
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

## FEATURES ####################################################################

from __future__ import division

## IMPORTS #####################################################################

import abc

class WrapperABC(object):
    __metaclass__ = abc.ABCMeta
    
    ## PROPERTIES ##
    
    def getaddress(self):
        '''
        Read the current instrument address
        '''
        raise NotImplementedError
    def setaddress(self, newval):
        '''
        Change the instrument address
        '''
        raise NotImplementedError
    address = abc.abstractproperty(getaddress, setaddress)
    
    def getterminator(self):
        '''
        Read the EOS termination
        '''
        raise NotImplementedError
    def setterminator(self, newval):
        '''
        Change the communication EOS terminator
        '''
        raise NotImplementedError
    terminator = abc.abstractproperty(getterminator, setterminator)
    
    def gettimeout(self):
        '''
        Get the connection interface timeout
        '''
        raise NotImplementedError
    def settimeout(self, newval):
        '''
        Set the connection interface timeout
        '''
        raise NotImplementedError
    timeout = abc.abstractproperty(gettimeout, settimeout)
    
    ## METHODS ##
    
    @abc.abstractmethod
    def sendcmd(self, msg):
        '''
        Sends the incoming msg down to the wrapped file-like object
        but appends any other commands or termination characters required
        by the communication.
        
        This differs from the wrapper .write method which directly exposes
        the communication channel without appending other data.
        '''
        raise NotImplementedError
    
    @abc.abstractmethod    
    def query(self, msg, size=-1):
        '''
        Send a string to the connected instrument using sendcmd and read the
        response. This is an abstract method because there are situations where
        information contained in the sent command is needed for reading logic.
        
        An example of this is the Galvant Industries GPIB adapter where if
        you are connected to an older instrument and the query command does not
        contain a `?`, then the command `+read` needs to be send to force the
        instrument to send its response.
        '''
        raise NotImplementedError
        
    @abc.abstractmethod
    def flush_input(self):
        '''
        Instruct the wrapper to flush the input buffer, discarding the entirety
        of its contents.
        '''
        raise NotImplementedError

