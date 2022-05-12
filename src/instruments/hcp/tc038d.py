#!/usr/bin/env python
"""
Provides support for the TC038 AC crystal oven by HC Photonics.
"""


# IMPORTS #####################################################################


from instruments.units import ureg as u

from instruments.abstract_instruments.instrument import Instrument
from instruments.util_fns import assume_units


# CLASSES #####################################################################


class TC038D(Instrument):
    """
    Communication with the HCP TC038D oven.

    This is the newer version with DC heating.

    The temperature controller is on default set to modbus communication.
    The oven expects raw bytes written, no ascii code, and sends raw bytes.
    For the variables are two or four-byte modes available. We use the
    four-byte mode addresses, so do we. In that case element count has to be
    double the variables read.
    """

    functions = {'read': 0x03, 'writeMultiple': 0x10,
                 'writeSingle': 0x06, 'echo': 0x08}

    def __init__(self, *args, **kwargs):
        """
        The TC038 is a crystal oven.

        Example usage:

        >>> import instruments as ik
        >>> import instruments.units as u
        >>> inst = ik.hcp.TC038.open_visa('TCPIP0:192.168.0.35')
        >>> inst.setpoint = 45.3
        >>> print(inst.temperature)
        """
        super().__init__(*args, **kwargs)
        self.addr = 1

    def CRC16(self, data):
        """Calculate the CRC16 checksum for the data byte array."""
        CRC = 0xFFFF
        for octet in data:
            CRC ^= octet
            for j in range(8):
                lsb = CRC & 0x1  # least significant bit
                CRC = CRC >> 1
                if lsb:
                    CRC ^= 0xA001
        return [CRC & 0xFF, CRC >> 8]

    def readRegister(self, address, count=2):
        """Read count variables from start address on."""
        # Count has to be double the number of elements in 4-byte-mode.
        data = [self.addr]
        data.append(0x03)  # function code
        data += [address >> 8, address & 0xFF]  # 2B address
        data += [count >> 8, count & 0xFF]  # 2B number of elements
        data += self.CRC16(data)
        self._file.write_raw(bytes(data))
        got = self.read_raw(3)
        # Slave address, function, length
        if got[1] == 0x03:
            length = got[2]
            read = self.read_raw(length + 2)
            # data, CRC
            return read[:-2]
        else:  # an error occurred
            end = self.read_raw(2)  # empty the buffer
            if got[2] == 0x02:
                raise ValueError("The read start address is incorrect.")
            if got[2] == 0x03:
                raise ValueError("The number of elements exceeds the allowed range")
            raise ConnectionError(f"Unknown read error. Received: {got} {end}")

    def writeMultiple(self, address, values, byteMode=4):
        """Write multiple variables."""
        data = [self.addr]
        data.append(0x10)  # function code
        data += [address >> 8, address & 0xFF]  # 2B address
        if isinstance(values, int):
            data += [0x0, byteMode // 2]  # 2B number of elements
            data.append(byteMode)  # 1B number of write data
            for i in range(byteMode - 1, -1, -1):
                data.append(values >> i * 8 & 0xFF)
        elif hasattr(values, "__iter__"):
            elements = len(values) * byteMode // 2
            data += [elements >> 8, elements & 0xFF]  # 2B number of elements
            data.append(len(values) * byteMode)  # 1B number byte count
            for element in values:
                for i in range(byteMode - 1, -1, -1):
                    data.append(element >> i * 8 & 0xFF)
        else:
            raise ValueError(("Values has to be an integer or an iterable of "
                              f"integers. values: {values}"))
        data += self.CRC16(data)
        self._file.write_raw(bytes(data))
        got = self.read_raw(2)
        # slave address, function
        if got[1] == 0x10:
            return self.read_raw(2 + 2 + 2)
            # start address, number elements, CRC
        else:
            end = self.read_raw(3)  # error code and CRC
            errors = {0x02: "Wrong start address",
                      0x03: "Variable data error",
                      0x04: "Operation error"}
            raise ValueError(errors[end[0]])

    @property
    def setpoint(self):
        """Get the current setpoint in °C."""
        value = int.from_bytes(self.readRegister(0x106), byteorder='big') / 10
        return u.Quantity(value, u.degC)

    @setpoint.setter
    def setpoint(self, value):
        """Set the setpoint in °C."""
        number = assume_units(value, u.degC).to(u.degC).magnitude
        value = int(round(value.to('degC').magnitude * 10, 0))
        self.writeMultiple(0x106, int(round(number * 10)))

    @property
    def temperature(self):
        """Get the current temperature in °C."""
        value = int.from_bytes(self.readRegister(0x0), byteorder='big') / 10
        return u.Quantity(value, u.degC)
