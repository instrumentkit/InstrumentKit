#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# hp6652a.py: Python class for the HP 6652a power supply
##
# © 2014 Steven Casagrande (scasagrande@galvant.ca)
# hp6652a class authored by Wil Langford (wil.langford+instrumentkit@gmail.com)
# portions adapted from hp6624a.py by Steven Casagrande
#
# This file is a part of the InstrumentKit project.
# Licensed under the AGPL version 3.
##
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
##

## FEATURES ####################################################################

from __future__ import division

## IMPORTS #####################################################################

import quantities as pq

from instruments.abstract_instruments import (PowerSupply, PowerSupplyChannel)
from instruments.util_fns import unitful_property, bool_property


## CLASSES #####################################################################


class HP6652a(PowerSupply, PowerSupplyChannel):
    """
    The HP6652a is a single output power supply.

    Because it is a single channel output, this object inherits from both
    PowerSupply and PowerSupplyChannel.

    According to the manual, this class MIGHT be usable for any HP power supply
    with a model number HP66XYA, where X is in {4,5,7,8,9} and Y is a digit(?).
    (e.g. HP6652A and HP6671A)

    HOWEVER, it has only been tested by the author with an HP6652A power supply.
    
    Example usage:

    >>> import time
    >>> import instruments as ik
    >>> psu = ik.hp.HP6652a.open_serial('/dev/ttyUSB0', 57600)
    >>> psu.voltage = 3 # Sets output voltage to 3V.
    >>> psu.output = True
    >>> psu.voltage
    array(3.0) * V
    >>> psu.voltage_sense < 5
    True
    >>> psu.output = False
    >>> psu.voltage_sense < 1
    True
    >>> psu.display_textmode=True
    >>> psu.display_text("test GOOD")
    'TEST GOOD'
    >>> time.sleep(5)
    >>> psu.display_textmode=False
    """
    
    def __init__(self, filelike):
        super(HP6652a, self).__init__(filelike)

    ## ENUMS ##

    # I don't know of any possible enumerations supported
    # by this instrument.

    ## PROPERTIES ##

    voltage = unitful_property(
        "VOLT",
        pq.volt,
        doc="""
        Gets/sets the output voltage.

        Note there is no bounds checking on the value specified.

        :units: As specified, or assumed to be :math:`\\text{V}` otherwise.
        :type: `float` or `~quantities.Quantity`
        """)

    current = unitful_property(
        "CURR",
        pq.amp,
        doc="""
        Gets/sets the output current.

        Note there is no bounds checking on the value specified.

        :units: As specified, or assumed to be :math:`\\text{A}` otherwise.
        :type: `float` or `~quantities.Quantity`
        """)

    voltage_sense = unitful_property(
        "MEAS:VOLT",
        pq.volt,
        doc="""
        Gets the actual output voltage as measured by the sense wires.

        :units: :math:`\\text{V}` (volts)
        :rtype: `~quantities.Quantity`
        """,
        readonly=True
    )

    current_sense = unitful_property(
        "MEAS:CURR",
        pq.amp,
        doc="""
        Gets the actual output current as measured by the sense wires.

        :units: :math:`\\text{A}` (amps)
        :rtype: `~quantities.Quantity`
        """,
        readonly=True
    )

    overvoltage = unitful_property(
        "VOLT:PROT",
        pq.volt,
        doc="""
        Gets/sets the overvoltage protection setting in volts.

        Note there is no bounds checking on the value specified.

        :units: As specified, or assumed to be :math:`\\text{V}` otherwise.
        :type: `float` or `~quantities.Quantity`
        """
    )

    overcurrent = bool_property(
        "CURR:PROT:STAT",
        '1',
        '0',
        doc="""
        Gets/sets the overcurrent protection setting.

        This is a toggle setting. It is either on or off.

        :type: `bool`
        """
    )

    output = bool_property(
        "OUTP",
        '1',
        '0',
        doc="""
        Gets/sets the output status.

        This is a toggle setting. True will turn on the instrument output
        while False will turn it off.

        :type: `bool`
        """
    )

    display_textmode = bool_property(
        "DISP:MODE",
        'TEXT',
        'NORM',
        doc="""
        Gets/sets the display mode.

        This is a toggle setting. True will allow text to be sent to the
        front-panel LCD with the display_text() method.  False returns to
        the normal display mode.

        See also: display_text()

        :type: `bool`
        """
    )

    @property
    def name(self):
        """
        The name of the connected instrument, as reported by the
        standard SCPI command ``*IDN?``.
        
        :rtype: `str`
        """
        idn_string = self.query("*IDN?")
        idn_list = idn_string.split(',')
        return ' '.join(idn_list[:2])

    @property
    def mode(self):
        """
        Unimplemented.
        """
        raise NotImplementedError("Setting the mode is not implemented.")

    @mode.setter
    def mode(self, newval):
        """
        Unimplemented.
        """
        raise NotImplementedError("Setting the mode is not implemented.")

    ## METHODS ##

    def reset(self):
        """
        Reset overvoltage and overcurrent errors to resume operation.
        """
        self.sendcmd('OUTP:PROT:CLE')

    def display_text(self, text_to_display):
        """
        Sends up to 12 (uppercase) alphanumerics to be sent to the
        front-panel LCD display.  Some punctuation is allowed, and
        can affect the number of characters allowed.  See the
        programming manual for the HP6652A for more details.

        Because the maximum valid number of possible characters is
        15 (counting the possible use of punctuation), the text will
        be truncated to 15 characters before the command is sent to
        the instrument.

        If an invalid string is sent, the command will fail silently.
        Any lowercase letters in the text_to_display will be converted
        to uppercase before the command is sent to the instrument.

        No attempt to validate punctuation is currently made.

        Because the string cannot be read back from the instrument,
        this method returns the actual string value sent.

        :type: 'str'
        """

        if len(text_to_display) > 15:
            text_to_display = text_to_display[:15]
        text_to_display = text_to_display.upper()

        self.sendcmd('DISP:TEXT "{}"'.format(text_to_display))

        return text_to_display

    def channel(self):
        """
        Return the channel (which in this case is the entire instrument.)

        :rtype: 'tuple'
        """
        return (self,)
