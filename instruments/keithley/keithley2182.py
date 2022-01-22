#!/usr/bin/env python
"""
Driver for the Keithley 2182 nano-voltmeter
"""

# IMPORTS #####################################################################

from enum import Enum

from instruments.abstract_instruments import Multimeter
from instruments.generic_scpi import SCPIMultimeter
from instruments.optional_dep_finder import numpy
from instruments.units import ureg as u
from instruments.util_fns import ProxyList

# CLASSES #####################################################################


class Keithley2182(SCPIMultimeter):

    """
    The Keithley 2182 is a nano-voltmeter. You can find the full specifications
    list in the `user's guide`_.

    Example usage:

    >>> import instruments as ik
    >>> meter = ik.keithley.Keithley2182.open_gpibusb("/dev/ttyUSB0", 10)
    >>> print(meter.measure(meter.Mode.voltage_dc))


    """

    # INNER CLASSES #

    class Channel(Multimeter):
        """
        Class representing a channel on the Keithley 2182 nano-voltmeter.

        .. warning:: This class should NOT be manually created by the user. It
            is designed to be initialized by the `Keithley2182` class.
        """

        # pylint: disable=super-init-not-called
        def __init__(self, parent, idx):
            self._parent = parent
            self._idx = idx + 1

        # PROPERTIES #

        @property
        def mode(self):
            return Keithley2182.Mode(self._parent.query("SENS:FUNC?"))

        @mode.setter
        def mode(self, newval):
            raise NotImplementedError

        @property
        def trigger_mode(self):
            raise NotImplementedError

        @trigger_mode.setter
        def trigger_mode(self, newval):
            raise NotImplementedError

        @property
        def relative(self):
            raise NotImplementedError

        @relative.setter
        def relative(self, newval):
            raise NotImplementedError

        @property
        def input_range(self):
            raise NotImplementedError

        @input_range.setter
        def input_range(self, newval):
            raise NotImplementedError

        # METHODS #

        def measure(self, mode=None):
            """
            Performs a measurement of the specified channel. If no mode
            parameter is specified then the current mode is used.

            :param mode: Mode that the measurement will be performed in
            :type mode: Keithley2182.Mode
            :return: The value of the measurement
            :rtype: `~pint.Quantity`
            """
            if mode is not None:
                # self.mode = mode
                raise NotImplementedError
            self._parent.sendcmd(f"SENS:CHAN {self._idx}")
            value = float(self._parent.query("SENS:DATA:FRES?"))
            unit = self._parent.units
            return u.Quantity(value, unit)

    # ENUMS #

    class Mode(Enum):
        """
        Enum containing valid measurement modes for the Keithley 2182
        """

        voltage_dc = "VOLT"
        temperature = "TEMP"

    class TriggerMode(Enum):
        """
        Enum containing valid trigger modes for the Keithley 2182
        """

        immediate = "IMM"
        external = "EXT"
        bus = "BUS"
        timer = "TIM"
        manual = "MAN"

    # PROPERTIES #

    @property
    def channel(self):
        """
        Gets a specific Keithley 2182 channel object. The desired channel is
        specified like one would access a list.

        Although not default, the 2182 has up to two channels.

        For example, the following would print the measurement from channel 1:

        >>> meter = ik.keithley.Keithley2182.open_gpibusb("/dev/ttyUSB0", 10)
        >>> print meter.channel[0].measure()

        :rtype: `Keithley2182.Channel`
        """
        return ProxyList(self, Keithley2182.Channel, range(2))

    @property
    def relative(self):
        """
        Gets/sets the relative measurement function of the Keithley 2182.

        This is used to enable or disable the relative function for the
        currently set mode. When enabling, the current reading is used as a
        baseline which is subtracted from future measurements.

        If relative is already on, the stored value is refreshed with the
        currently read value.

        See the manual for more information.

        :type: `bool`
        """
        mode = self.channel[0].mode
        return self.query(f"SENS:{mode.value}:CHAN1:REF:STAT?") == "ON"

    @relative.setter
    def relative(self, newval):
        if not isinstance(newval, bool):
            raise TypeError("Relative mode must be a boolean.")
        mode = self.channel[0].mode
        if self.relative:
            self.sendcmd(f"SENS:{mode.value}:CHAN1:REF:ACQ")
        else:
            newval = "ON" if newval is True else "OFF"
            self.sendcmd(f"SENS:{mode.value}:CHAN1:REF:STAT {newval}")

    @property
    def input_range(self):
        raise NotImplementedError

    @input_range.setter
    def input_range(self, newval):
        raise NotImplementedError

    @property
    def units(self):
        """
        Gets the current measurement units of the instrument.

        :rtype: `~pint.Unit`
        """
        mode = self.channel[0].mode
        if mode == Keithley2182.Mode.voltage_dc:
            return u.volt
        unit = self.query("UNIT:TEMP?")
        if unit == "C":
            unit = u.celsius
        elif unit == "K":
            unit = u.kelvin
        elif unit == "F":
            unit = u.fahrenheit
        else:
            raise ValueError("Unknown temperature units.")
        return unit

    # METHODS #

    def fetch(self):
        """
        Transfer readings from instrument memory to the output buffer, and thus
        to the computer.
        If currently taking a reading, the instrument will wait until it is
        complete before executing this command.
        Readings are NOT erased from memory when using fetch. Use the ``R?``
        command to read and erase data.
        Note that the data is transfered as ASCII, and thus it is not
        recommended to transfer a large number of data points using GPIB.

        :return: Measurement readings from the instrument output buffer.
        :rtype: `tuple`[`~pint.Quantity`, ...]
            or if numpy is installed, `~pint.Quantity` with `numpy.array` data
        """
        data = list(map(float, self.query("FETC?").split(",")))
        unit = self.units
        if numpy:
            return data * unit
        return tuple(d * unit for d in data)

    def measure(self, mode=None):
        """
        Perform and transfer a measurement of the desired type.

        :param mode: Desired measurement mode. If left at default the
            measurement will occur with the current mode.
        :type: `Keithley2182.Mode`

        :return: Returns a single shot measurement of the specified mode.
        :rtype: `~pint.Quantity`
        :units: Volts, Celsius, Kelvin, or Fahrenheit
        """
        if mode is None:
            mode = self.channel[0].mode
        if not isinstance(mode, Keithley2182.Mode):
            raise TypeError(
                "Mode must be specified as a Keithley2182.Mode "
                "value, got {} instead.".format(mode)
            )
        value = float(self.query(f"MEAS:{mode.value}?"))
        unit = self.units
        return value * unit
