#!/usr/bin/env python
"""
Provides an abstract base class for optical spectrum analyzer instruments
"""

# IMPORTS #####################################################################


import abc

from instruments.abstract_instruments import Instrument

# CLASSES #####################################################################


class OpticalSpectrumAnalyzer(Instrument, metaclass=abc.ABCMeta):

    """
    Abstract base class for optical spectrum analyzer instruments.

    All applicable concrete instruments should inherit from this ABC to
    provide a consistent interface to the user.
    """

    class Channel(metaclass=abc.ABCMeta):
        """
        Abstract base class for physical channels on an optical spectrum analyzer.

        All applicable concrete instruments should inherit from this ABC to
        provide a consistent interface to the user.
        """

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
            raise NotImplementedError

    # PROPERTIES #

    @property
    @abc.abstractmethod
    def channel(self):
        """
        Gets an iterator or list for easy Pythonic access to the various
        channel objects on the OSA instrument. Typically generated
        by the `~instruments.util_fns.ProxyList` helper.
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def start_wl(self):
        """
        Gets/sets the the start wavelength of the OSA. This is
        an abstract property.

        :type: `~pint.Quantity`
        """
        raise NotImplementedError

    @start_wl.setter
    @abc.abstractmethod
    def start_wl(self, newval):
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def stop_wl(self):
        """
        Gets/sets the the stop wavelength of the OSA. This is
        an abstract property.

        :type: `~pint.Quantity`
        """
        raise NotImplementedError

    @stop_wl.setter
    @abc.abstractmethod
    def stop_wl(self, newval):
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def bandwidth(self):
        """
        Gets/sets the the bandwidth of the OSA. This is
        an abstract property.

        :type: `~pint.Quantity`
        """
        raise NotImplementedError

    @bandwidth.setter
    @abc.abstractmethod
    def bandwidth(self, newval):
        raise NotImplementedError

    # METHODS #

    @abc.abstractmethod
    def start_sweep(self):
        """
        Forces a start sweep on the attached OSA.
        """
        raise NotImplementedError
