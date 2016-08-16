#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides the support for the Thorlabs MDT693B Piezo Controller.

Class originally contributed by Catherine Holloway.
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division

import quantities as pq

from instruments.abstract_instruments import Instrument
from instruments.util_fns import ProxyList, bool_property, int_property, \
    unitful_property


# CLASSES #####################################################################



class MDT693B(Instrument):
    """
    The MDT693B is is a controller for the voltage on precisely-controlled
    actuators. This model has three output voltages, and is primarily used to
    control stages in three dimensions.

    The user manual can be found here:
    https://www.thorlabs.com/drawings/f9c1d1abd428d849-AA2346ED-5056-1F02-43AE1247C3CAB43A/MDT694B-Manual.pdf
    """

    def __init__(self, filelike):
        super(MDT693B, self).__init__(filelike)
        self.terminator = "\r\n"
        self.prompt = "> "
        self._channel_count = 3

    # INNER CLASSES #

    class Channel(object):
        """
        Class representing a channel on the MDT693B
        """

        __CHANNEL_NAMES = {
            0: 'x',
            1: 'y',
            2: 'z'
        }

        def __init__(self, mdt, idx):
            self._mdt = mdt
            self._idx = idx
            self._chan = self.__CHANNEL_NAMES[self._idx]


        @property
        def voltage(self):
            """
            Gets/Sets the channel voltage.

            :param new_voltage: the new set voltage.
            :type new_voltage: quantities.V
            :return: The voltage of the channel.
            :rtype: quantities.V
            """
            return float(self._mdt.query(self._chan+"voltage?"))*pq.V

        @voltage.setter
        def voltage(self, new_voltage):
            new_voltage = new_voltage.rescale('V').magnitude
            self._mdt.sendcmd(self._chan+"voltage="+str(new_voltage))

        @property
        def minimum(self):
            """
            Gets/Sets the minimum channel voltage.

            :param new_voltage: the new minimum voltage.
            :type new_voltage: quantities.V
            :return: The minimum voltage of the channel.
            :rtype: quantities.V
            """
            return float(self._mdt.query(self._chan+"min?"))*pq.V

        @minimum.setter
        def minimum(self, new_voltage):
            new_voltage = new_voltage.rescale('V').magnitude
            self._mdt.sendcmd(self._chan+"min="+str(new_voltage))
            
        @property
        def maximum(self):
            """
            Gets/Sets the maximum channel voltage.

            :param new_voltage: the new maximum voltage.
            :type new_voltage: quantities.V
            :return: The maximum voltage of the channel.
            :rtype: quantities.V
            """
            return float(self._mdt.query(self._chan+"max?"))*pq.V

        @maximum.setter
        def maximum(self, new_voltage):
            new_voltage = new_voltage.rescale('V').magnitude
            self._mdt.sendcmd(self._chan+"min="+str(new_voltage))


    @property
    def channel(self):
        """
        Gets a specific channel object. The desired channel is specified like
        one would access a list.

        :rtype: `MDT693B.Channel`
        """
        return ProxyList(self, MDT693B.Channel, range(self._channel_count))

    master_scan_enable = bool_property(
        "msenable",
        "1",
        "0",
        doc="""
        Gets/Sets the master scan enabled status.

        Returns `True` if master scan is enabled, and `False` otherwise.

        :rtype: `bool`
        """,
        set_fmt='{}={}'
    )

    intensity = int_property(
        "intensity",
        valid_set=range(0, 15),
        set_fmt="{}={}",
        doc="""
        Gets/sets the screen brightness.

        Value within [0, 15]

        :return: the gain (in nnn)
        :type: `int`
        """
    )

    master_scan_voltage = unitful_property(
        "msvoltage",
        units=pq.V,
        format_code="{:.1f}",
        set_fmt="{}={}",
        doc="""
        Gets/sets the master scan voltage increment.

        :return: The master scan voltage increment
        :units: Voltage
        :type: `~quantities.V`
        """
    )