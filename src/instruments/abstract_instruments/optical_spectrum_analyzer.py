#!/usr/bin/env python
"""
Provides an abstract base class for optical spectrum analyzer instruments
"""

# IMPORTS #####################################################################

import abc

from instruments.abstract_instruments import Instrument
from instruments.util_fns import ProxyList

# CLASSES #####################################################################


class OpticalSpectrumAnalyzer(Instrument, metaclass=abc.ABCMeta):
    """
    Abstract base class for optical spectrum analyzer instruments.

    All applicable concrete instruments should inherit from this ABC to
    provide a consistent interface to the user.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._channel_count = 1

    class Channel(metaclass=abc.ABCMeta):
        """
        Abstract base class for physical channels on an optical spectrum analyzer.

        All applicable concrete instruments should inherit from this ABC to
        provide a consistent interface to the user.

        Optical spectrum analyzers that only have a single channel do not need to
        define their own concrete implementation of this class. Ones with
        multiple channels need their own definition of this class, where
        this class contains the concrete implementations of the below
        abstract methods. Instruments with 1 channel have their concrete
        implementations at the parent instrument level.
        """

        def __init__(self, parent, name):
            self._parent = parent
            self._name = name

        # METHODS #

        @abc.abstractmethod
        def wavelength(self, bin_format=True):
            """
            Gets the x-axis of the specified data source channel. This is an
            abstract property.

            :param bool bin_format: If the waveform should be transfered in binary
                (``True``) or ASCII (``False``) formats.
            :return: The wavelength component of the waveform.
            :rtype: `numpy.ndarray`
            """
            if self._parent._channel_count == 1:
                return self._parent.wavelength(bin_format=bin_format)
            else:
                raise NotImplementedError

        @abc.abstractmethod
        def data(self, bin_format=True):
            """
            Gets the y-axis of the specified data source channel. This is an
            abstract property.

            :param bool bin_format: If the waveform should be transfered in binary
                (``True``) or ASCII (``False``) formats.
            :return: The y-component of the waveform.
            :rtype: `numpy.ndarray`
            """
            if self._parent._channel_count == 1:
                return self._parent.data(bin_format=bin_format)
            else:
                raise NotImplementedError

    # PROPERTIES #

    @property
    def channel(self):
        """
        Gets an iterator or list for easy Pythonic access to the various
        channel objects on the OSA instrument. Typically generated
        by the `~instruments.util_fns.ProxyList` helper.
        """
        return ProxyList(self, self.Channel, range(self._channel_count))

    @property
    def start_wl(self):
        """
        Gets/sets the the start wavelength of the OSA. This is
        an abstract property.

        :type: `~pint.Quantity`
        """
        raise NotImplementedError

    @start_wl.setter
    def start_wl(self, newval):
        raise NotImplementedError

    @property
    def stop_wl(self):
        """
        Gets/sets the the stop wavelength of the OSA. This is
        an abstract property.

        :type: `~pint.Quantity`
        """
        raise NotImplementedError

    @stop_wl.setter
    def stop_wl(self, newval):
        raise NotImplementedError

    @property
    def bandwidth(self):
        """
        Gets/sets the the bandwidth of the OSA. This is
        an abstract property.

        :type: `~pint.Quantity`
        """
        raise NotImplementedError

    @bandwidth.setter
    def bandwidth(self, newval):
        raise NotImplementedError

    # METHODS #

    @abc.abstractmethod
    def start_sweep(self):
        """
        Forces a start sweep on the attached OSA.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def wavelength(self, bin_format=True):
        """
        Gets the x-axis of the specified data source channel. This is an
        abstract property.

        :param bool bin_format: If the waveform should be transfered in binary
            (``True``) or ASCII (``False``) formats.
        :return: The wavelength component of the waveform.
        :rtype: `numpy.ndarray`
        """
        if self._channel_count > 1:
            return self.channel[0].wavelength(bin_format=bin_format)
        else:
            raise NotImplementedError

    @abc.abstractmethod
    def data(self, bin_format=True):
        """
        Gets the y-axis of the specified data source channel. This is an
        abstract property.

        :param bool bin_format: If the waveform should be transfered in binary
            (``True``) or ASCII (``False``) formats.
        :return: The y-component of the waveform.
        :rtype: `numpy.ndarray`
        """
        if self._channel_count > 1:
            return self.channel[0].data(bin_format=bin_format)
        else:
            raise NotImplementedError
