#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# instrument.py: Provides base class for all instruments.
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

import serial
import time
import struct
import socket
import urlparse

import serialManager as sm
import socketwrapper as sw
import usbwrapper as uw
import visawrapper as vw
import gi_gpib
from instruments.abstract_instruments import WrapperABC

try:
    import usb
    import usb.core
    import usb.util
except ImportError:
    usb = None

try:
    import visa
except ImportError:
    visa = None

import numpy as np

## CLASSES #####################################################################

class Instrument(object):

    # Set a default terminator.
    # This can and should be overriden in subclasses for instruments
    # that use different terminators.
    _terminator = "\n"
    
    def __init__(self, filelike):
        # Check to make sure filelike is a subclass of WrapperABC
        if isinstance(filelike, WrapperABC):
            self._file = filelike
        else:
            raise TypeError('Instrument must be initialized with a filelike '
                              'object that is a subclass of WrapperABC.')
    
    ## COMMAND-HANDLING METHODS ##
    
    def sendcmd(self, cmd):
        """
        Sends a command without waiting for a response. 
        
        :param str cmd: String containing the command to
            be sent.
        """
        self.write(str(cmd))
        
    def query(self, cmd, size=-1):
        """
        Executes the given query.
        
        :param str cmd: String containing the query to 
            execute.
        :param int size: Number of bytes to be read. Default is read until
            termination character is found.
        :return: The result of the query as returned by the
            connected instrument.
        :rtype: `str`
        """
        return self._file.query(cmd, size)
        
    ## PROPERTIES ##
    
    @property
    def timeout(self):
        return self._file.timeout
    @timeout.setter
    def timeout(self, newval):
        self._file.timeout = newval
    
    @property
    def address(self):
        return self._file.address
    @address.setter
    def address(self, newval):
        self._file.address = newval
            
    @property
    def terminator(self):
        return self._file.terminator
    @terminator.setter
    def terminator(self, newval):
        self._file.terminator = newval
        
    ## BASIC I/O METHODS ##
    
    def write(self, msg):
        '''
        Write data string to GPIB connected instrument.
        This function sends all the necessary GI-GPIB adapter internal commands
        that are required for the specified instrument.  
        '''
        self._file.write(msg)        
        
    def binblockread(self,dataWidth):
        '''
        Read a binary data block from attached instrument.
        This requires that the instrument respond in a particular manner
        as EOL terminators naturally can not be used in binary transfers.
        
        The format is as follows:
        #{number of following digits:1-9}{num of bytes to be read}{data bytes}
        
        '''
        if( dataWidth not in [1,2]):
            print 'Error: Data width must be 1 or 2.'
            return 0
        # This needs to be a # symbol for valid binary block
        symbol = self._file.read(1)
        if( symbol != '#' ): # Check to make sure block is valid
            raise ValueError('Not a valid binary block start. Binary blocks '
                                'require the first character to be #.')
            return 0
        else:
            # Read in the num of digits for next part
            digits = int( self._file.read(1) )
            # Read in the num of bytes to be read
            num_of_bytes = int( self._file.read(digits) )
            # Read in the data bytes
            temp = self._file.read(num_of_bytes)
            
            # Create zero array
            raw = np.zeros(num_of_bytes/dataWidth)
            for i in range(0,num_of_bytes/dataWidth):
                # Parse binary string into ints
                raw[i] = struct.unpack(">h", temp[i*dataWidth:\
                                                  i*dataWidth+dataWidth])[0]
            del temp
        
            return raw
            
    ## CLASS METHODS ##
    
    @classmethod
    def open_from_uri(cls, uri):
        # Break apart the URI using urlparse. This returns a named tuple whose
        # parts describe the incoming URI.
        parsed_uri = urlparse.urlparse(uri)
        
        # We always want the query string to provide keyword args to the
        # class method.
        # FIXME: This currently won't work, as everything is strings,
        #        but the other class methods expect ints or floats, depending. 
        kwargs = urlparse.parse_qs(parsed_uri.query)
        if parsed_uri.scheme == "serial":
            # Ex: serial:///dev/ttyACM0
            # We want to pass this verbatim to pyserial, save for that we
            # need to first parse the kwargs part. As such, we drop the query
            # string and fragment parts, then urlunparse the rest, substituting
            # empty strings in their places.
            return cls.open_serial(
                urlparse.urlunparse(parsed_uri[0:-2] + ("",) * 2),
                **kwargs)
        elif parsed_uri.scheme == "tcpip":
            # Ex: tcpip://192.168.0.10:4100
            return cls.open_tcpip(*parsed_uri.netloc.split(":"), **kwargs)
        elif parsed_uri.scheme == "gpib+usb" or scheme == "gpib+serial":
            # Ex: gpib+usb://COM3/15
            #     scheme="gpib+usb", netloc="COM3", path="/15"
            return cls.open_serial(
                parsed_uri.netloc,
                # Drop the leading / from the address.
                int(parsed_uri.path[1:]),
                **kwargs)
        elif parsed_uri.scheme == "visa":
            # Ex: visa://USB::{VID}::{PID}::{SERIAL}::0::INSTR
            #     where {VID}, {PID} and {SERIAL} are to be replaced with
            #     the vendor ID, product ID and serial number of the USB-VISA
            #     device.
            return cls.open_visa(parsed_uri.netloc, **kwargs)
        else:
            return NotImplementedError("Invalid scheme or not yet implemented.")
    
    @classmethod
    def open_tcpip(cls, host, port):
        conn = socket.socket()
        conn.connect((host, port))
        return cls(sw.SocketWrapper(conn))
        
    @classmethod
    def open_serial(cls, port, baud, timeout=3, writeTimeout=3):
        ser = sm.newSerialConnection(port, 
                                     baud,
                                     timeout, 
                                     writeTimeout)
        return cls(ser)
    
    @classmethod
    def open_gpibusb(cls, port, gpib_address, timeout=3, writeTimeout=3):
        ser = sm.newSerialConnection(port,
                timeout=timeout,
                 writeTimeout=writeTimeout)
        return cls(gi_gpib.GPIBWrapper(ser, gpib_address))
        
    @classmethod
    def open_gpibethernet(cls, host, port, gpib_address):
        conn = socket.socket()
        conn.connect((host, port))
        return cls(gi_gpib.GPIBWrapper(conn, gpib_address))

    @classmethod
    def open_visa(cls, resource_name):
        if visa is None:
            raise ImportError("PyVISA is required for loading VISA instruments.")
        ins = visa.instrument(resource_name)
        return cls(vw.VisaWrapper(ins))

    @classmethod
    def open_usb(cls, vid, pid):
        if usb is None:
            raise ImportError("USB support not imported. Do you have PyUSB version 1.0 or later?")

        dev = usb.core.find(idVendor=vid, idProduct=pid)
        if dev is None:
            raise IOError("No such device found.")

        # Use the default configuration offered by the device.
        dev.set_configuration()

        # Copied from the tutorial at:
        #     http://pyusb.sourceforge.net/docs/1.0/tutorial.html
        cfg = dev.get_active_configuration()
        interface_number = cfg[(0,0)].bInterfaceNumber
        alternate_setting = usb.control.get_interface(dev, interface_number)
        intf = usb.util.find_descriptor(
            cfg, bInterfaceNumber = interface_number,
            bAlternateSetting = alternate_setting
        )

        ep = usb.util.find_descriptor(
            intf,
            custom_match = lambda e: \
                usb.util.endpoint_direction(e.bEndpointAddress) == \
                usb.util.ENDPOINT_OUT
            )
        if ep is None:
            raise IOError("USB descriptor not found.")

        return cls(uw.USBWrapper(ep))
