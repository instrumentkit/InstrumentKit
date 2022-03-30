#!/usr/bin/env python
"""
Provides an abstract base class for function generator instruments
"""

# IMPORTS #####################################################################


import abc
from enum import Enum

from pint.errors import DimensionalityError

from instruments.abstract_instruments import Instrument
from instruments.units import ureg as u
from instruments.util_fns import assume_units, ProxyList

# CLASSES #####################################################################


class FunctionGenerator(Instrument, metaclass=abc.ABCMeta):

    """
    Abstract base class for function generator instruments.

    All applicable concrete instruments should inherit from this ABC to
    provide a consistent interface to the user.
    """

    def __init__(self, filelike):
        super().__init__(filelike)
        self._channel_count = 1

    # pylint:disable=protected-access
    class Channel(metaclass=abc.ABCMeta):
        """
        Abstract base class for physical channels on a function generator.

        All applicable concrete instruments should inherit from this ABC to
        provide a consistent interface to the user.

        Function generators that only have a single channel do not need to
        define their own concrete implementation of this class. Ones with
        multiple channels need their own definition of this class, where
        this class contains the concrete implementations of the below
        abstract methods. Instruments with 1 channel have their concrete
        implementations at the parent instrument level.
        """

        def __init__(self, parent, name):
            self._parent = parent
            self._name = name

        # ABSTRACT PROPERTIES #

        @property
        def frequency(self):
            """
            Gets/sets the the output frequency of the function generator. This is
            an abstract property.

            :type: `~pint.Quantity`
            """
            if self._parent._channel_count == 1:
                return self._parent.frequency
            else:
                raise NotImplementedError()

        @frequency.setter
        def frequency(self, newval):
            if self._parent._channel_count == 1:
                self._parent.frequency = newval
            else:
                raise NotImplementedError()

        @property
        def function(self):
            """
            Gets/sets the output function mode of the function generator. This is
            an abstract property.

            :type: `~enum.Enum`
            """
            if self._parent._channel_count == 1:
                return self._parent.function
            else:
                raise NotImplementedError()

        @function.setter
        def function(self, newval):
            if self._parent._channel_count == 1:
                self._parent.function = newval
            else:
                raise NotImplementedError()

        @property
        def offset(self):
            """
            Gets/sets the output offset voltage of the function generator. This is
            an abstract property.

            :type: `~pint.Quantity`
            """
            if self._parent._channel_count == 1:
                return self._parent.offset
            else:
                raise NotImplementedError()

        @offset.setter
        def offset(self, newval):
            if self._parent._channel_count == 1:
                self._parent.offset = newval
            else:
                raise NotImplementedError()

        @property
        def phase(self):
            """
            Gets/sets the output phase of the function generator. This is an
            abstract property.

            :type: `~pint.Quantity`
            """
            if self._parent._channel_count == 1:
                return self._parent.phase
            else:
                raise NotImplementedError()

        @phase.setter
        def phase(self, newval):
            if self._parent._channel_count == 1:
                self._parent.phase = newval
            else:
                raise NotImplementedError()

        def _get_amplitude_(self):
            if self._parent._channel_count == 1:
                return self._parent._get_amplitude_()
            else:
                raise NotImplementedError()

        def _set_amplitude_(self, magnitude, units):
            if self._parent._channel_count == 1:
                self._parent._set_amplitude_(magnitude=magnitude, units=units)
            else:
                raise NotImplementedError()

        @property
        def amplitude(self):
            """
            Gets/sets the output amplitude of the function generator.

            If set with units of :math:`\\text{dBm}`, then no voltage mode can
            be passed.

            If set with units of :math:`\\text{V}` as a `~pint.Quantity` or a
            `float` without a voltage mode, then the voltage mode is assumed to be
            peak-to-peak.

            :units: As specified, or assumed to be :math:`\\text{V}` if not
                specified.
            :type: Either a `tuple` of a `~pint.Quantity` and a
                `FunctionGenerator.VoltageMode`, or a `~pint.Quantity`
                if no voltage mode applies.
            """
            mag, units = self._get_amplitude_()

            if units == self._parent.VoltageMode.dBm:
                return u.Quantity(mag, u.dBm)

            return u.Quantity(mag, u.V), units

        @amplitude.setter
        def amplitude(self, newval):
            # Try and rescale to dBm... if it succeeds, set the magnitude
            # and units accordingly, otherwise handle as a voltage.
            try:
                newval_dbm = newval.to(u.dBm)
                mag = float(newval_dbm.magnitude)
                units = self._parent.VoltageMode.dBm
            except (AttributeError, ValueError, DimensionalityError):
                # OK, we have volts. Now, do we have a tuple? If not, assume Vpp.
                if not isinstance(newval, tuple):
                    mag = newval
                    units = self._parent.VoltageMode.peak_to_peak
                else:
                    mag, units = newval

                # Finally, convert the magnitude out to a float.
                mag = float(assume_units(mag, u.V).to(u.V).magnitude)

            self._set_amplitude_(mag, units)

        def sendcmd(self, cmd):
            self._parent.sendcmd(cmd)

        def query(self, cmd, size=-1):
            return self._parent.query(cmd, size)

    # ENUMS #

    class VoltageMode(Enum):
        """
        Enum containing valid voltage modes for many function generators
        """

        peak_to_peak = "VPP"
        rms = "VRMS"
        dBm = "DBM"

    class Function(Enum):
        """
        Enum containg valid output function modes for many function generators
        """

        sinusoid = "SIN"
        square = "SQU"
        triangle = "TRI"
        ramp = "RAMP"
        noise = "NOIS"
        arbitrary = "ARB"

    @property
    def channel(self):
        """
        Gets a channel object for the function generator. This should use
        `~instruments.util_fns.ProxyList` to achieve this.

        The number of channels accessable depends on the value
        of FunctionGenerator._channel_count

        :rtype: `FunctionGenerator.Channel`
        """
        return ProxyList(self, self.Channel, range(self._channel_count))

    # PASSTHROUGH PROPERTIES #

    @property
    def amplitude(self):
        """
        Gets/sets the output amplitude of the first channel
        of the function generator

        :type: `~pint.Quantity`
        """
        return self.channel[0].amplitude

    @amplitude.setter
    def amplitude(self, newval):
        self.channel[0].amplitude = newval

    def _get_amplitude_(self):
        raise NotImplementedError()

    def _set_amplitude_(self, magnitude, units):
        raise NotImplementedError()

    @property
    def frequency(self):
        """
        Gets/sets the the output frequency of the function generator. This is
        an abstract property.

        :type: `~pint.Quantity`
        """
        if self._channel_count > 1:
            return self.channel[0].frequency
        else:
            raise NotImplementedError()

    @frequency.setter
    def frequency(self, newval):
        if self._channel_count > 1:
            self.channel[0].frequency = newval
        else:
            raise NotImplementedError()

    @property
    def function(self):
        """
        Gets/sets the output function mode of the function generator. This is
        an abstract property.

        :type: `~enum.Enum`
        """
        if self._channel_count > 1:
            return self.channel[0].function
        else:
            raise NotImplementedError()

    @function.setter
    def function(self, newval):
        if self._channel_count > 1:
            self.channel[0].function = newval
        else:
            raise NotImplementedError()

    @property
    def offset(self):
        """
        Gets/sets the output offset voltage of the function generator. This is
        an abstract property.

        :type: `~pint.Quantity`
        """
        if self._channel_count > 1:
            return self.channel[0].offset
        else:
            raise NotImplementedError()

    @offset.setter
    def offset(self, newval):
        if self._channel_count > 1:
            self.channel[0].offset = newval
        else:
            raise NotImplementedError()

    @property
    def phase(self):
        """
        Gets/sets the output phase of the function generator. This is an
        abstract property.

        :type: `~pint.Quantity`
        """
        if self._channel_count > 1:
            return self.channel[0].phase
        else:
            raise NotImplementedError()

    @phase.setter
    def phase(self, newval):
        if self._channel_count > 1:
            self.channel[0].phase = newval
        else:
            raise NotImplementedError()
