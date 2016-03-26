#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides support for the Keithley 6220 constant current supply
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division

import quantities as pq

from instruments.abstract_instruments import PowerSupply
from instruments.generic_scpi import SCPIInstrument
from instruments.util_fns import bounded_unitful_property

# CLASSES #####################################################################


class Keithley6220(SCPIInstrument, PowerSupply):

    """
    The Keithley 6220 is a single channel constant current supply.

    Because this is a constant current supply, most features that a regular
    power supply have are not present on the 6220.

    Example usage:

    >>> import quantities as pq
    >>> import instruments as ik
    >>> ccs = ik.keithley.Keithley6220.open_gpibusb("/dev/ttyUSB0", 10)
    >>> ccs.current = 10 * pq.milliamp # Sets current to 10mA
    >>> ccs.disable() # Turns off the output and sets the current to 0A
    """

    # PROPERTIES ##

    @property
    def channel(self):
        """
        For most power supplies, this would return a channel specific object.
        However, the 6220 only has a single channel, so this function simply
        returns a tuple containing itself. This is for compatibility reasons
        if a multichannel supply is replaced with the single-channel 6220.

        For example, the following commands are the same and both set the
        current to 10mA:

        >>> ccs.channel[0].current = 0.01
        >>> ccs.current = 0.01
        """
        return self,

    @property
    def voltage(self):
        """
        This property is not supported by the Keithley 6220.
        """
        raise NotImplementedError("The Keithley 6220 does not support voltage "
                                  "settings.")

    @voltage.setter
    def voltage(self, newval):
        raise NotImplementedError("The Keithley 6220 does not support voltage "
                                  "settings.")

    current, current_min, current_max = bounded_unitful_property(
        "SOUR:CURR",
        pq.amp,
        valid_range=(-105 * pq.milliamp, +105 * pq.milliamp),
        doc="""
        Gets/sets the output current of the source. Value must be between
        -105mA and +105mA.

        :units: As specified, or assumed to be :math:`\\text{A}` otherwise.
        :type: `float` or `~quantities.Quantity`
        """
    )

    # METHODS #

    def disable(self):
        """
        Set the output current to zero and disable the output.
        """
        self.sendcmd("SOUR:CLE:IMM")
