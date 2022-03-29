#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides support for the Rigol DP832 power supply.
"""

# IMPORTS #####################################################################


from enum import Enum

from instruments.units import ureg as u

from instruments.abstract_instruments import (
    PowerSupply,
    PowerSupplyChannel,
)
from instruments.generic_scpi import SCPIInstrument
from instruments.util_fns import ProxyList, unitful_property, bool_property

# CLASSES #####################################################################

class RigolDP832(PowerSupply, SCPIInstrument):

    """
    The Rigol DP832 is a multi-output power supply.
    
    This class can also be used for DP8XX where XX=11,21,32,31. Some models
    have less channels than the DP832, and it is up to the user to take this
    into account. This can be changed with the `~DP832.channel_count` proerty.

    +--------------+--------------------+
    | Model        | Number of Channels |
    +==============+====================+
    | DP831A/DP831 | 3                  |
    +--------------+--------------------+
    | DP832A/DP832 | 3                  |
    +--------------+--------------------+
    | DP821A/DP821 | 2                  |
    +--------------+--------------------+
    | DP811A/DP811 | 1                  |
    +--------------+--------------------+
    
    Example usage:

    >>> import instruments as ik
    >>> psu = ik.rigol.rigoldp832.open_gpibusb('/dev/ttyUSB0', 1)
    >>> psu.channel[0].voltage = 10 # Sets channel 1 voltage to 10 V.

    The user manual can be found here:
    http://beyondmeasure.rigoltech.com/acton/attachment/1579/f-03a1/1/-/-/-/-/DP800%20Programming%20Guide.pdf
    """

    def __init__(self, filelike):
        super(RigolDP832, self).__init__(filelike)
        self._channel_count = 3

    # ENUMS #

    class Mode(Enum):
        """
        Enum containing valid output modes for DP832
        """
        constant_curr = "CC"
        cont_volt     = "CV"
        unreg         = "UR"

    # INNER CLASSES #

    class Channel(PowerSupplyChannel):
        """
        Class representing a power supply channel on the DP832

        .. warning:: This class should NOT be manually created by the user. It is
        designed to be initialized by the `DP832` class.
        """

        def __init__(self, dp, idx):
            self._dp  = dp
            self._idx = idx + 1
            
        # COMMUNICATION METHODS #

        def _format_cmd(self, cmd):
            
            cmd = cmd.split("|") # Arbitrary data delimiter
            assert len(cmd) <= 2 # Assumption to check.

            cmd = cmd[0].format(idx=self._idx, value=cmd[1])
            
            return cmd

        def sendcmd(self, cmd):
            """
            Function used to send a command to the instrument while wrapping
            the command with the neccessary identifier for the channel.
            :param str cmd: Command that will be sent to the instrument after
                being prefixed with the channel identifier
            """
            cmd = self._format_cmd(cmd)
            self._dp.sendcmd(cmd)

        def query(self, cmd):
            """
            Function used to send a command to the instrument while wrapping
            the command with the neccessary identifier for the channel.
            :param str cmd: Command that will be sent to the instrument after
                being prefixed with the channel identifier
            :return: The result from the query
            :rtype: `str`
            """
            cmd = self._format_cmd(cmd)
            return self._dp.query(cmd)

        # PROPERTIES #

        @property
        def mode(self):
            """
            Gets the mode for the specified channel.
            """
            return RigolDP832.Mode(self.query("OUTP:MODE? CH{idx}"))

        @mode.setter
        def mode(self):
            raise NotImplementedError

        @property
        def output(self):
            """
            Gets/sets the outputting status of the specified channel.
            This is a toggle setting. True will turn on the channel output
            while False will turn it off.
            """
            # Manual property because the factories append a "?", breaking this
            return self.query("OUTP? CH{idx}").strip() == "ON"

        @output.setter
        def output(self, newval):
            if not isinstance(newval, bool):
                raise TypeError("Bool properties must be specified with a "
                            "boolean value")

            self.sendcmd("{}|{}".format("OUTP CH{idx},{value}", 
                                        "ON" if newval else "OFF"))

        voltage = unitful_property(
            "SOUR{idx}:VOLT",
            u.volt,
            set_cmd="SOUR{idx}:VOLT {value}",
            set_fmt="{}|{}",
            output_decoration=float,
            doc="""
            Gets/sets the voltage of the specified channel. If the device is in
            constant current mode, this sets the voltage limit.
            Note there is no bounds checking on the value specified.
            :units: As specified, or assumed to be :math:`\\text{V}` otherwise.
            :type: `float` or `~pint.Quantity`
            """
        )

        current = unitful_property(
            "SOUR{idx}:CURR",
            u.amp,
            set_cmd="SOUR{idx}:CURR {value}",
            set_fmt="{}|{}",
            output_decoration=float,
            doc="""
            Gets/sets the current of the specified channel. If the device is in
            constant voltage mode, this sets the current limit.
            Note there is no bounds checking on the value specified.
            :units: As specified, or assumed to be :math:`\\text{A}` otherwise.
            :type: `float` or `~pint.Quantity`
            """
        )

        overvoltage = unitful_property(
            "SOUR{idx}:VOLT:PROT?",
            u.volt,
            set_cmd="SOUR{idx}:VOLT:PROT {value}",
            set_fmt="{}|{}",
            output_decoration=float,
            doc="""
            Gets/sets the overvoltage protection setting for the specified channel.
            Note there is no bounds checking on the value specified.
            :units: As specified, or assumed to be :math:`\\text{V}` otherwise.
            :type: `float` or `~pint.Quantity`
            """
        )

        overcurrent = unitful_property(
            "SOUR{idx}:CURR:PROT",
            u.amp,
            set_cmd="SOUR{idx}:CURR:PROT:{value}",
            set_fmt="{}|{}",
            output_decoration=float,
            doc="""
            Gets/sets the overcurrent protection setting for the specified channel.
            Note there is no bounds checking on the value specified.
            :units: As specified, or assumed to be :math:`\\text{A}` otherwise.
            :type: `float` or `~pint.Quantity`
            """
        )

        output = bool_property(
            "OUTP? CH{idx}",
            set_cmd="OUTP CH{idx},{value}",
            set_fmt="{}|{}",
            inst_true="ON",
            inst_false="OFF",
            doc="""
            Gets/sets the outputting status of the specified channel.
            This is a toggle setting. True will turn on the channel output
            while False will turn it off.
            :type: `bool`
            """
        )

        def reset(self):
            """
            Reset overvoltage and overcurrent errors to resume operation.
            """
            self.sendcmd('OUTP:OVP:CLEAR CH{idx}')
            self.sendcmd('OUTP:OCP:CLEAR CH{idx}')

    # PROPERTIES ##

    @property
    def channel(self):
        """
        Gets a specific channel object. The desired channel is specified like
        one would access a list.
        :rtype: `RigolDP832.Channel`
        .. seealso::
            `RigolDP832` for example using this property.
        """
        return ProxyList(self, RigolDP832.Channel, range(self.channel_count))

    @property
    def voltage(self):
        """
        Gets/sets the voltage for all four channels.
        :units: As specified (if a `~pint.Quantity`) or assumed to be
            of units Volts.
        :type: `tuple`[`~pint.Quantity`, ...] with units Volt
        """
        return tuple([
            self.channel[i].voltage for i in range(self.channel_count)
        ])

    @voltage.setter
    def voltage(self, newval):
        if isinstance(newval, (list, tuple)):
            if len(newval) is not self.channel_count:
                raise ValueError('When specifying the voltage for all channels '
                                 'as a list or tuple, it must be of '
                                 'length {}.'.format(self.channel_count))
            for i in range(self.channel_count):
                self.channel[i].voltage = newval[i]
        else:
            for i in range(self.channel_count):
                self.channel[i].voltage = newval

    @property
    def current(self):
        """
        Gets/sets the current for all four channels.
        :units: As specified (if a `~pint.Quantity`) or assumed to be
            of units Amps.
        :type: `tuple`[`~pint.Quantity`, ...] with units Amp
        """
        return tuple([
            self.channel[i].current for i in range(self.channel_count)
        ])

    @current.setter
    def current(self, newval):
        if isinstance(newval, (list, tuple)):
            if len(newval) is not self.channel_count:
                raise ValueError('When specifying the current for all channels '
                                 'as a list or tuple, it must be of '
                                 'length {}.'.format(self.channel_count))
            for i in range(self.channel_count):
                self.channel[i].current = newval[i]
        else:
            for i in range(self.channel_count):
                self.channel[i].current = newval

    @property
    def channel_count(self):
        """
        Gets/sets the number of output channels available for the connected
        power supply.
        :type: `int`
        """
        return self._channel_count

    @channel_count.setter
    def channel_count(self, newval):
        if not isinstance(newval, int):
            raise TypeError('Channel count must be specified as an integer.')
        if newval < 1:
            raise ValueError('Channel count must be >=1')
        elif newval > 3:
            raise ValueError('Channel count must be <=3')
        self._channel_count = newval

    # SCPI OVERRIDES ###########################################################

    def check_error_queue(self):
        """
        Returns the latest error in the error queue, then clears the error
        from the error queue. If there are no more errors in the queue then
        error -101 "Invalid Character" is continuously returned. 
        """
        # Return example: '-101,"Invalid character"\n'
        err = self.query("SYST:ERR?").strip().split(",")

        # Checks if error code in enum, if not returns the sent error string.
        return self.ErrorCodes(int(err[0])) if int(err[0]) in self.ErrorCodes._value2member_map_ else err[1].strip('"')
    
    @property
    def line_frequency(self):
        raise NotImplementedError

    @line_frequency.setter
    def line_frequency(self, newval):
        raise NotImplementedError

    @property
    def display_brightness(self):
        raise NotImplementedError

    @display_brightness.setter
    def display_brightness(self, newval):
        raise NotImplementedError

    @property
    def display_contrast(self):
        raise NotImplementedError

    @display_contrast.setter
    def display_contrast(self, newval):
        raise NotImplementedError