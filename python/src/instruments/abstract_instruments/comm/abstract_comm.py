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

## FEATURES ###################################################################

from __future__ import division

## IMPORTS ####################################################################

import abc
import logging

## CLASSES ####################################################################

class AbstractCommunicator(object):
    __metaclass__ = abc.ABCMeta
    
    ## INITIALIZER ##
    
    def __init__(self):
        self._debug = False
        
        # Create a new logger for the module containing the concrete
        # subclass that we're a part of.
        self._logger = logging.getLogger(type(self).__module__)
        
        # Ensure that there's at least something setup to receive logs.
        self._logger.addHandler(logging.NullHandler())
        
    ## FORMATTING METHODS ##
    
    def __repr__(self):
        return "<{} object at 0x{:X} "\
                "connected to {}>".format(type(self).__name__, id(self), repr(self.address))
    
    ## CONCRETE PROPERTIES ##
    
    @property
    def debug(self):
        """
        Enables or disables debug support. If active, all messages sent to
        or received from this communicator are logged to the Python logging
        service, with the logger name given by the module of the current
        communicator.
        Generating log messages for each exchanged command is slow, so these
        log messages are suppressed by default.
        
        Note that you must turn on logging to at least the DEBUG level in order
        to see these messages. For instance:
        
        >>> import logging
        >>> logging.basicConfig(level=logging.DEBUG)
        """
        return self._debug
    @debug.setter
    def debug(self, newval):
        self._debug = bool(newval)
    
    ## ABSTRACT PROPERTIES ##
    
    @abc.abstractproperty
    def address(self):
        '''
        Reads or changes the current address for this communicator.
        '''
        raise NotImplementedError
    
    @abc.abstractproperty
    def terminator(self):
        '''
        Reads or changes the EOS termination.
        '''
        raise NotImplementedError
    
    @abc.abstractproperty
    def timeout(self):
        '''
        Get the connection interface timeout.
        '''
        raise NotImplementedError
    
    ## ABSTRACT METHODS ##
    
    @abc.abstractmethod
    def _sendcmd(self, msg):
        '''
        Sends a message to the connected device, handling all proper
        termination characters and secondary commands as required.
        
        Note that this is called by :class:`AbstractCommunicator.sendcmd`,
        which also handles debug, event and capture support.
        '''
        pass
        
    @abc.abstractmethod    
    def _query(self, msg, size=-1):
        '''
        Send a string to the connected instrument using sendcmd and read the
        response. This is an abstract method because there are situations where
        information contained in the sent command is needed for reading logic.
        
        An example of this is the Galvant Industries GPIB adapter where if
        you are connected to an older instrument and the query command does not
        contain a `?`, then the command `+read` needs to be send to force the
        instrument to send its response.
        
        Note that this is called by :class:`AbstractCommunicator.query`,
        which also handles debug, event and capture support.
        '''
        pass
        
    
    ## CONCRETE METHODS ##
    
    def sendcmd(self, msg):
        '''
        Sends the incoming msg down to the wrapped file-like object
        but appends any other commands or termination characters required
        by the communication.
        
        This differs from the wrapper .write method which directly exposes
        the communication channel without appending other data.
        '''
        if self.debug:
            self._logger.debug(" <- {}".format(repr(msg)))
        self._sendcmd(msg)
    
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
        if self.debug:
            self._logger.debug(" <- {}".format(repr(msg)))
        resp = self._query(msg, size)
        if self.debug:
            self._logger.debug(" -> {}".format(repr(resp)))
        return resp
        
    @abc.abstractmethod
    def flush_input(self):
        '''
        Instruct the wrapper to flush the input buffer, discarding the entirety
        of its contents.
        '''
        raise NotImplementedError

