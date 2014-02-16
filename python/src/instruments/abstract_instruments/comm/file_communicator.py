#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# file_communicator.py: Treats a file on the filesystem as a communicator
#     (aka wrapper).
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

import errno
import io
import time
from instruments.abstract_instruments.comm import WrapperABC
import os

## CLASSES #####################################################################

class FileCommunicator(io.IOBase, WrapperABC):
    """
    Wraps a `file` object, providing ``sendcmd`` and ``query`` methods,
    while passing everything else through.
    
    :param filelike: File or name of a file to be wrapped as a communicator.
        Any file-like object wrapped by this class **must** support both
        reading and writing. If using the `open` builtin function, the mode
        ``r+`` is recommended, and has been tested to work with character
        devices under Linux.
    :type filelike: `str` or `file`
    """
    
    def __init__(self, filelike):
        if isinstance(filelike, str):
            filelike = open(filelike, 'r+')
            
        self._filelike = filelike
        self._terminator = "\n" # Use the system default line ending by default.
        self._debug = False
    
    def __repr__(self):
        return "<FileCommunicator object at 0x{:X} "\
                "connected to {}>".format(id(self), repr(self._filelike))
    
    ## PROPERTIES ##
    
    @property
    def address(self):
        if hasattr(self._filelike, 'name'):
            return self._filelike.name
        else:
            return None
    @address.setter
    def address(self, newval):
        raise NotImplementedError("Changing addresses of a file communicator"
                                     " is not yet supported.")
        
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
            self._filelike.close()
        except:
            pass
        
    def read(self, size):
        msg = self._filelike.read(size)
        if self._debug:
            print " -> {} ".format(repr(msg))
        return msg
        
    def write(self, msg):
        if self._debug:
            print " <- {} ".format(repr(msg))
        self._filelike.write(msg)
        
    def seek(self, offset):
        self._filelike.seek(offset)
        
    def tell(self):
        return self._filelike.tell()
        
    def flush(self):
        self._filelike.flush()
        
    ## METHODS ##
    
    def sendcmd(self, msg):
        msg = msg + self._terminator
        self.write(msg)
        self.flush()        
        
    def query(self, msg, size=-1):
        self.sendcmd(msg)
        time.sleep(0.02) # Give the bus time to respond.
        resp = ""
        try:
            # FIXME: this is slow, but we do it to avoid unreliable
            #        filelike devices such as some usbtmc-class devices.
            while True:
                nextchar = self._filelike.read(1)
                if not nextchar:
                    break
                resp += nextchar
                if nextchar.endswith(self._terminator):
                    break
        except IOError as ex:
            if ex.errno == errno.ETIMEDOUT:
                # We don't mind timeouts if resp is nonempty,
                # and will just return what we have.
                if not resp:
                    raise
            elif ex.errno != errno.EPIPE:
                raise # Reraise the existing exception.
            else: # Give a more helpful and specific exception.
                raise IOError(
                    "Pipe broken when reading from {}; this probably "
                    "indicates that the driver "
                    "providing the device file is unable to communicate with "
                    "the instrument. Consider restarting the instrument.".format(
                        self.address
                    ))
        if self._debug:
            print " -> {}".format(repr(resp))
        return resp
        
