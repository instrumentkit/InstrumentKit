#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides support for the SRS 345 function generator.
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division

from enum import IntEnum

import quantities as pq

from instruments.abstract_instruments import FunctionGenerator
from instruments.generic_scpi import SCPIInstrument
from instruments.util_fns import enum_property, unitful_property

# CLASSES #####################################################################


class SRS345(SCPIInstrument, FunctionGenerator):

    """
    The SRS DS345 is a 30MHz function generator.

    Example usage:

    >>> import instruments as ik
    >>> import quantities as pq
    >>> srs = ik.srs.SRS345.open_gpib('/dev/ttyUSB0', 1)
    >>> srs.frequency = 1 * pq.MHz
    >>> print(srs.offset)
    >>> srs.function = srs.Function.triangle
    """
    # FIXME: need to add OUTX 1 here, but doing so seems to cause a syntax
    #        error on the instrument.

    # CONSTANTS #

    _UNIT_MNEMONICS = {
        FunctionGenerator.VoltageMode.peak_to_peak: "VP",
        FunctionGenerator.VoltageMode.rms:          "VR",
        FunctionGenerator.VoltageMode.dBm:          "DB",
    }

    _MNEMONIC_UNITS = dict((mnem, unit)
                           for unit, mnem in _UNIT_MNEMONICS.items())

    # FunctionGenerator CONTRACT #

    def _get_amplitude_(self):
        resp = self.query("AMPL?").strip()

        return (
            float(resp[:-2]),
            self._MNEMONIC_UNITS[resp[-2:]]
        )

    def _set_amplitude_(self, magnitude, units):
        self.sendcmd(
            "AMPL {}{}".format(magnitude, self._UNIT_MNEMONICS[units]))

    # ENUMS ##

    class Function(IntEnum):
        """
        Enum containing valid output function modes for the SRS 345
        """
        sinusoid = 0
        square = 1
        triangle = 2
        ramp = 3
        noise = 4
        arbitrary = 5

    # PROPERTIES ##

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
        enum=Function,
        input_decoration=int,
        doc="""
        Gets/sets the output function of the function generator.

        :type: `~SRS345.Function`
        """
    )

    offset = unitful_property(
        name="OFFS",
        units=pq.volt,
        doc="""
        Gets/sets the offset voltage for the output waveform.

        :units: As specified, or assumed to be :math:`\\text{V}` otherwise.
        :type: `float` or `~quantities.quantity.Quantity`
        """
    )

    phase = unitful_property(
        name="PHSE",
        units=pq.degree,
        doc="""
        Gets/sets the phase for the output waveform.

        :units: As specified, or assumed to be degrees (:math:`{}^{\\circ}`)
            otherwise.
        :type: `float` or `~quantities.quantity.Quantity`
        """
    )
