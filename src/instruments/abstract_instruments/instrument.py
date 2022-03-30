#!/usr/bin/env python
"""
Provides the base Instrument class for all instruments.
"""

# IMPORTS #####################################################################


import os
import collections
import socket
import struct
import urllib.parse as parse

from serial import SerialException
from serial.tools.list_ports import comports
import pyvisa
import usb.core

from instruments.abstract_instruments.comm import (
    SocketCommunicator,
    USBCommunicator,
    VisaCommunicator,
    FileCommunicator,
    LoopbackCommunicator,
    GPIBCommunicator,
    AbstractCommunicator,
    USBTMCCommunicator,
    VXI11Communicator,
    serial_manager,
)
from instruments.optional_dep_finder import numpy
from instruments.errors import AcknowledgementError, PromptError

# CONSTANTS ###################################################################

_DEFAULT_FORMATS = collections.defaultdict(lambda: ">b")
_DEFAULT_FORMATS.update({1: ">b", 2: ">h", 4: ">i"})

# CLASSES #####################################################################


class Instrument:

    """
    This is the base instrument class from which all others are derived from.
    It provides the basic implementation for all communication related
    tasks. In addition, it also contains several class methods for opening
    connections via the supported hardware channels.
    """

    def __init__(self, filelike):
        # Check to make sure filelike is a subclass of AbstractCommunicator
        if isinstance(filelike, AbstractCommunicator):
            self._file = filelike
        else:
            raise TypeError(
                "Instrument must be initialized with a filelike "
                "object that is a subclass of "
                "AbstractCommunicator."
            )
        # Record if we're using the Loopback Communicator and put class in
        # testing mode so we can disable sleeps in class implementations
        self._testing = isinstance(self._file, LoopbackCommunicator)

        self._prompt = None
        self._terminator = "\n"

    # COMMAND-HANDLING METHODS #

    def _ack_expected(self, msg=""):  # pylint: disable=unused-argument,no-self-use
        return None

    def sendcmd(self, cmd):
        """
        Sends a command without waiting for a response.

        :param str cmd: String containing the command to
            be sent.
        """
        self._file.sendcmd(str(cmd))
        ack_expected_list = self._ack_expected(
            cmd
        )  # pylint: disable=assignment-from-none
        if not isinstance(ack_expected_list, (list, tuple)):
            ack_expected_list = [ack_expected_list]
        for ack_expected in ack_expected_list:
            if ack_expected is None:
                break
            ack = self.read()
            if ack != ack_expected:
                raise AcknowledgementError(
                    "Incorrect ACK message received: got {} "
                    "expected {}".format(ack, ack_expected)
                )
        if self.prompt is not None:
            prompt = self.read(len(self.prompt))
            if prompt != self.prompt:
                raise PromptError(
                    "Incorrect prompt message received: got {} "
                    "expected {}".format(prompt, self.prompt)
                )

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
        ack_expected_list = self._ack_expected(
            cmd
        )  # pylint: disable=assignment-from-none
        if not isinstance(ack_expected_list, (list, tuple)):
            ack_expected_list = [ack_expected_list]

        if ack_expected_list[0] is None:  # Case no ACK
            value = self._file.query(cmd, size)
        else:  # Case with ACKs
            _ = self._file.query(cmd, size=0)  # Send the cmd, don't read
            for ack_expected in ack_expected_list:  # Read and verify ACKs
                ack = self.read()
                if ack != ack_expected:
                    raise AcknowledgementError(
                        f"Incorrect ACK message received: got {ack} expected {ack_expected}"
                    )
            value = self.read(size)  # Now read in our return data
        if self.prompt is not None:
            prompt = self.read(len(self.prompt))
            if prompt != self.prompt:
                raise PromptError(
                    f"Incorrect prompt message received: got {prompt} expected {self.prompt}"
                )
        return value

    def read(self, size=-1, encoding="utf-8"):
        """
        Read the last line.

        :param int size: Number of bytes to be read. Default is read until
            termination character is found.
        :return: The result of the read as returned by the
            connected instrument.
        :rtype: `str`
        """
        return self._file.read(size, encoding)

    def read_raw(self, size=-1):
        """
        Read the raw last line.

        :param int size: Number of bytes to be read. Default is read until
            termination character is found.
        :return: The result of the read as returned by the
            connected instrument.
        :rtype: `str`
        """
        return self._file.read_raw(size)

    # PROPERTIES #

    @property
    def timeout(self):
        """
        Gets/sets the communication timeout for this instrument. Note that
        setting this value after opening the connection is not supported for
        all connection types.

        :type: `int`
        """
        return self._file.timeout

    @timeout.setter
    def timeout(self, newval):
        self._file.timeout = newval

    @property
    def address(self):
        """
        Gets/sets the target communication of the instrument.

        This is useful for situations when running straight from a Python shell
        and your instrument has enumerated with a different address. An example
        when this can happen is if you are using a USB to Serial adapter and
        you disconnect/reconnect it.

        :type: `int` for GPIB address, `str` for other
        """
        return self._file.address

    @address.setter
    def address(self, newval):
        self._file.address = newval

    @property
    def terminator(self):
        """
        Gets/sets the terminator used for communication.

        For communication options where this is applicable, the value
        corresponds to the ASCII character used for termination in decimal
        format. Example: 10 sets the character to NEWLINE.

        :type: `int`, or `str` for GPIB adapters.
        """
        return self._file.terminator

    @terminator.setter
    def terminator(self, newval):
        self._file.terminator = newval

    @property
    def prompt(self):
        """
        Gets/sets the prompt used for communication.

        The prompt refers to a character that is sent back from the instrument
        after it has finished processing your last command. Typically this is
        used to indicate to an end-user that the device is ready for input when
        connected to a serial-terminal interface.

        In IK, the prompt is specified that that it (and its associated
        termination character) are read in. The value read in from the device
        is also checked against the stored prompt value to make sure that
        everything is still in sync.

        :type: `str`
        """
        return self._prompt

    @prompt.setter
    def prompt(self, newval):
        self._prompt = newval

    # BASIC I/O METHODS #

    def write(self, msg):
        """
        Write data string to the connected instrument. This will call
        the write method for the attached filelike object. This will typically
        bypass attaching any termination characters or other communication
        channel related work.

        .. seealso:: `Instrument.sendcmd` if you wish to send a string to the
        instrument, while still having InstrumentKit handle termination
        characters and other communication channel related work.

        :param str msg: String that will be written to the filelike object
            (`Instrument._file`) attached to this instrument.
        """
        self._file.write(msg)

    def binblockread(self, data_width, fmt=None):
        """ "
        Read a binary data block from attached instrument.
        This requires that the instrument respond in a particular manner
        as EOL terminators naturally can not be used in binary transfers.

        The format is as follows:
        #{number of following digits:1-9}{num of bytes to be read}{data bytes}

        :param int data_width: Specify the number of bytes wide each data
            point is. One of [1,2,4].

        :param str fmt: Format string as specified by the :mod:`struct` module,
            or `None` to choose a format automatically based on the data
            width. Typically you can just specify `data_width` and leave this
            default.
        """
        # This needs to be a # symbol for valid binary block
        symbol = self._file.read_raw(1)
        if symbol != b"#":  # Check to make sure block is valid
            raise OSError(
                "Not a valid binary block start. Binary blocks "
                "require the first character to be #, instead got "
                "{}".format(symbol)
            )
        else:
            # Read in the num of digits for next part
            digits = int(self._file.read_raw(1))

            # Read in the num of bytes to be read
            num_of_bytes = int(self._file.read_raw(digits))

            # Make or use the required format string.
            if fmt is None:
                fmt = _DEFAULT_FORMATS[data_width]

            # Read in the data bytes, and pass them to numpy using the specified
            # data type (format).
            # This is looped in case a communication timeout occurs midway
            # through transfer and multiple reads are required
            tries = 3
            data = self._file.read_raw(num_of_bytes)
            while len(data) < num_of_bytes:
                old_len = len(data)
                data += self._file.read_raw(num_of_bytes - old_len)
                if old_len == len(data):
                    tries -= 1
                if tries == 0:
                    raise OSError(
                        "Did not read in the required number of bytes"
                        "during binblock read. Got {}, expected "
                        "{}".format(len(data), num_of_bytes)
                    )
            if numpy:
                return numpy.frombuffer(data, dtype=fmt)
            return struct.unpack(f"{fmt[0]}{int(len(data)/data_width)}{fmt[-1]}", data)

    # CLASS METHODS #

    URI_SCHEMES = [
        "serial",
        "tcpip",
        "gpib+usb",
        "gpib+serial",
        "visa",
        "file",
        "usbtmc",
        "vxi11",
        "test",
    ]

    @classmethod
    def open_from_uri(cls, uri):
        # pylint: disable=too-many-return-statements,too-many-branches
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
            test://

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
            if scheme not in parse.uses_query:
                parse.uses_query.append(scheme)

        # Break apart the URI using urlparse. This returns a named tuple whose
        # parts describe the incoming URI.
        parsed_uri = parse.urlparse(uri)

        # We always want the query string to provide keyword args to the
        # class method.
        # FIXME: This currently won't work, as everything is strings,
        #        but the other class methods expect ints or floats, depending.
        kwargs = parse.parse_qs(parsed_uri.query)
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
                kwargs["baud"] = int(kwargs["baud"][0])
            else:
                kwargs["baud"] = 115200

            return cls.open_serial(dev_name, **kwargs)
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
            return cls.open_gpibusb(dev_path, int(uri_tail), **kwargs)
        elif parsed_uri.scheme == "visa":
            # Ex: visa://USB::{VID}::{PID}::{SERIAL}::0::INSTR
            #     where {VID}, {PID} and {SERIAL} are to be replaced with
            #     the vendor ID, product ID and serial number of the USB-VISA
            #     device.
            return cls.open_visa(parsed_uri.netloc, **kwargs)
        elif parsed_uri.scheme == "usbtmc":
            # TODO: check for other kinds of usbtmc URLs.
            # Ex: usbtmc can take URIs exactly like visa://.
            return cls.open_usbtmc(parsed_uri.netloc, **kwargs)
        elif parsed_uri.scheme == "file":
            return cls.open_file(
                os.path.join(parsed_uri.netloc, parsed_uri.path), **kwargs
            )
        elif parsed_uri.scheme == "vxi11":
            # Examples:
            #   vxi11://192.168.1.104
            #   vxi11://TCPIP::192.168.1.105::gpib,5::INSTR
            return cls.open_vxi11(parsed_uri.netloc, **kwargs)
        elif parsed_uri.scheme == "test":
            return cls.open_test(**kwargs)
        else:
            raise NotImplementedError("Invalid scheme or not yet " "implemented.")

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
        return cls(SocketCommunicator(conn))

    # pylint: disable=too-many-arguments
    @classmethod
    def open_serial(
        cls,
        port=None,
        baud=9600,
        vid=None,
        pid=None,
        serial_number=None,
        timeout=3,
        write_timeout=3,
    ):
        """
        Opens an instrument, connecting via a physical or emulated serial port.
        Note that many instruments which connect via USB are exposed to the
        operating system as serial ports, so this method will very commonly
        be used for connecting instruments via USB.

        This method can be called by either supplying a port as a string,
        or by specifying vendor and product IDs, and an optional serial
        number (used when more than one device with the same IDs is
        attached). If both the port and IDs are supplied, the port will
        default to the supplied port string, else it will search the
        available com ports for a port matching the defined IDs and serial
        number.

        :param str port: Name of the the port or device file to open a
            connection on. For example, ``"COM10"`` on Windows or
            ``"/dev/ttyUSB0"`` on Linux.
        :param int baud: The baud rate at which instrument communicates.
        :param int vid: the USB port vendor id.
        :param int pid: the USB port product id.
        :param str serial_number: The USB port serial_number.
        :param float timeout: Number of seconds to wait when reading from the
            instrument before timing out.
        :param float write_timeout: Number of seconds to wait when writing to the
            instrument before timing out.

        :rtype: `Instrument`
        :return: Object representing the connected instrument.

        .. seealso::
            `~serial.Serial` for description of `port`, baud rates and timeouts.
        """
        if port is None and vid is None:
            raise ValueError(
                "One of port, or the USB VID/PID pair, must be " "specified when "
            )
        if port is not None and vid is not None:
            raise ValueError(
                "Cannot specify both a specific port, and a USB" "VID/PID pair."
            )
        if (vid is not None and pid is None) or (pid is not None and vid is None):
            raise ValueError(
                "Both VID and PID must be specified when opening"
                "a serial connection via a USB VID/PID pair."
            )

        if port is None:
            match_count = 0
            for _port in comports():
                # If no match on vid/pid, go to next comport
                if not _port.pid == pid or not _port.vid == vid:
                    continue
                # If we specified a serial num, verify then break
                if serial_number is not None and _port.serial_number == serial_number:
                    port = _port.device
                    break
                # If no provided serial number, match, but also keep a count
                if serial_number is None:
                    port = _port.device
                    match_count += 1
                # If we found more than 1 vid/pid device, but no serial number,
                # raise an exception due to ambiguity
                if match_count > 1:
                    raise SerialException(
                        "Found more than one matching serial " "port from VID/PID pair"
                    )

        # if the port is still None after that, raise an error.
        if port is None and vid is not None:
            err_msg = (
                "Could not find a port with the attributes vid: {vid}, "
                "pid: {pid}, serial number: {serial_number}"
            )
            raise ValueError(
                err_msg.format(
                    vid=vid,
                    pid=pid,
                    serial_number="any" if serial_number is None else serial_number,
                )
            )

        ser = serial_manager.new_serial_connection(
            port, baud=baud, timeout=timeout, write_timeout=write_timeout
        )
        return cls(ser)

    @classmethod
    def open_gpibusb(cls, port, gpib_address, timeout=3, write_timeout=3, model="gi"):
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
        :param float write_timeout: Number of seconds to wait when writing to the
            instrument before timing out.
        :param str model: The brand of adapter to be connected to. Currently supported
            is "gi" for Galvant Industries, and "pl" for Prologix LLC.

        :rtype: `Instrument`
        :return: Object representing the connected instrument.

        .. seealso::
            `~serial.Serial` for description of `port` and timeouts.

        .. _Galvant Industries GPIB-USB adapter: galvant.ca/#!/store/gpibusb
        """
        ser = serial_manager.new_serial_connection(
            port, baud=460800, timeout=timeout, write_timeout=write_timeout
        )
        return cls(GPIBCommunicator(ser, gpib_address, model))

    @classmethod
    def open_gpibethernet(cls, host, port, gpib_address, model="pl"):
        """
        Opens an instrument, connecting via a Prologix GPIBETHERNET adapter.

        :param str host: Name or IP address of the instrument.
        :param int port: TCP port on which the insturment is listening.
        :param int gpib_address: Address on the connected GPIB bus assigned to
            the instrument.
        :param str model: The brand of adapter to be connected to. Currently supported
            is "gi" for Galvant Industries, and "pl" for Prologix LLC.

        .. warning:: This function has been setup for use with the Prologix
            GPIBETHERNET adapter but has not been tested as confirmed working.
        """
        conn = socket.socket()
        conn.connect((host, port))
        return cls(GPIBCommunicator(conn, gpib_address, model))

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
        version = list(map(int, pyvisa.__version__.split(".")))
        while len(version) < 3:
            version += [0]
        if version[0] >= 1 and version[1] >= 6:
            ins = pyvisa.ResourceManager().open_resource(resource_name)
        else:
            ins = pyvisa.instrument(resource_name)  # pylint: disable=no-member
        return cls(VisaCommunicator(ins))

    @classmethod
    def open_test(cls, stdin=None, stdout=None):
        """
        Opens an instrument using a loopback communicator for a test
        connection. The primary use case of this is to instantiate a specific
        instrument class without requiring an actual physical connection
        of any kind. This is also very useful for creating unit tests through
        the parameters of this class method.

        :param stdin: The stream of data coming from the instrument
        :type stdin: `io.BytesIO` or `None`
        :param stdout: Empty data stream that will hold data sent from the
            Python class to the loopback communicator. This can then be checked
            for the contents.
        :type stdout: `io.BytesIO` or `None`
        :return: Object representing the virtually-connected instrument
        """
        return cls(LoopbackCommunicator(stdin, stdout))

    @classmethod
    def open_usbtmc(cls, *args, **kwargs):
        """
        Opens an instrument, connecting to a USB-TMC device using the Python
        `usbtmc` library.

        .. warning:: The operational status of this is unknown. It is suggested
            that you connect via the other provided class methods. For Linux,
            if you have the ``usbtmc`` kernel module, the
            `~instruments.Instrument.open_file` class method will work. On
            Windows, using the `~instruments.Instrument.open_visa` class
            method along with having the VISA libraries installed will work.

        :return: Object representing the connected instrument
        """
        usbtmc_comm = USBTMCCommunicator(*args, **kwargs)
        return cls(usbtmc_comm)

    @classmethod
    def open_vxi11(cls, *args, **kwargs):
        """
        Opens a vxi11 enabled instrument, connecting using the python
        library `python-vxi11`_. This package must be present and installed
        for this method to function.

        :rtype: `Instrument`
        :return: Object representing the connected instrument.

        .. _python-vxi11: https://github.com/python-ivi/python-vxi11
        """
        vxi11_comm = VXI11Communicator(*args, **kwargs)
        return cls(vxi11_comm)

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
        :param str pid: Product ID of the USB device to open.

        :rtype: `Instrument`
        :return: Object representing the connected instrument.
        """
        dev = usb.core.find(idVendor=vid, idProduct=pid)
        if dev is None:
            raise OSError("No such device found.")

        return cls(USBCommunicator(dev))

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
