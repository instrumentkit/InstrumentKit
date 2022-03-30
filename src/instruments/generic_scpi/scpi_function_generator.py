#!/usr/bin/env python
"""
Provides support for SCPI compliant function generators
"""

# IMPORTS #####################################################################


from instruments.units import ureg as u

from instruments.abstract_instruments import FunctionGenerator
from instruments.generic_scpi import SCPIInstrument
from instruments.util_fns import enum_property, unitful_property

# CLASSES #####################################################################


class SCPIFunctionGenerator(FunctionGenerator, SCPIInstrument):

    """
    This class is used for communicating with generic SCPI-compliant
    function generators.

    Example usage:

    >>> import instruments as ik
    >>> import instruments.units as u
    >>> inst = ik.generic_scpi.SCPIFunctionGenerator.open_tcpip("192.168.1.1")
    >>> inst.frequency = 1 * u.kHz
    """

    # CONSTANTS #

    _UNIT_MNEMONICS = {
        FunctionGenerator.VoltageMode.peak_to_peak: "VPP",
        FunctionGenerator.VoltageMode.rms: "VRMS",
        FunctionGenerator.VoltageMode.dBm: "DBM",
    }

    _MNEMONIC_UNITS = {mnem: unit for unit, mnem in _UNIT_MNEMONICS.items()}

    # FunctionGenerator CONTRACT #

    def _get_amplitude_(self):
        """
        Gets the amplitude for a generic SCPI function generator

        :type: `tuple` containing `float` for value, and
            `FunctionGenerator.VoltageMode` for the type of measurement
            (eg VPP, VRMS, DBM).
        """
        units = self.query("VOLT:UNIT?").strip()

        return (float(self.query("VOLT?").strip()), self._MNEMONIC_UNITS[units])

    def _set_amplitude_(self, magnitude, units):
        """
        Sets the amplitude for a generic SCPI function generator

        :param magnitude: Desired amplitude magnitude
        :type magnitude: `float`
        :param units: The type of voltage measurements units
        :type units: `FunctionGenerator.VoltageMode`
        """
        self.sendcmd(f"VOLT:UNIT {self._UNIT_MNEMONICS[units]}")
        self.sendcmd(f"VOLT {magnitude}")

    # PROPERTIES #

    frequency = unitful_property(
        command="FREQ",
        units=u.Hz,
        doc="""
        Gets/sets the output frequency.

        :units: As specified, or assumed to be :math:`\\text{Hz}` otherwise.
        :type: `float` or `~pint.Quantity`
        """,
    )

    function = enum_property(
        command="FUNC",
        enum=FunctionGenerator.Function,
        doc="""
        Gets/sets the output function of the function generator

        :type: `SCPIFunctionGenerator.Function`
        """,
    )

    offset = unitful_property(
        command="VOLT:OFFS",
        units=u.volt,
        doc="""
        Gets/sets the offset voltage of the function generator.

        Set value should be within correct bounds of instrument.

        :units: As specified  (if a `~pint.Quantity`) or assumed
            to be of units volts.
        :type: `~pint.Quantity` with units volts.
        """,
    )

    @property
    def phase(self):
        raise NotImplementedError

    @phase.setter
    def phase(self, newval):
        raise NotImplementedError
