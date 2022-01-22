#!/usr/bin/env python
"""
Provides a communication layer for an instrument connected via a Galvant
Industries or Prologix GPIB adapter.
"""

# IMPORTS #####################################################################


from enum import Enum
import io
import time

from instruments.units import ureg as u

from instruments.abstract_instruments.comm import AbstractCommunicator
from instruments.util_fns import assume_units

# CLASSES #####################################################################


class GPIBCommunicator(io.IOBase, AbstractCommunicator):

    """
    Communicates with a SocketCommunicator or SerialCommunicator object for
    use with Galvant Industries or Prologix GPIBUSB or GPIBETHERNET adapters.

    It essentially wraps those physical communication layers with the extra
    overhead required by the GPIB adapters.
    """

    # pylint: disable=too-many-instance-attributes
    def __init__(self, filelike, gpib_address, model="gi"):
        super().__init__(self)
        self._model = self.Model(model)
        self._file = filelike
        self._gpib_address = gpib_address
        self._file.terminator = "\r"
        if self._model == GPIBCommunicator.Model.gi:
            self._version = int(self._file.query("+ver"))
        if self._model == GPIBCommunicator.Model.pl:
            self._file.sendcmd("++auto 0")
        self._terminator = None
        self.terminator = "\n"
        self._eoi = True
        self._timeout = 1000 * u.millisecond
        if self._model == GPIBCommunicator.Model.gi and self._version <= 4:
            self._eos = 10
        else:
            self._eos = "\n"

    # ENUMS #

    class Model(Enum):
        """
        Enum containing the supported GPIB controller models
        """

        #: Galvant Industries
        gi = "gi"
        #: Prologix, LLC
        pl = "pl"

    # PROPERTIES #

    @property
    def address(self):
        """
        Gets/sets the GPIB address and downstream address associated with
        the instrument.

        When setting, if specified as an integer, only changes the GPIB
        address. If specified as a list, the first element changes the GPIB
        address, while the second is passed downstream.

        Example: [<int>gpib_address, downstream_address]

        Where downstream_address needs to be formatted as appropriate for the
        connection (eg SerialCommunicator, SocketCommunicator, etc).
        """
        return self._gpib_address, self._file.address

    @address.setter
    def address(self, newval):
        if isinstance(newval, int):
            if (newval < 1) or (newval > 30):
                raise ValueError("GPIB address must be between 1 and 30.")
            self._gpib_address = newval
        elif isinstance(newval, list):
            self.address = newval[0]  # Set GPIB address
            self._file.address = newval[1]  # Send downstream address
        else:
            raise TypeError("Not a valid input type for Instrument address.")

    @property
    def timeout(self):
        """
        Gets/sets the timeeout of both the GPIB bus and the connection
        channel between the PC and the GPIB adapter.

        :type: `~pint.Quantity`
        :units: As specified, or assumed to be of units ``seconds``
        """
        return self._timeout

    @timeout.setter
    def timeout(self, newval):
        newval = assume_units(newval, u.second)
        if self._model == GPIBCommunicator.Model.gi and self._version <= 4:
            newval = newval.to(u.second)
            self._file.sendcmd(f"+t:{int(newval.magnitude)}")
        else:
            newval = newval.to(u.millisecond)
            self._file.sendcmd(f"++read_tmo_ms {int(newval.magnitude)}")
        self._file.timeout = newval.to(u.second)
        self._timeout = newval.to(u.second)

    @property
    def terminator(self):
        """
        Gets/sets the GPIB termination character. This can be set to
        ``\n``, ``\r``, ``\r\n``, or ``eoi``.

        .. seealso:: `eos` and `eoi` for direct manipulation of these
            parameters.

        :type: `str`
        """
        if not self._eoi:
            return self._terminator

        return "eoi"

    @terminator.setter
    def terminator(self, newval):
        if isinstance(newval, bytes):
            newval = newval.decode("utf-8")
        if isinstance(newval, str):
            newval = newval.lower()

        if self._model == GPIBCommunicator.Model.gi and self._version <= 4:
            if newval == "eoi":
                self.eoi = True
            elif not isinstance(newval, int):
                if len(newval) == 1:
                    newval = ord(newval)
                    self.eoi = False
                    self.eos = newval
                else:
                    raise TypeError(
                        "GPIB termination must be integer 0-255 "
                        "represending decimal value of ASCII "
                        "termination character or a string"
                        'containing "eoi".'
                    )
            elif (newval < 0) or (newval > 255):
                raise ValueError(
                    "GPIB termination must be integer 0-255 "
                    "represending decimal value of ASCII "
                    "termination character."
                )
            else:
                self.eoi = False
                self.eos = newval
                self._terminator = chr(newval)
        else:
            if newval != "eoi":
                self.eos = newval
                self.eoi = False
                self._terminator = self.eos
            elif newval == "eoi":
                self.eos = None
                self._terminator = "eoi"
                self.eoi = True

    @property
    def eoi(self):
        """
        Gets/sets the EOI usage status.

        EOI is a dedicated line on the GPIB bus. When used, it is used by
        instruments to signal that the current byte being transmitted is the
        last in the message. This avoids the need to use a dedicated
        termination character such as ``\n``. Frequently, instruments will
        use both EOI-signalling and append an end-of-string (EOS) character.
        Some will only use one or the other.

        .. seealso:: `terminator`, `eos` for more communication termination
            related properties.

        :type: `bool`
        """
        return self._eoi

    @eoi.setter
    def eoi(self, newval):
        if not isinstance(newval, bool):
            raise TypeError("EOI status must be specified as a boolean")
        self._eoi = newval
        if self._model == GPIBCommunicator.Model.gi and self._version <= 4:
            self._file.sendcmd("+eoi:{}".format("1" if newval else "0"))
        else:
            self._file.sendcmd("++eoi {}".format("1" if newval else "0"))

    @property
    def eos(self):
        """
        Gets/sets the end-of-string (EOS) character.

        Valid EOS settings are ``\n``, ``\r``, ``\r\n`` and `None`.

        .. seealso:: `terminator`, `eoi` for more communication termination
            related properties.

        :type: `str` or `None`
        """
        return self._eos

    @eos.setter
    def eos(self, newval):
        if self._model == GPIBCommunicator.Model.gi and self._version <= 4:
            if isinstance(newval, (str, bytes)):
                newval = ord(newval)
            self._file.sendcmd(f"+eos:{newval}")
            self._eos = newval
        else:
            if isinstance(newval, int):
                newval = str(chr(newval))
            if newval == "\r\n":
                self._eos = newval
                newval = 0
            elif newval == "\r":
                self._eos = newval
                newval = 1
            elif newval == "\n":
                self._eos = newval
                newval = 2
            elif newval is None:
                self._eos = newval
                newval = 3
            else:
                raise ValueError("EOS must be CRLF, CR, LF, or None")
            self._file.sendcmd(f"++eos {newval}")

    # FILE-LIKE METHODS #

    def close(self):
        """
        Close connection to the underlying physical connection channel
        of the GPIB connection. This is typically a serial connection that
        is then closed.
        """
        self._file.close()

    def read_raw(self, size=-1):
        """
        Read bytes in from the gpibusb connection.

        :param int size: The number of bytes to read in from the
            connection.

        :return: The read bytes from the connection
        :rtype: `bytes`
        """
        return self._file.read_raw(size)

    def read(self, size=-1, encoding="utf-8"):
        """
        Read characters from wrapped class (ie SocketCommunicator or
        SerialCommunicator).

        If size = -1, characters will be read until termination character
        is found.

        GI GPIB adapters always terminate serial connections with a CR.
        Function will read until a CR is found.

        :param int size: Number of bytes to read
        :param str encoding: Encoding that will be applied to the read bytes

        :return: Data read from the GPIB adapter
        :rtype: `str`
        """
        return self._file.read(size, encoding)

    def write_raw(self, msg):
        """
        Write bytes to the gpibusb connection.

        :param bytes msg: Bytes to be sent to the instrument over the
            connection.
        """
        self._file.write_raw(msg)

    def write(self, msg, encoding="utf-8"):
        """
        Write data string to GPIB connected instrument.

        :param str msg: String to write to the instrument
        :param str encoding: Encoding to apply on msg to convert the message
            into bytes
        """
        self._file.write(msg, encoding)

    def flush_input(self):
        """
        Instruct the communicator to flush the input buffer, discarding the
        entirety of its contents.
        """
        self._file.flush_input()

    # METHODS #

    def _sendcmd(self, msg):
        """
        This is the implementation of ``sendcmd`` for communicating with
        the GPIB adapters. This function is in turn wrapped by the concrete
        method `AbstractCommunicator.sendcmd` to provide consistent
        logging functionality across all communication layers.

        :param str msg: The command message to send to the instrument
        """
        sleep_time = 0.01

        if msg == "":
            return
        if self._model == GPIBCommunicator.Model.gi:
            self._file.sendcmd(f"+a:{str(self._gpib_address)}")
        else:
            self._file.sendcmd(f"++addr {str(self._gpib_address)}")
        time.sleep(sleep_time)
        self.eoi = self.eoi
        time.sleep(sleep_time)
        self.timeout = self.timeout
        time.sleep(sleep_time)
        self.eos = self.eos
        time.sleep(sleep_time)
        self._file.sendcmd(msg)
        time.sleep(sleep_time)

    def _query(self, msg, size=-1):
        """
        This is the implementation of ``query`` for communicating with
        the GPIB adapters. This function is in turn wrapped by the concrete
        method `AbstractCommunicator.query` to provide consistent
        logging functionality across all communication layers.

        The Galvant Industries adaptor is set to automatically get a
        response if a ``?`` is present in ``msg``. If it is not present,
        then the adapter will be instructed to get the response from the
        instrument via the ``+read`` command.

        The Prologix adapter is set to not get a response unless told to do
        so. It is instructed to get a response from the instrument via the
        ``++read`` command.

        :param str msg: The query message to send to the instrument
        :param int size: The number of bytes to read back from the instrument
            response.
        :return: The instrument response to the query
        :rtype: `str`
        """
        self.sendcmd(msg)
        if self._model == GPIBCommunicator.Model.gi and "?" not in msg:
            self._file.sendcmd("+read")
        if self._model == GPIBCommunicator.Model.pl:
            self._file.sendcmd("++read")
        return self._file.read(size).strip()
