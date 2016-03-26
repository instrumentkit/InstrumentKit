#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides support for the SRS CTC-100 cryogenic temperature controller.
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division
from contextlib import contextmanager
from builtins import range

from enum import Enum

import quantities as pq
import numpy as np


from instruments.generic_scpi import SCPIInstrument
from instruments.util_fns import ProxyList

# CLASSES #####################################################################


class SRSCTC100(SCPIInstrument):

    """
    Communicates with a Stanford Research Systems CTC-100 cryogenic temperature
    controller.
    """

    def __init__(self, filelike):
        super(SRSCTC100, self).__init__(filelike)
        self._do_errcheck = True

    # DICTIONARIES #

    _BOOL_NAMES = {
        'On': True,
        'Off': False
    }

    # Note that the SRS CTC-100 uses '\xb0' to represent '°'.
    _UNIT_NAMES = {
        '\xb0C': pq.celsius,
        'W':     pq.watt,
        'V':     pq.volt,
        '\xea':  pq.ohm,
        '':      pq.dimensionless
    }

    # INNER CLASSES ##

    class SensorType(Enum):
        """
        Enum containing valid sensor types for the SRS CTC-100
        """
        rtd = 'RTD'
        thermistor = 'Thermistor'
        diode = 'Diode'
        rox = 'ROX'

    class Channel(object):

        """
        Represents an input or output channel on an SRS CTC-100 cryogenic
        temperature controller.
        """

        def __init__(self, ctc, chan_name):
            self._ctc = ctc

            # Save the pretty name that we are given.
            self._chan_name = chan_name

            # Strip spaces from the name used in remote programming, as
            # specified on page 14 of the manual.
            self._rem_name = chan_name.replace(" ", "")

        # PRIVATE METHODS #

        def _get(self, prop_name):
            return self._ctc.query("{}.{}?".format(
                self._rem_name,
                prop_name
            )).strip()

        def _set(self, prop_name, newval):
            self._ctc.sendcmd(
                '{}.{} = "{}"'.format(self._rem_name, prop_name, newval))

        # DISPLAY AND PROGRAMMING #
        # These properties control how the channel is identified in scripts
        # and on the front-panel display.

        @property
        def name(self):
            """
            Gets/sets the name of the channel that will be used by the
            instrument to identify the channel in programming and on the
            display.

            :type: `str`
            """
            return self._chan_name

        @name.setter
        def name(self, newval):
            self._set('name', newval)
            # TODO: check for errors!
            self._chan_name = newval
            self._rem_name = newval.replace(" ", "")

        # BASICS #

        @property
        def value(self):
            """
            Gets the measurement value of the channel. Units depend on what
            kind of sensor and/or channel you have specified. Units can be one
            of ``celsius``, ``watt``, ``volt``, ``ohm``, or ``dimensionless``.

            :type: `~quantities.Quantity`
            """
            # WARNING: Queries all units all the time.
            # TODO: Make an OutputChannel that subclasses this class,
            #       and add a setter for value.
            return pq.Quantity(
                float(self._get('value')),
                self.units
            )

        @property
        def units(self):
            """
            Gets the appropriate units for the specified channel.

            Units can be one of ``celsius``, ``watt``, ``volt``, ``ohm``, or
            ``dimensionless``.

            :type: `~quantities.UnitQuantity`
            """
            # FIXME: does not respect "chan.d/dt" property.
            return self._ctc.channel_units()[self._chan_name]
            # FIXME: the following line doesn't do what I'd expect, and so it's
            #        commented out.
            # return
            # self._ctc._UNIT_NAMES[self._ctc.query('{}.units?'.format(self._rem_name)).strip()]

        @property
        def sensor_type(self):
            """
            Gets the type of sensor attached to the specified channel.

            :type: `SRSCTC100.SensorType`
            """
            return self._ctc.SensorType(self._get('sensor'))

        # STATS #
        # The following properties control and query the statistics of the
        # channel.

        @property
        def stats_enabled(self):
            """
            Gets/sets enabling the statistics for the specified channel.

            :type: `bool`
            """
            return True if self._get('stats') is 'On' else False

        @stats_enabled.setter
        def stats_enabled(self, newval):
            # FIXME: replace with bool_property factory
            self._set('stats', 'On' if newval else 'Off')

        @property
        def stats_points(self):
            """
            Gets/sets the number of sample points to use for the channel
            statistics.

            :type: `int`
            """
            return int(self._get('points'))

        @stats_points.setter
        def stats_points(self, newval):
            self._set('points', int(newval))

        @property
        def average(self):
            """
            Gets the average measurement for the specified channel as
            determined by the statistics gathering.

            :type: `~quantities.Quantity`
            """
            return pq.Quantity(
                float(self._get('average')),
                self.units
            )

        @property
        def std_dev(self):
            """
            Gets the standard deviation for the specified channel as determined
            by the statistics gathering.

            :type: `~quantities.Quantity`
            """
            return pq.Quantity(
                float(self._get('SD')),
                self.units
            )

        # LOGGING #

        def get_log_point(self, which='next', units=None):
            """
            Get a log data point from the instrument.

            :param str which: Which data point you want. Valid examples
                include ``first``, and ``next``. Consult the instrument
                manual for the complete list
            :param units: Units to attach to the returned data point. If left
                with the value of `None` then the instrument will be queried
                for the current units setting.
            :type units: `~quantities.UnitQuantity`
            :return: The log data point with units
            :rtype: `~quantities.Quantity`
            """
            if units is None:
                units = self.units

            point = [
                s.strip() for s in
                self._ctc.query(
                    'getLog.xy {}, {}'.format(self._chan_name, which)
                ).split(',')
            ]
            return pq.Quantity(point[0], 'ms'), pq.Quantity(point[1], units)

        def get_log(self):
            """
            Gets all of the log data points currently saved in the instrument
            memory.

            :return: Tuple of all the log data points. First value is time,
                second is the measurement value.
            :rtype: Tuple of 2x `~quantities.Quantity`, each comprised of
                a numpy array (`numpy.dnarray`).
            """
            # Remember the current units.
            units = self.units

            # Find out how many points there are.
            n_points = int(
                self._ctc.query('getLog.xy? {}'.format(self._chan_name)))

            # Make an empty quantity that size for the times and for the channel
            # values.
            ts = pq.Quantity(np.empty((n_points,)), 'ms')
            temps = pq.Quantity(np.empty((n_points,)), units)

            # Reset the position to the first point, then save it.
            # pylint: disable=protected-access
            with self._ctc._error_checking_disabled():
                ts[0], temps[0] = self.get_log_point('first', units)
                for idx in range(1, n_points):
                    ts[idx], temps[idx] = self.get_log_point('next', units)

            # Do an actual error check now.
            if self._ctc.error_check_toggle:
                self._ctc.errcheck()

            return ts, temps

    # PRIVATE METHODS ##

    def _channel_names(self):
        """
        Returns the names of valid channels, using the ``getOutput.names``
        command, as documented in the example on page 14 of the
        `CTC-100 manual`_.

        Note that ``getOutput`` also lists input channels, confusingly enough.

        .. _CTC-100 manual: http://www.thinksrs.com/downloads/PDFs/Manuals/CTC100m.pdf
        """
        # We need to split apart the comma-separated list and make sure that
        # no newlines or other whitespace gets carried along for the ride.
        # Note that we do NOT strip spaces here, as this is done inside
        # the Channel object. Doing things that way allows us to present
        # the actual pretty name to users, but to use the remote-programming
        # name in commands.
        # As a consequence, users of this instrument MUST use spaces
        # matching the pretty name and not the remote-programming name.
        # CG could not think of a good way around this.
        names = [
            name.strip()
            for name in self.query('getOutput.names?').split(',')
        ]
        return names

    def channel_units(self):
        """
        Returns a dictionary from channel names to channel units, using the
        ``getOutput.units`` command. Unknown units and dimensionless quantities
        are presented the same way by the instrument, and so both are reported
        using `pq.dimensionless`.

        :rtype: `dict` with channel names as keys and units as values
        """
        unit_strings = [
            unit_str.strip()
            for unit_str in self.query('getOutput.units?').split(',')
        ]
        return dict(
            (chan_name, self._UNIT_NAMES[unit_str])
            for chan_name, unit_str in zip(self._channel_names(), unit_strings)
        )

    def errcheck(self):
        """
        Performs an error check query against the CTC100. This function does
        not return anything, but will raise an `IOError` if the error code
        received by the instrument is not zero.

        :return: Nothing
        """
        errs = super(SRSCTC100, self).query('geterror?').strip()
        err_code, err_descript = errs.split(',')
        err_code = int(err_code)
        if err_code == 0:
            return err_code
        else:
            raise IOError(err_descript.strip())

    @contextmanager
    def _error_checking_disabled(self):
        old = self._do_errcheck
        self._do_errcheck = False
        yield
        self._do_errcheck = old

    # PROPERTIES ##
    @property
    def channel(self):
        """
        Gets a specific measurement channel on the SRS CTC100. This is accessed
        like one would access a `dict`. Here you must use the actual channel
        names to address a specific channel. This is different from most
        other instruments in InstrumentKit because the CRC100 channel names
        can change by the user.

        The list of current valid channel names can be accessed by the
        `SRSCTC100._channel_names()` function.

        :type: `SRSCTC100.Channel`
        """
        # Note that since the names can change, we need to query channel names
        # each time. This is inefficient, but alas.
        return ProxyList(self, self.Channel, self._channel_names())

    @property
    def display_figures(self):
        """
        Gets/sets the number of significant figures to display. Valid range
        is 0-6 inclusive.

        :type: `int`
        """
        return int(self.query('system.display.figures?'))

    @display_figures.setter
    def display_figures(self, newval):
        if newval not in range(7):
            raise ValueError("Number of display figures must be an integer "
                             "from 0 to 6, inclusive.")
        self.sendcmd('system.display.figures = {}'.format(newval))

    @property
    def error_check_toggle(self):
        """
        Gets/sets if errors should be checked for after every command.

        :bool:
        """
        return self._do_errcheck

    @error_check_toggle.setter
    def error_check_toggle(self, newval):
        if not isinstance(newval, bool):
            raise TypeError
        self._do_errcheck = newval

    # OVERRIDEN METHODS #

    # We override sendcmd() and query() to do error checking after each
    # command.
    def sendcmd(self, cmd):
        super(SRSCTC100, self).sendcmd(cmd)
        if self._do_errcheck:
            self.errcheck()

    def query(self, cmd, size=-1):
        resp = super(SRSCTC100, self).query(cmd, size)
        if self._do_errcheck:
            self.errcheck()
        return resp

    # LOGGING COMMANDS #

    def clear_log(self):
        """
        Clears the SRS CTC100 log

        Not sure if this works.
        """
        self.sendcmd('System.Log.Clear yes')
