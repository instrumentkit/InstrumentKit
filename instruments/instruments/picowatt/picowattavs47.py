#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides support for the Picowatt AVS 47 resistance bridge
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division

from builtins import range
from enum import IntEnum

import quantities as pq

from instruments.generic_scpi import SCPIInstrument
from instruments.util_fns import (enum_property, bool_property, int_property,
                                  ProxyList)

# CLASSES #####################################################################


class PicowattAVS47(SCPIInstrument):

    """
    The Picowatt AVS 47 is a resistance bridge used to measure the resistance
    of low-temperature sensors.

    Example usage:

    >>> import instruments as ik
    >>> bridge = ik.picowatt.PicowattAVS47.open_gpibusb('/dev/ttyUSB0', 1)
    >>> print bridge.sensor[0].resistance
    """

    def __init__(self, filelike):
        super(PicowattAVS47, self).__init__(filelike)
        self.sendcmd("HDR 0")  # Disables response headers from replies

    # INNER CLASSES #

    class Sensor(object):

        """
        Class representing a sensor on the PicowattAVS47

        .. warning:: This class should NOT be manually created by the user. It is
            designed to be initialized by the `PicowattAVS47` class.
        """

        def __init__(self, parent, idx):
            self._parent = parent
            self._idx = idx  # The AVS47 is actually zero-based indexing! Wow!

        @property
        def resistance(self):
            """
            Gets the resistance. It first ensures that the next measurement
            reading is up to date by first sending the "ADC" command.

            :units: :math:`\\Omega` (ohms)
            :rtype: `~quantities.Quantity`
            """
            # First make sure the mux is on the correct channel
            if self._parent.mux_channel != self._idx:
                self._parent.input_source = self._parent.InputSource.ground
                self._parent.mux_channel = self._idx
                self._parent.input_source = self._parent.InputSource.actual
            # Next, prep a measurement with the ADC command
            self._parent.sendcmd("ADC")
            return float(self._parent.query("RES?")) * pq.ohm

    # ENUMS #

    class InputSource(IntEnum):
        """
        Enum containing valid input source modes for the AVS 47
        """
        ground = 0
        actual = 1
        reference = 2

    # PROPERTIES #

    @property
    def sensor(self):
        """
        Gets a specific sensor object. The desired sensor is specified like
        one would access a list.

        :rtype: `~PicowattAVS47.Sensor`

        .. seealso::
            `PicowattAVS47` for an example using this property.
        """
        return ProxyList(self, PicowattAVS47.Sensor, range(8))

    remote = bool_property(
        name="REM",
        inst_true="1",
        inst_false="0",
        doc="""
        Gets/sets the remote mode state.

        Enabling the remote mode allows all settings to be changed by computer
        interface and locks-out the front panel.

        :type: `bool`
        """
    )

    input_source = enum_property(
        name="INP",
        enum=InputSource,
        input_decoration=int,
        doc="""
        Gets/sets the input source.

        :type: `PicowattAVS47.InputSource`
        """
    )

    mux_channel = int_property(
        name="MUX",
        doc="""
        Gets/sets the multiplexer sensor number.
        It is recommended that you ground the input before switching the
        multiplexer channel.

        Valid mux channel values are 0 through 7 (inclusive).

        :type: `int`
        """,
        valid_set=range(8)
    )

    excitation = int_property(
        name="EXC",
        doc="""
        Gets/sets the excitation sensor number.

        Valid excitation sensor values are 0 through 7 (inclusive).

        :type: `int`
        """,
        valid_set=range(8)
    )

    display = int_property(
        name="DIS",
        doc="""
        Gets/sets the sensor that is displayed on the front panel.

        Valid display sensor values are 0 through 7 (inclusive).

        :type: `int`
        """,
        valid_set=range(8)
    )
