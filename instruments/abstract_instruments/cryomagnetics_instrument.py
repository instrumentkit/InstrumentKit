# -*- codingL utf-8 -*-
"""
Extends the instrument class, and overwrites `Instrument.open_serial`, in order
to use the `CryomagneticsSerialCommunicator`. This needs to be done because
Cryomagnetics Instruments are special.
"""

# IMPORTS #####################################################################

from serial.tools.list_ports import comports
from serial import SerialException
from instruments.abstract_instruments.comm import (
    CryomagneticsSerialCommunicator, serial_manager
)

from instruments.abstract_instruments.instrument import Instrument

# CLASSES #####################################################################


class CryomagneticsInstrument(Instrument):
    """
    Base class for Cryomagnetics Instruments
    """

    def __init__(self, filelike):
        Instrument.__init__(self, filelike)

    @classmethod
    def open_serial(cls, port=None, baud=9600, vid=None, pid=None,
                    serial_number=None, timeout=3, write_timeout=3):
        """
        Opens an instrument, connecting via physical or emulated serial ports.
        This method is expected to be used wherever `Instrument.open_serial` is
        used, however, it returns `CryomagneticsSerialCommunicator` instead of
        `SerialCommunicator`

        :param str port: Name of the the port or device file to open a
            connection on. For example, ``"COM10"`` on Windows or
            ``"/dev/ttyUSB0"`` on Linux.
        :param int baud: The baud rate at which instrument communicates.
        :param int vid: the USB port vendor id.
        :param int pid: the USB port product id.
        :param str serial_number: The USB port serial_number.
        :param float timeout: Number of seconds to wait when reading from the
            instrument before timing out.
        :param float write_timeout: Number of seconds to wait when writing to
            the instrument before timing out.

        :rtype: `Instrument`
        :return: Object representing the connected instrument.

        .. seealso::
            `~serial.Serial` for description of `port`, baud rates and
            timeouts.
        """
        if port is None and vid is None:
            raise ValueError("One of port, or the USB VID/PID pair, must be "
                             "specified when ")
        if port is not None and vid is not None:
            raise ValueError("Cannot specify both a specific port, and a USB"
                             "VID/PID pair.")
        if (vid is not None and pid is None) or (pid is not None and vid is None):
            raise ValueError("Both VID and PID must be specified when opening"
                             "a serial connection via a USB VID/PID pair.")

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
                    raise SerialException("Found more than one matching serial "
                                          "port from VID/PID pair")

        # if the port is still None after that, raise an error.
        if port is None and vid is not None:
            err_msg = "Could not find a port with the attributes vid: {vid}, " \
                      "pid: {pid}, serial number: {serial_number}"
            raise ValueError(
                err_msg.format(
                    vid=vid,
                    pid=pid,
                    serial_number="any" if serial_number is None else serial_number
                )
            )

        ser = serial_manager.new_serial_connection(
            port,
            baud=baud,
            timeout=timeout,
            write_timeout=write_timeout,
            communicator_type=CryomagneticsSerialCommunicator
        )
        return cls(ser)
