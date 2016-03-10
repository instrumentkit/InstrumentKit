#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides support for SCPI compliant function generators
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division

import quantities as pq

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
    >>> import quantities as pq
    >>> inst = ik.generic_scpi.SCPIFunctionGenerator.open_tcpip("192.168.1.1")
    >>> inst.frequency = 1 * pq.kHz
    """

    def __init__(self, filelike):
        super(SCPIFunctionGenerator, self).__init__(filelike)

    # CONSTANTS #

    _UNIT_MNEMONICS = {
        FunctionGenerator.VoltageMode.peak_to_peak: "VPP",
        FunctionGenerator.VoltageMode.rms:          "VRMS",
        FunctionGenerator.VoltageMode.dBm:          "DBM",
    }

    _MNEMONIC_UNITS = dict((mnem, unit)
                           for unit, mnem in _UNIT_MNEMONICS.items())

    # FunctionGenerator CONTRACT #

    def _get_amplitude_(self):
        """
        Gets the amplitude for a generic SCPI function generator

        :type: `tuple` containing `float` for value, and
            `FunctionGenerator.VoltageMode` for the type of measurement
            (eg VPP, VRMS, DBM).
        """
        units = self.query("VOLT:UNIT?").strip()

        return (
            float(self.query("VOLT?").strip()),
            self._MNEMONIC_UNITS[units]
        )

    def _set_amplitude_(self, magnitude, units):
        """
        Sets the amplitude for a generic SCPI function generator

        :param magnitude: Desired amplitude magnitude
        :type magnitude: `float`
        :param units: The type of voltage measurements units
        :type units: `FunctionGenerator.VoltageMode`
        """
        self.sendcmd("VOLT:UNIT {}".format(self._UNIT_MNEMONICS[units]))
        self.sendcmd("VOLT {}".format(magnitude))

    # PROPERTIES #

    frequency = unitful_property(
        name="FREQ",
        units=pq.Hz,
        doc="""
        Gets/sets the output frequency.

        :units: As specified, or assumed to be :math:`\\text{Hz}` otherwise.
        :type: `float` or `~quantities.quantity.Quantity`
        """
    )

    function = enum_property(
        name="FUNC",
        enum=lambda: Function,  # pylint: disable=undefined-variable
        doc="""
        Gets/sets the output function of the function generator

        :type: `SCPIFunctionGenerator.Function`
        """
    )

    offset = unitful_property(
        name="VOLT:OFFS",
        units=pq.volt,
        doc="""
        Gets/sets the offset voltage of the function generator.

        Set value should be within correct bounds of instrument.

        :units: As specified  (if a `~quntities.quantity.Quantity`) or assumed
            to be of units volts.
        :type: `~quantities.quantity.Quantity` with units volts.
        """
    )

    @property
    def phase(self):
        raise NotImplementedError

    @phase.setter
    def phase(self, newval):
        raise NotImplementedError
