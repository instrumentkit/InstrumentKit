#!/usr/bin/env python
"""Support for Comet Cito Plus RF generator."""

# IMPORTS #####################################################################

from enum import IntEnum
from typing import Union

import serial

from instruments.abstract_instruments import Instrument
from instruments.units import ureg as u
from instruments.util_fns import assume_units

# CLASSES #####################################################################


class CitoPlus1310(Instrument):
    """Communicate with the Comet Cito Plus 1310 RF generator.

    Various connection options are available for different models.
    Note that this driver is only tested with the RS-232 interface
    and that, according to the manual, communication over TCP/IP is
    different.

    Example:
        >>> import instruments as ik
        >>> port = '/dev/ttyUSB0'
        >>> baud = 15200
        >>> inst = ik.comet.CitoPlus1310.open_serial(port, baud)
        >>> inst.rf  # query RF state
        False
        >>> inst.rf = True  # turn on RF
    """

    class RegulationMode(IntEnum):
        """Regulation modes that are available on the Cito Plus 1310."""

        ForwardPower = 0
        LoadPower = 1
        ProcessControl = 2

    def __init__(self, filelike):
        super().__init__(filelike)
        self._file.parity = serial.PARITY_EVEN

        self._address = 0x0A

        self._exception_codes = {
            0x01: "Unknown parameter or illegal function code",
            0x04: "Value invalid",
            0x05: "Parameter not writable",
            0x06: "Parameter not readable",
            0x07: "Stop",
            0x08: "Not allowed",
            0x09: "Wrong data type",
            0x0A: "Internal error",
            0x0B: "Value too high",
            0x0C: "Value too low",
        }

        self._byte_order = "big"  # byte order for command and data
        self._byte_order_crc = "little"  # byte order for CRC-16 checksum

    @property
    def name(self) -> str:
        """Get the name of the instrument."""
        data = self.query(self._make_pkg(10))
        return data.decode("utf-8")

    @property
    def forward_power(self) -> u.Quantity:
        """Get the actual forward power of the generator in W.

        :return: Forward power.
        :rtype: Quantity
        """
        data = self.query(self._make_pkg(8021))
        data = int.from_bytes(data, byteorder=self._byte_order)
        return assume_units(data, u.mW).to(u.W)

    @property
    def load_power(self) -> u.Quantity:
        """Get the actual load power of the generator in W.

        :return: Load power.
        :rtype: Quantity
        """
        data = self.query(self._make_pkg(8023))
        data = int.from_bytes(data, byteorder=self._byte_order)
        return assume_units(data, u.mW).to(u.W)

    @property
    def output_power(self) -> u.Quantity:
        """Get/set the set output power of the generator in W.

        :return: Output power.
        :rtype: Quantity
        """
        data = self.query(self._make_pkg(1206))
        data = int.from_bytes(data, byteorder=self._byte_order)
        return assume_units(data, u.mW).to(u.W)

    @output_power.setter
    def output_power(self, value: u.Quantity) -> None:
        value = assume_units(value, u.W).to(u.mW)
        if value < 1 * u.W:
            value = 0 * u.W  # instrument can't set anything lower
        value = int(value.magnitude)
        self.sendcmd(self._make_pkg(1206, value))

    @property
    def reflected_power(self) -> u.Quantity:
        """Get the actual reflected power of the generator in W.

        :return: Reflected power.
        :rtype: Quantity
        """
        data = self.query(self._make_pkg(8022))
        data = int.from_bytes(data, byteorder=self._byte_order)
        return assume_units(data, u.mW).to(u.W)

    @property
    def regulation_mode(self) -> RegulationMode:
        """Get/set the regulation mode of the generator.

        :return: Regulation mode.
        :rtype: RegulationMode
        """
        data = self.query(self._make_pkg(1201))
        return self.RegulationMode(int.from_bytes(data, byteorder=self._byte_order))

    @regulation_mode.setter
    def regulation_mode(self, value) -> None:
        self.sendcmd(self._make_pkg(1201, value.value))

    @property
    def rf(self) -> bool:
        """Get/set the RF state.

        :return: The RF state.
        :rtype: bool
        """
        data = self.query(self._make_pkg(8000))
        return int.from_bytes(data, byteorder=self._byte_order) != 1

    @rf.setter
    def rf(self, value: bool) -> None:
        data = 1 if value else 0
        self.sendcmd(self._make_pkg(1001, data))

    def sendcmd(self, pkg: bytes) -> None:
        """Write a command to the instrument.

        Uses the query command to check return, i.e., that everything is fine,
        but does not return data.

        :param bytes pkg: The package to send to the instrument.
        """
        self.query(pkg, write_cmd=True)

    def query(self, pkg: bytes, write_cmd=False) -> Union[None, bytes]:
        """Query instrument.

        This will check if the command is accepted by the instrument and if not,
        raise an OSError with the appropriate return code that came back.

        :param bytes pkg: The package to send to the instrument.
        :param boolwrite_cmd: If True, this is a write command and will only check
                if received package the same as sent one.
        """
        self._file.write_raw(pkg)

        hdr = self._file.read_raw(2)
        fn_code = hdr[1]

        if fn_code != 0x41 and fn_code != 0x42:
            exc_code = self._file.read_raw(1)[0]
            self._check_exception(fn_code, exc_code)

        if write_cmd:
            # read the rest, make sure the packages agree and if not raise OSError.
            len_to_read = len(pkg) - 2
            rest = self._file.read_raw(len_to_read)
            pkg_return = hdr + rest
            if pkg_return != pkg:
                raise OSError("Received package does not match sent package.")
            return

        # so it is a query and we expect data
        data_length = self._file.read_raw(1)
        data = self._file.read_raw(
            int.from_bytes(data_length, byteorder=self._byte_order)
        )
        crc = self._file.read_raw(2)

        crc_exp = _crc16(hdr + data_length + data).to_bytes(
            2, byteorder=self._byte_order_crc
        )

        if crc != crc_exp:
            raise OSError("CRC-16 checksum of returned package does not match.")

        return data

    def _check_exception(self, fn_code: int, exc_code: int) -> None:
        """Checks if the function code is an exception and raises an OSError if so.

        :param int fn_code: The function code.
        :param int exc_code: The exception code.

        :raises OSError: If the function code is an exception.
        """
        if fn_code != 0x41 or fn_code != 0x42:
            raise OSError(
                f"Exception code: {hex(exc_code)}: {self._exception_codes.get(exc_code, 'Unknown')}"
            )

    def _make_hdr(self, fn_code: int) -> bytes:
        """Make the header according to our init settings.

        :param int fn_code: The function code to use.

        :return: The header bytes.
        :rtype: bytes
        """
        hdr = bytes([self._address, fn_code])
        return hdr

    def _make_pkg(self, cmd_code, data=None, data_length=4):
        """Create a package to send to the instrument.

        :param int cmd_code: The command code.
        :param data: The data to send. If None, this is a read command. Defaults to None.
        :param int data_length: The length of the data in bytes. Only used when writing.

        :return: Properly packed data to send to the instrument.
        :rtype: bytes
        """
        if data is None:
            fn_code = 0x41
        else:
            fn_code = 0x42

        hdr = self._make_hdr(fn_code)

        cmd = cmd_code.to_bytes(length=2, byteorder=self._byte_order)

        if data is not None:
            dat = data.to_bytes(length=data_length, byteorder=self._byte_order)
        else:
            dat = (0x01).to_bytes(length=2, byteorder=self._byte_order)

        pkg = hdr + cmd + dat
        crc = _crc16(pkg)
        crc_bytes = crc.to_bytes(2, byteorder=self._byte_order_crc)

        return pkg + crc_bytes


def _crc16(data: bytes):
    """Create the CRC-16 checksum for the given data.

    :param bytes data: The data for which to create the checksum.

    :return: The CRC-16 checksum.
    :rtype: int
    """
    crc16tab = [
        0x0000,
        0xC0C1,
        0xC181,
        0x0140,
        0xC301,
        0x03C0,
        0x0280,
        0xC241,
        0xC601,
        0x06C0,
        0x0780,
        0xC741,
        0x0500,
        0xC5C1,
        0xC481,
        0x0440,
        0xCC01,
        0x0CC0,
        0x0D80,
        0xCD41,
        0x0F00,
        0xCFC1,
        0xCE81,
        0x0E40,
        0x0A00,
        0xCAC1,
        0xCB81,
        0x0B40,
        0xC901,
        0x09C0,
        0x0880,
        0xC841,
        0xD801,
        0x18C0,
        0x1980,
        0xD941,
        0x1B00,
        0xDBC1,
        0xDA81,
        0x1A40,
        0x1E00,
        0xDEC1,
        0xDF81,
        0x1F40,
        0xDD01,
        0x1DC0,
        0x1C80,
        0xDC41,
        0x1400,
        0xD4C1,
        0xD581,
        0x1540,
        0xD701,
        0x17C0,
        0x1680,
        0xD641,
        0xD201,
        0x12C0,
        0x1380,
        0xD341,
        0x1100,
        0xD1C1,
        0xD081,
        0x1040,
        0xF001,
        0x30C0,
        0x3180,
        0xF141,
        0x3300,
        0xF3C1,
        0xF281,
        0x3240,
        0x3600,
        0xF6C1,
        0xF781,
        0x3740,
        0xF501,
        0x35C0,
        0x3480,
        0xF441,
        0x3C00,
        0xFCC1,
        0xFD81,
        0x3D40,
        0xFF01,
        0x3FC0,
        0x3E80,
        0xFE41,
        0xFA01,
        0x3AC0,
        0x3B80,
        0xFB41,
        0x3900,
        0xF9C1,
        0xF881,
        0x3840,
        0x2800,
        0xE8C1,
        0xE981,
        0x2940,
        0xEB01,
        0x2BC0,
        0x2A80,
        0xEA41,
        0xEE01,
        0x2EC0,
        0x2F80,
        0xEF41,
        0x2D00,
        0xEDC1,
        0xEC81,
        0x2C40,
        0xE401,
        0x24C0,
        0x2580,
        0xE541,
        0x2700,
        0xE7C1,
        0xE681,
        0x2640,
        0x2200,
        0xE2C1,
        0xE381,
        0x2340,
        0xE101,
        0x21C0,
        0x2080,
        0xE041,
        0xA001,
        0x60C0,
        0x6180,
        0xA141,
        0x6300,
        0xA3C1,
        0xA281,
        0x6240,
        0x6600,
        0xA6C1,
        0xA781,
        0x6740,
        0xA501,
        0x65C0,
        0x6480,
        0xA441,
        0x6C00,
        0xACC1,
        0xAD81,
        0x6D40,
        0xAF01,
        0x6FC0,
        0x6E80,
        0xAE41,
        0xAA01,
        0x6AC0,
        0x6B80,
        0xAB41,
        0x6900,
        0xA9C1,
        0xA881,
        0x6840,
        0x7800,
        0xB8C1,
        0xB981,
        0x7940,
        0xBB01,
        0x7BC0,
        0x7A80,
        0xBA41,
        0xBE01,
        0x7EC0,
        0x7F80,
        0xBF41,
        0x7D00,
        0xBDC1,
        0xBC81,
        0x7C40,
        0xB401,
        0x74C0,
        0x7580,
        0xB541,
        0x7700,
        0xB7C1,
        0xB681,
        0x7640,
        0x7200,
        0xB2C1,
        0xB381,
        0x7340,
        0xB101,
        0x71C0,
        0x7080,
        0xB041,
        0x5000,
        0x90C1,
        0x9181,
        0x5140,
        0x9301,
        0x53C0,
        0x5280,
        0x9241,
        0x9601,
        0x56C0,
        0x5780,
        0x9741,
        0x5500,
        0x95C1,
        0x9481,
        0x5440,
        0x9C01,
        0x5CC0,
        0x5D80,
        0x9D41,
        0x5F00,
        0x9FC1,
        0x9E81,
        0x5E40,
        0x5A00,
        0x9AC1,
        0x9B81,
        0x5B40,
        0x9901,
        0x59C0,
        0x5880,
        0x9841,
        0x8801,
        0x48C0,
        0x4980,
        0x8941,
        0x4B00,
        0x8BC1,
        0x8A81,
        0x4A40,
        0x4E00,
        0x8EC1,
        0x8F81,
        0x4F40,
        0x8D01,
        0x4DC0,
        0x4C80,
        0x8C41,
        0x4400,
        0x84C1,
        0x8581,
        0x4540,
        0x8701,
        0x47C0,
        0x4680,
        0x8641,
        0x8201,
        0x42C0,
        0x4380,
        0x8341,
        0x4100,
        0x81C1,
        0x8081,
        0x4040,
    ]
    crc = 0
    for dat in data:
        tmp = (0xFF & crc) ^ dat  # only last 16 bits of `crc`!
        crc = (crc >> 8) ^ crc16tab[tmp]
    return crc
