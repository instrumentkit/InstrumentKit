#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Driver for the HP6652a single output power supply

Originally contributed by Wil Langford (wil.langford+instrumentkit@gmail.com)
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division

import quantities as pq

from instruments.abstract_instruments import (PowerSupply, PowerSupplyChannel)
from instruments.util_fns import unitful_property, bool_property


# CLASSES #####################################################################


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

    # ENUMS ##

    # I don't know of any possible enumerations supported
    # by this instrument.

    # PROPERTIES ##

    voltage = unitful_property(
        "VOLT",
        pq.volt,
        doc="""
        Gets/sets the output voltage.

        Note there is no bounds checking on the value specified.

        :units: As specified, or assumed to be :math:`\\text{V}` otherwise.
        :type: `float` or `~quantities.Quantity`
        """
    )

    current = unitful_property(
        "CURR",
        pq.amp,
        doc="""
        Gets/sets the output current.

        Note there is no bounds checking on the value specified.

        :units: As specified, or assumed to be :math:`\\text{A}` otherwise.
        :type: `float` or `~quantities.Quantity`
        """
    )

    voltage_sense = unitful_property(
        "MEAS:VOLT",
        pq.volt,
        readonly=True,
        doc="""
        Gets the actual output voltage as measured by the sense wires.

        :units: :math:`\\text{V}` (volts)
        :rtype: `~quantities.Quantity`
        """
    )

    current_sense = unitful_property(
        "MEAS:CURR",
        pq.amp,
        readonly=True,
        doc="""
        Gets the actual output current as measured by the sense wires.

        :units: :math:`\\text{A}` (amps)
        :rtype: `~quantities.Quantity`
        """
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
        inst_true="1",
        inst_false="0",
        doc="""
        Gets/sets the overcurrent protection setting.

        This is a toggle setting. It is either on or off.

        :type: `bool`
        """
    )

    output = bool_property(
        "OUTP",
        inst_true="1",
        inst_false="0",
        doc="""
        Gets/sets the output status.

        This is a toggle setting. True will turn on the instrument output
        while False will turn it off.

        :type: `bool`
        """
    )

    display_textmode = bool_property(
        "DISP:MODE",
        inst_true="TEXT",
        inst_false="NORM",
        doc="""
        Gets/sets the display mode.

        This is a toggle setting. True will allow text to be sent to the
        front-panel LCD with the display_text() method.  False returns to
        the normal display mode.

        .. seealso:: `~HP6652a.display_text()`

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

    # METHODS ##

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

        :param text_to_display: The text that you wish to have displayed
            on the front-panel LCD
        :type text_to_display: 'str'
        :return: Returns the version of the provided string that will
            be send to the instrument. This means it will be truncated to
            a maximum of 15 characters and changed to all upper case.
        :rtype: `str`
        """

        if len(text_to_display) > 15:
            text_to_display = text_to_display[:15]
        text_to_display = text_to_display.upper()

        self.sendcmd('DISP:TEXT "{}"'.format(text_to_display))

        return text_to_display

    @property
    def channel(self):
        """
        Return the channel (which in this case is the entire instrument, since
        there is only 1 channel on the HP6652a.)

        :rtype: 'tuple' of length 1 containing a reference back to the parent
            HP6652a object.
        """
        return self,
