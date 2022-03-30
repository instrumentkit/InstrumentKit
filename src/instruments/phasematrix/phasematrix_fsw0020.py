#!/usr/bin/env python
"""
Provides support for the Phase Matrix FSW0020 signal generator.
"""

# IMPORTS #####################################################################


from instruments.abstract_instruments.signal_generator import SingleChannelSG
from instruments.units import ureg as u
from instruments.util_fns import assume_units

# CLASSES #####################################################################


class PhaseMatrixFSW0020(SingleChannelSG):

    """
    Communicates with a Phase Matrix FSW-0020 signal generator via the
    "Native SPI" protocol, supported on all FSW firmware versions.

    Example::

        >>> import instruments as ik
        >>> import instruments.units as u
        >>> inst = ik.phasematrix.PhaseMatrixFSW0020.open_serial("/dev/ttyUSB0", baud=115200)
        >>> inst.frequency = 1 * u.GHz
        >>> inst.power = 0 * ik.units.dBm  # Can omit units and will assume dBm
        >>> inst.output = True
    """

    def reset(self):
        r"""
        Causes the connected signal generator to perform a hardware reset.
        Note that no commands will be accepted by the generator for at least
        :math:`5 \mu\text{s}`.
        """
        self.sendcmd("0E.")

    @property
    def frequency(self):
        """
        Gets/sets the output frequency of the signal generator.
        If units are not specified, the frequency is assumed
        to be in gigahertz (GHz).

        :type: `~pint.Quantity`
        :units: frequency, assumed to be GHz
        """
        return (int(self.query("04."), 16) * u.mHz).to(u.GHz)

    @frequency.setter
    def frequency(self, newval):
        # Rescale the input to millihertz as demanded by the signal
        # generator, then convert to an integer.
        newval = int(assume_units(newval, u.GHz).to(u.mHz).magnitude)

        # Write the integer to the serial port in ASCII-encoded
        # uppercase-hexadecimal format, with padding to 12 nybbles.
        self.sendcmd(f"0C{newval:012X}.")

        # No return data, so no readline needed.

    @property
    def power(self):
        """
        Gets/sets the output power of the signal generator.
        If units are not specified, the power is assumed to be in
        decibel-milliwatts (dBm).

        :type: `~pint.Quantity`
        :units: log-power, assumed to be dBm
        """
        return u.Quantity((int(self.query("0D."), 16)), u.cBm).to(u.dBm)

    @power.setter
    def power(self, newval):
        # TODO: convert UnitPower Quantity instances to UnitLogPower.
        #       That is, convert [W] to [dBm].

        # The Phase Matrix unit speaks in units of centibel-milliwats,
        # so convert and take the integer part.
        newval = int(assume_units(newval, u.dBm).to(u.cBm).magnitude)

        # Command code 0x03, parameter length 2 bytes (4 nybbles)
        self.sendcmd(f"03{newval:04X}.")

    @property
    def phase(self):
        raise NotImplementedError

    @phase.setter
    def phase(self, newval):
        raise NotImplementedError

    @property
    def blanking(self):
        """
        Gets/sets the blanking status of the FSW0020

        :type: `bool`
        """
        raise NotImplementedError

    @blanking.setter
    def blanking(self, newval):
        self.sendcmd(f"05{1 if newval else 0:02X}.")

    @property
    def ref_output(self):
        """
        Gets/sets the reference output status of the FSW0020

        :type: `bool`
        """
        raise NotImplementedError

    @ref_output.setter
    def ref_output(self, newval):
        self.sendcmd(f"08{1 if newval else 0:02X}.")

    @property
    def output(self):
        """
        Gets/sets the channel output status of the FSW0020. Setting this
        property to `True` will turn the output on.

        :type: `bool`
        """
        raise NotImplementedError

    @output.setter
    def output(self, newval):
        self.sendcmd(f"0F{1 if newval else 0:02X}.")

    @property
    def pulse_modulation(self):
        """
        Gets/sets the pulse modulation status of the FSW0020

        :type: `bool`
        """
        raise NotImplementedError

    @pulse_modulation.setter
    def pulse_modulation(self, newval):
        self.sendcmd(f"09{1 if newval else 0:02X}.")

    @property
    def am_modulation(self):
        """
        Gets/sets the amplitude modulation status of the FSW0020

        :type: `bool`
        """
        raise NotImplementedError

    @am_modulation.setter
    def am_modulation(self, newval):
        self.sendcmd(f"0A{1 if newval else 0:02X}.")
