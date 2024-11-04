"""Support for Dressler Cesar 1312 RF generator."""

# IMPORTS #####################################################################

from enum import IntEnum
from typing import List, Tuple, Union

import serial

from instruments.abstract_instruments import Instrument
from instruments.units import ureg as u
from instruments.util_fns import assume_units

# CLASSES #####################################################################


class Cesar1312(Instrument):
    """Communicate with the Dressler Cesar 1312 RF generator.

    Various connection options are available for different models.
    This driver has been tested using the RS-232 option.
    Upon initialization, the instrument is automatically put into
    odd parity communication mode (as required by the device).

    Note that you must set the control mode to `ControlMode.Host`
    in order to send any commands from the computer to the device.

    Example:
        >>> import serial
        >>> import instruments as ik
        >>> port = '/dev/ttyUSB0'
        >>> baud = 115200
        >>> inst = ik.dressler.Cesar1312.open_serial(port, baud)
        >>> inst.control_mode = inst.ControlMode.Host
        >>> inst.rf  # query RF state
        False
        >>> inst.rf = True  # turn on RF
    """

    class ControlMode(IntEnum):
        """Control modes of the Cesar 1312 RF generator."""

        Host = 2
        UserPort = 4
        FrontPanel = 6

    class RegulationMode(IntEnum):
        """Regulation modes of the Cesar 1312 RF generator."""

        ForwardPower = 6
        LoadPower = 7
        ExternalPower = 8

    def __init__(self, filelike):
        super().__init__(filelike)

        self._file.parity = serial.PARITY_ODD

        self._retries = 3

        self._csr_codes = {
            0: "OK",
            1: "Command rejected because unit is in wrong control mode.",
            2: "Command rejected because RF output is on.",
            4: "Command rejected because data sent is out of range.",
            5: "Command rejected because User Port RF signal is off.",
            7: "Command rejected because active fault(s) exist in generator.",
            9: "Command rejected because the data byte count is incorrect.",
            19: "Command rejected because the recipe mode is active",
            50: "Command rejected because the frequency is out of range.",
            51: "Command rejected because the duty cycle is out of range.",
            99: "Command not implemented.",
        }
        self._address = 0x01
        self._ack = bytes([0x06])
        self._nak = bytes([0x15])

    # CLASS PROPERTIES #

    @property
    def address(self) -> int:
        """Set/get the address of the device.

        Note that an address of 0 is the broadcast address.
        Most likely, you can leave this at the default of 1.

        :return: The set address.
        :rtype: int
        """
        return self._address

    @address.setter
    def address(self, value: int) -> None:
        if value < 0 or value > 31:
            raise ValueError("Address must be in the range 0-31.")
        self._address = value

    @property
    def retries(self) -> int:
        """Set/get the number of retries if a command fails.

        :return: The number of retries as an integer.
        :rtype: int
        """
        return self._retries

    @retries.setter
    def retries(self, value: int) -> Tuple[int, int, bytes]:
        if value < 0:
            raise ValueError("Retries must be greater than or equal to 0.")
        self._retries = value

    # INSTRUMENT PROPERTIES #

    @property
    def control_mode(self) -> ControlMode:
        """Set/get the active control of the RF generator.

        Possible values are given in the `ControlMode` enum. For computer
        control, you likely want to set this to `ControlMode.Host`.

        ..note:: If you set the control mode at any time back to
            `ControlMode.FrontPanel`, the RF will turn off.

        :return: The current control mode.
        :rtype: ControlMode

        Example:
            >>> inst.control_mode = ik.dressler.Cesar1312.ControlMode.Host
            >>> inst.control_mode
            <ControlMode.Host: 2>
        """
        data = self.query(self._make_pkg(155))
        return self.ControlMode(data[0])

    @control_mode.setter
    def control_mode(self, value: ControlMode) -> None:
        self.sendcmd(self._make_pkg(14, self._make_data(1, value.value)))

    @property
    def name(self) -> str:
        """Get the supply type and size of the RF generator.

        :return: The supply type and size.
        :rtype: str

        Example:
            >>> inst.name
            'CESAR_1312'
        """
        name_type = self.query(self._make_pkg(128)).decode("utf-8")
        name_size = self.query(self._make_pkg(129)).decode("utf-8")
        return f"{name_type}{name_size}"

    @property
    def output_power(self) -> u.Quantity:
        """Set/get the output power of the device in W.

        :return: The output power in W for the defined mode.
        :rtype: u.Quantity

        Example:
            >>> inst.output_power = 10 * u.W
            >>> inst.output_power
            <Quantity(10, 'watt')>
        """
        ret_data = self.query(self._make_pkg(164))[:2]
        return u.Quantity(int.from_bytes(ret_data, "little"), u.W)

    @output_power.setter
    def output_power(self, value: u.Quantity) -> None:
        value = assume_units(value, u.W).to(u.W)
        data = self._make_data(2, int(value.magnitude))
        self.sendcmd(self._make_pkg(8, data))

    @property
    def reflected_power(self) -> u.Quantity:
        """Get the reflected power in W.

        :return: The reflected power in W.
        :rtype: u.Quantity

        Example:
            >>> inst.reflected_power
            <Quantity(0, 'watt')>
        """
        ret_data = self.query(self._make_pkg(166))
        return u.Quantity(int.from_bytes(ret_data, "little"), u.W)

    @property
    def regulation_mode(self) -> RegulationMode:
        """Set/get the regulation mode.

        Possible values are given in the `RegulationMode` enum.

        :return: The current regulation mode.
        :rtype: RegulationMode

        Example:
            >>> inst.regulation_mode = ik.dressler.Cesar1312.RegulationMode.ForwardPower
            >>> inst.regulation_mode
            <RegulationMode.ForwardPower: 6>
        """
        data = self.query(self._make_pkg(154))
        return self.RegulationMode(data[0])

    @regulation_mode.setter
    def regulation_mode(self, value: RegulationMode) -> None:
        self.sendcmd(self._make_pkg(3, self._make_data(1, value.value)))

    @property
    def rf(self) -> bool:
        """Set/get the RF output state of the device.

        RF on will be `True` while RF off will be `False`.

        :return: The current RF state.
        :rtype: bool

        Example:
            >>> inst.rf = True
            >>> inst.rf
            True
        """
        data = self.query(self._make_pkg(162))
        return bool(data[0] & 0b00100000)

    @rf.setter
    def rf(self, value: bool) -> None:
        cmd = 2 if value else 1
        self.sendcmd(self._make_pkg(cmd))

    # METHODS #

    def query(self, package: bytes, len_data=1) -> bytes:
        """Send a package to the instrument, assert it's all good, and return answer.

        This sends the package and checks the response. If the response is NAK,
        it retries until an ACK is received or the number of retries is reached.

        Once an ACK is received, it listens for the response of the instrument
        parsed the header, command, and optinally the data length (if > 6),
        then listens to the data and checksum and ensures that the overallc hecksum
        is zero. If not, it will send a NAK and retry reading until the checksum is
        zero. Then it will send an ACK to finish the communication.

        :param bytes package: The package to send.

        :return: The data received from the device.
        :rtype: bytes
        """
        tries = 0
        got_ack = False
        while tries < self.retries + 1:
            self._file.write_raw(package)
            response = self.read_raw(1)
            if response == self._ack:
                got_ack = True
                break
            else:
                tries += 1

        if not got_ack:
            raise OSError("Failed to get ACK from device after sending the command.")

        tries = 0
        got_pkg = False
        while tries < self.retries:
            header = self.read_raw(1)
            cmd = self.read_raw(1)

            adr, dlength = self._unpack_header(header)

            optional_data_length = None
            if dlength == 0b111:
                optional_data_length = self.read_raw(1)
                dlength = int(optional_data_length.hex(), 16)

            data = self.read_raw(dlength) if dlength > 0 else None

            checksum = self.read_raw(1)

            pkg = header + cmd
            if optional_data_length:
                pkg += optional_data_length

            if data:
                pkg += data
            pkg += checksum

            if self._calculate_checksum(pkg) == bytes([0x0]):
                self._file.write_raw(self._ack)
                got_pkg = True
                break
            else:
                tries += 1
                self._file.write_raw(self._nak)

        if not got_pkg:
            raise OSError("Failed to get a valid package from the device.")

        return data

    def sendcmd(self, pkg: bytes) -> None:
        """Send a package to the instrument and assert it's all good.

        Uses the query routine and interprets the data, which should be one byte,
        as a CSR. If the CSR is not OK (0), will print a warning with the message.

        :param bytes pkg: The package to send.
        """
        data = self.query(pkg)
        if data:
            csr = int(data.hex(), 16)
            if csr != 0:
                raise OSError(
                    f"{self._csr_codes.get(csr, 'Unknown error')} (CSR={csr})"
                )
        else:
            raise ValueError("No data received from the device.")

    def _make_data(
        self, length: Union[int, List[int]], data: Union[int, List[int]]
    ) -> bytes:
        """Create the data bytes for the package.

        If only one number is given, provide the length and the actual value as integers (or list).
        If more than one number is given, provide both as lists.

        :param Union[int, list[int]] length: The length of the data.
        :param Union[int, list[int]] data: The data to send.

        :return: Data in appropriate order.
        :rtype: bytes
        """
        if isinstance(length, int):
            length = [length]
        if isinstance(data, int):
            data = [data]

        data_bytes = b""
        for ll, dd in zip(length, data):
            data_bytes += dd.to_bytes(ll, byteorder="little", signed=False)

        return data_bytes

    def _make_pkg(self, cmd_number: int, data: Union[None, bytes] = None) -> bytes:
        """Make a package and return it packed as bytes.

        :param int cmd_number: The command number.
        :param bytes data: The data to send, already in proper order as bytes, or None.
            Defaults to None, which makes it a query command.
        """
        data_length = len(data) if data else 0

        header = self._pack_header(data_length)

        if data_length > 255:
            raise ValueError("Data length too long, must be <= 255.")

        if cmd_number > 255:
            raise ValueError("Command number too long, must be <= 255.")

        if data_length > 6:
            pkg = [header, cmd_number, data_length]
        else:
            pkg = [header, cmd_number]

        pkg = bytes(pkg)
        if data is not None:
            pkg += data

        pkg = pkg + self._calculate_checksum(pkg)
        return pkg

    @staticmethod
    def _calculate_checksum(data: bytes) -> bytes:
        """Calculate the checksum of the data.

        :param bytes data: The data to calculate the checksum for.

        :return: Checksum.
        :rtype: bytes
        """
        checksum = data[0]
        for it, bt in enumerate(data):
            if it > 0:
                checksum ^= bt
        return bytes([checksum])

    def _pack_header(self, data_length: int):
        """Make the header of the package.

        :param int data_length: The length of the data. If > 6, will be set to 7.

        :return: The header as an integer.
        """
        if data_length > 6:
            data_length = 7  # need an extra byte for data length
        return (self._address << 3) + data_length

    @staticmethod
    def _unpack_header(hdr: bytes) -> Tuple[int]:
        """Parse the header and return address and data length.

        :param bytes hdr: The header byte.

        :return: The address and data length as integers.
        :rtype: tuple[int]
        """
        addr = hdr[0] >> 3
        data_length = hdr[0] & 0b00000111
        return addr, data_length
