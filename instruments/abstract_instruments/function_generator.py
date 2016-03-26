#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides an abstract base class for function generator instruments
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division

import abc
from enum import Enum

from future.utils import with_metaclass
import quantities as pq


from instruments.abstract_instruments import Instrument
import instruments.units as u
from instruments.util_fns import assume_units

# CLASSES #####################################################################


class FunctionGenerator(with_metaclass(abc.ABCMeta, Instrument)):

    """
    Abstract base class for function generator instruments.

    All applicable concrete instruments should inherit from this ABC to
    provide a consistent interface to the user.
    """

    # ENUMS #

    class VoltageMode(Enum):
        """
        Enum containing valid voltage modes for many function generators
        """
        peak_to_peak = 'VPP'
        rms = 'VRMS'
        dBm = 'DBM'

    class Function(Enum):
        """
        Enum containg valid output function modes for many function generators
        """
        sinusoid = 'SIN'
        square = 'SQU'
        triangle = 'TRI'
        ramp = 'RAMP'
        noise = 'NOIS'
        arbitrary = 'ARB'

    # ABSTRACT METHODS #

    @abc.abstractmethod
    def _get_amplitude_(self):
        pass

    @abc.abstractmethod
    def _set_amplitude_(self, magnitude, units):
        pass

    # ABSTRACT PROPERTIES #

    @property
    @abc.abstractmethod
    def frequency(self):
        """
        Gets/sets the the output frequency of the function generator. This is
        an abstract property.

        :type: `~quantities.Quantity`
        """
        pass

    @frequency.setter
    @abc.abstractmethod
    def frequency(self, newval):
        pass

    @property
    @abc.abstractmethod
    def function(self):
        """
        Gets/sets the output function mode of the function generator. This is
        an abstract property.

        :type: `~enum.Enum`
        """
        pass

    @function.setter
    @abc.abstractmethod
    def function(self, newval):
        pass

    @property
    @abc.abstractmethod
    def offset(self):
        """
        Gets/sets the output offset voltage of the function generator. This is
        an abstract property.

        :type: `~quantities.Quantity`
        """
        pass

    @offset.setter
    @abc.abstractmethod
    def offset(self, newval):
        pass

    @property
    @abc.abstractmethod
    def phase(self):
        """
        Gets/sets the output phase of the function generator. This is an
        abstract property.

        :type: `~quantities.Quantity`
        """
        pass

    @phase.setter
    @abc.abstractmethod
    def phase(self, newval):
        pass

    # CONCRETE PROPERTIES #

    @property
    def amplitude(self):
        """
        Gets/sets the output amplitude of the function generator.

        If set with units of :math:`\\text{dBm}`, then no voltage mode can
        be passed.

        If set with units of :math:`\\text{V}` as a `~quantities.Quantity` or a
        `float` without a voltage mode, then the voltage mode is assumed to be
        peak-to-peak.

        :units: As specified, or assumed to be :math:`\\text{V}` if not
            specified.
        :type: Either a `tuple` of a `~quantities.Quantity` and a
            `FunctionGenerator.VoltageMode`, or a `~quantities.Quantity`
            if no voltage mode applies.
        """
        mag, units = self._get_amplitude_()

        if units == self.VoltageMode.dBm:
            return pq.Quantity(mag, u.dBm)
        else:
            return pq.Quantity(mag, pq.V), units

    @amplitude.setter
    def amplitude(self, newval):
        # Try and rescale to dBm... if it succeeds, set the magnitude
        # and units accordingly, otherwise handle as a voltage.
        try:
            newval_dbm = newval.rescale(u.dBm)
            mag = float(newval_dbm.magnitude)
            units = self.VoltageMode.dBm
        except (AttributeError, ValueError):
            # OK, we have volts. Now, do we have a tuple? If not, assume Vpp.
            if not isinstance(newval, tuple):
                mag = newval
                # pylint: disable=redefined-variable-type
                units = self.VoltageMode.peak_to_peak
            else:
                mag, units = newval

            # Finally, convert the magnitude out to a float.
            mag = float(assume_units(mag, pq.V).rescale(pq.V).magnitude)

        self._set_amplitude_(mag, units)
