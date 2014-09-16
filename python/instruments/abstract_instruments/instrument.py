#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# instrument.py: Provides base class for all instruments.
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

import serial
import time
import struct
import socket
import urlparse

from instruments.abstract_instruments.comm import (
    SocketWrapper,
    USBWrapper,
    VisaWrapper,
    FileCommunicator,
    LoopbackWrapper,
    GPIBWrapper,
    AbstractCommunicator,
    USBTMCCommunicator,
    SerialWrapper,
    serialManager
)

import os

try:
    import usb
    import usb.core
    import usb.util
except ImportError:
    usb = None

try:
    WindowsError
except NameError:
    WindowsError = None
try:
    import visa
except (ImportError, WindowsError, OSError):
    visa = None

import numpy as np

import collections

## CONSTANTS ###################################################################

_DEFAULT_FORMATS = collections.defaultdict(lambda: '>b')
_DEFAULT_FORMATS.update({
    1: '>b',
    2: '>h',
    4: '>i'
})

## CLASSES #####################################################################

class Instrument(object):

    # Set a default terminator.
    # This can and should be overriden in subclasses for instruments
    # that use different terminators.
    _terminator = "\n"
    
    def __init__(self, filelike):
        # Check to make sure filelike is a subclass of AbstractCommunicator
        if isinstance(filelike, AbstractCommunicator):
            self._file = filelike
        else:
            raise TypeError('Instrument must be initialized with a filelike '
                              'object that is a subclass of AbstractCommunicator.')
    
    ## COMMAND-HANDLING METHODS ##
    
    def sendcmd(self, cmd):
        """
        Sends a command without waiting for a response. 
        
        :param str cmd: String containing the command to
            be sent.
        """
        self._file.sendcmd(str(cmd))
        
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

    def read(self, size=-1):
        """
        Read the last line.
        
        :param int size: Number of bytes to be read. Default is read until
            termination character is found.
        :return: The result of the read as returned by the
            connected instrument.
        :rtype: `str`
        """
        return self._file.read(size)

        
    ## PROPERTIES ##
    
    @property
    def timeout(self):
        '''
        Gets/sets the communication timeout for this instrument. Note that
        setting this value after opening the connection is not supported for
        all connection types.
        
        :type: `int`
        '''
        return self._file.timeout
    @timeout.setter
    def timeout(self, newval):
        self._file.timeout = newval
    
    @property
    def address(self):
        '''
        Gets/sets the target communication of the instrument.
        
        This is useful for situations when running straight from a Python shell
        and your instrument has enumerated with a different address. An example
        when this can happen is if you are using a USB to Serial adapter and
        you disconnect/reconnect it.
        
        :type: `int` for GPIB address, `str` for other
        '''
        return self._file.address
    @address.setter
    def address(self, newval):
        self._file.address = newval
            
    @property
    def terminator(self):
        '''
        Gets/sets the terminator used for communication.
        
        For communication options where this is applicable, the value 
        corresponds to the ASCII character used for termination in decimal 
        format. Example: 10 sets the character to NEWLINE.
        
        :type: `int`, or `str` for GPIB adapters. 
        '''
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
        
    def binblockread(self, data_width, fmt=None):
        '''
        Read a binary data block from attached instrument.
        This requires that the instrument respond in a particular manner
        as EOL terminators naturally can not be used in binary transfers.
        
        The format is as follows:
        #{number of following digits:1-9}{num of bytes to be read}{data bytes}

        :param int data_width: Specify the number of bytes wide each data
            point is. One of [1,2].
        
        :param str fmt: Format string as specified by the :mod:`struct` module,
            or `None` to choose a format automatically based on the data
            width.        
        '''
        #if(data_width not in [1,2]):
        #    print 'Error: Data width must be 1 or 2.'
        #    return 0
        # This needs to be a # symbol for valid binary block
        symbol = self._file.read(1)
        if(symbol != '#'): # Check to make sure block is valid
            raise IOError('Not a valid binary block start. Binary blocks '
                                'require the first character to be #.')
        else:
            # Read in the num of digits for next part
            digits = int(self._file.read(1))
            
            # Read in the num of bytes to be read
            num_of_bytes = int(self._file.read(digits))
            
            # Make or use the required format string.
            if fmt is None:
                fmt = _DEFAULT_FORMATS[data_width]
                
            # Read in the data bytes, and pass them to numpy using the specified
            # data type (format).
            return np.frombuffer(self._file.read(num_of_bytes), dtype=fmt)
            
    ## CLASS METHODS ##

    URI_SCHEMES = ['serial', 'tcpip', 'gpib+usb', 'gpib+serial', 'visa', 'file', 'usbtmc']
    
    @classmethod
    def open_from_uri(cls, uri):
        """
        Given an instrument URI, opens the instrument named by that URI.
        Instrument URIs are formatted with a scheme, such as ``serial://``,
        followed by a location that is interpreted differently for each
        scheme. The following examples URIs demonstrate the currently supported
        schemes and location formats::
        
            serial://COM3
            serial:///dev/ttyACM0
            tcpip://192.168.0.10:4100
            gpib+usb://COM3/15
            gpib+serial://COM3/15
            gpib+serial:///dev/ttyACM0/15 # Currently non-functional.
            visa://USB::0x0699::0x0401::C0000001::0::INSTR
            usbtmc://USB::0x0699::0x0401::C0000001::0::INSTR

        For the ``serial`` URI scheme, baud rates may be explicitly specified
        using the query parameter ``baud=``, as in the example
        ``serial://COM9?baud=115200``. If not specified, the baud rate
        is assumed to be 115200.
            
        :param str uri: URI for the instrument to be loaded.
        :rtype: `Instrument`
        
        .. seealso::
            `PySerial`_ documentation for serial port URI format
            
        .. _PySerial: http://pyserial.sourceforge.net/
        """
        # Make sure that urlparse knows that we want query strings.
        for scheme in cls.URI_SCHEMES:
            if scheme not in urlparse.uses_query:
                urlparse.uses_query.append(scheme)
        
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
            # We want to pass just the netloc and the path to PySerial,
            # sending the query string as kwargs. Thus, we should make the
            # device name here.
            dev_name = parsed_uri.netloc
            if parsed_uri.path:
                dev_name = os.path.join(dev_name, parsed_uri.path)

            # We should handle the baud rate separately, however, to ensure
            # that the default is set correctly and that the type is `int`,
            # as expected.
            if "baud" in kwargs:
                kwargs['baud'] = int(kwargs['baud'][0])
            else:
                kwargs['baud'] = 115200
                    
            return cls.open_serial(
                dev_name,
                **kwargs)
        elif parsed_uri.scheme == "tcpip":
            # Ex: tcpip://192.168.0.10:4100
            host, port = parsed_uri.netloc.split(":")
            port = int(port)
            return cls.open_tcpip(host, port, **kwargs)
        elif parsed_uri.scheme == "gpib+usb" or parsed_uri.scheme == "gpib+serial":
            # Ex: gpib+usb://COM3/15
            #     scheme="gpib+usb", netloc="COM3", path="/15"
            # Make a new device path by joining the netloc (if any)
            # with all but the last segment of the path.
            uri_head, uri_tail = os.path.split(parsed_uri.path)
            dev_path = os.path.join(parsed_uri.netloc, uri_head)
            return cls.open_gpibusb(
                dev_path,
                int(uri_tail),
                **kwargs)
        elif parsed_uri.scheme == "visa":
            # Ex: visa://USB::{VID}::{PID}::{SERIAL}::0::INSTR
            #     where {VID}, {PID} and {SERIAL} are to be replaced with
            #     the vendor ID, product ID and serial number of the USB-VISA
            #     device.
            return cls.open_visa(parsed_uri.netloc, **kwargs)
        elif parsed_uri.scheme == "usbtmc":
            # TODO: check for other kinds of usbtmc URLs.
            # Ex: usbtmc can take URIs exactly like visa://.
            return cls.open_visa(parsed_uri.netloc, **kwargs)
        elif parsed_uri.scheme == 'file':
            return cls.open_file(os.path.join(parsed_uri.netloc, 
                                               parsed_uri.path), **kwargs)
        else:
            raise NotImplementedError("Invalid scheme or not yet "
                                          "implemented.")
    
    @classmethod
    def open_tcpip(cls, host, port):
        """
        Opens an instrument, connecting via TCP/IP to a given host and TCP port.
        
        :param str host: Name or IP address of the instrument.
        :param int port: TCP port on which the insturment is listening.
        
        :rtype: `Instrument`
        :return: Object representing the connected instrument.
        
        .. seealso::
            `~socket.socket.connect` for description of `host` and `port`
            parameters in the TCP/IP address family.
        """
        conn = socket.socket()
        conn.connect((host, port))
        return cls(SocketWrapper(conn))
        
    @classmethod
    def open_serial(cls, port, baud, timeout=3, writeTimeout=3):
        """
        Opens an instrument, connecting via a physical or emulated serial port.
        Note that many instruments which connect via USB are exposed to the
        operating system as serial ports, so this method will very commonly
        be used for connecting instruments via USB.
        
        :param str port: Name of the the port or device file to open a
            connection on. For example, ``"COM10"`` on Windows or
            ``"/dev/ttyUSB0"`` on Linux.
        :param int baud: The baud rate at which instrument communicates.
        :param float timeout: Number of seconds to wait when reading from the
            instrument before timing out.
        :param float writeTimeout: Number of seconds to wait when writing to the
            instrument before timing out.
        
        :rtype: `Instrument`
        :return: Object representing the connected instrument.
        
        .. seealso::
            `~serial.Serial` for description of `port`, baud rates and timeouts.
        """
        ser = serialManager.newSerialConnection(port, 
                                     baud,
                                     timeout, 
                                     writeTimeout)
        return cls(ser)
    
    @classmethod
    def open_gpibusb(cls, port, gpib_address, timeout=3, writeTimeout=3):
        """
        Opens an instrument, connecting via a
        `Galvant Industries GPIB-USB adapter`_.
        
        :param str port: Name of the the port or device file to open a
            connection on. Note that because the GI GPIB-USB
            adapter identifies as a serial port to the operating system, this
            should be the name of a serial port.
        :param int gpib_address: Address on the connected GPIB bus assigned to
            the instrument.
        :param float timeout: Number of seconds to wait when reading from the
            instrument before timing out.
        :param float writeTimeout: Number of seconds to wait when writing to the
            instrument before timing out.
        
        :rtype: `Instrument`
        :return: Object representing the connected instrument.
        
        .. seealso::
            `~serial.Serial` for description of `port` and timeouts.
            
        .. _Galvant Industries GPIB-USB adapter: http://galvant.ca/shop/gpibusb/
        """
        ser = serialManager.newSerialConnection(port,
                timeout=timeout,
                 writeTimeout=writeTimeout)
        return cls(GPIBWrapper(ser, gpib_address))
        
    @classmethod
    def open_gpibethernet(cls, host, port, gpib_address):
        conn = socket.socket()
        conn.connect((host, port))
        return cls(GPIBWrapper(conn, gpib_address))

    @classmethod
    def open_visa(cls, resource_name):
        """
        Opens an instrument, connecting using the VISA library. Note that
        `PyVISA`_ and a VISA implementation must both be present and installed
        for this method to function.
        
        :param str resource_name: Name of a VISA resource representing the
            given instrument.
        
        :rtype: `Instrument`
        :return: Object representing the connected instrument.
        
        .. seealso::
            `National Instruments help page on VISA resource names
            <http://zone.ni.com/reference/en-XX/help/371361J-01/lvinstio/visa_resource_name_generic/>`_.
            
        .. _PyVISA: http://pyvisa.sourceforge.net/
        """
        if visa is None:
            raise ImportError("PyVISA is required for loading VISA "
                                "instruments.")
        ins = visa.instrument(resource_name)
        return cls(VisaWrapper(ins))

    @classmethod
    def open_test(cls, stdin=None, stdout=None):
        return cls(LoopbackWrapper(stdin, stdout))

    @classmethod
    def open_usbtmc(cls, *args, **kwargs):
        # TODO: docstring
        usbtmc_comm = USBTMCCommunicator(*args, **kwargs)
        return cls(usbtmc_comm)

    @classmethod
    def open_usb(cls, vid, pid):
        """
        Opens an instrument, connecting via a raw USB stream.
        
        .. note::
            Note that raw USB a very uncommon of connecting to instruments,
            even for those that are connected by USB. Most will identify as
            either serial ports (in which case,
            `~instruments.Instrument.open_serial` should be used), or as
            USB-TMC devices. On Linux, USB-TMC devices can be connected using
            `~instruments.Instrument.open_file`, provided that the ``usbtmc``
            kernel module is loaded. On Windows, some such devices can be opened
            using the VISA library and the `~instruments.Instrument.open_visa`
            method.
        
        :param str vid: Vendor ID of the USB device to open.
        :param int pid: Product ID of the USB device to open.
        
        :rtype: `Instrument`
        :return: Object representing the connected instrument.
        """
        if usb is None:
            raise ImportError("USB support not imported. Do you have PyUSB "
                                "version 1.0 or later?")

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

        return cls(USBWrapper(ep))
        
    @classmethod
    def open_file(cls, filename):
        """
        Given a file, treats that file as a character device file that can
        be read from and written to in order to communicate with the
        instrument. This may be the case, for instance, if the instrument
        is connected by the Linux ``usbtmc`` kernel driver.
        
        :param str filename: Name of the character device to open.
        
        :rtype: `Instrument`
        :return: Object representing the connected instrument.
        """
        return cls(FileCommunicator(filename))
