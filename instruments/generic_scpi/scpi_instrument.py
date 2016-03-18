#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides support for SCPI compliant instruments
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division

from builtins import map

from enum import IntEnum
import quantities as pq

from instruments.abstract_instruments import Instrument
from instruments.util_fns import assume_units

# CLASSES #####################################################################


class SCPIInstrument(Instrument):

    r"""
    Base class for all SCPI-compliant instruments. Inherits from
    from `~instruments.Instrument`.

    This class does not implement any instrument-specific communication
    commands. What it does add is several of the generic SCPI star commands.
    This includes commands such as ``*IDN?``, ``*OPC?``, and ``*RST``.

    Example usage:

    >>> import instruments as ik
    >>> inst = ik.generic_scpi.SCPIInstrument.open_tcpip('192.168.0.2', 8888)
    >>> print(inst.name)
    """

    def __init__(self, filelike):
        super(SCPIInstrument, self).__init__(filelike)

    # PROPERTIES #

    @property
    def name(self):
        """
        The name of the connected instrument, as reported by the
        standard SCPI command ``*IDN?``.

        :rtype: `str`
        """
        return self.query('*IDN?')

    @property
    def scpi_version(self):
        """
        Returns the version of the SCPI protocol supported by this instrument,
        as specified by the ``SYST:VERS?`` command described in section 21.21
        of the SCPI 1999 standard.
        """
        return self.query("SYST:VERS?")

    @property
    def op_complete(self):
        """
        Check if all operations sent to the instrument have been completed.

        :rtype: `bool`
        """
        result = self.query('*OPC?')
        return bool(int(result))

    @property
    def power_on_status(self):
        """
        Gets/sets the power on status for the instrument.

        :type: `bool`
        """
        result = self.query('*PSC?')
        return bool(int(result))

    @power_on_status.setter
    def power_on_status(self, newval):
        on = ['on', '1', 1, True]
        off = ['off', '0', 0, False]
        if isinstance(newval, str):
            newval = newval.lower()
        if newval in on:
            self.sendcmd('*PSC 1')
        elif newval in off:
            self.sendcmd('*PSC 0')
        else:
            raise ValueError

    @property
    def self_test_ok(self):
        """
        Gets the results of the instrument's self test. This lets you check
        if the self test was sucessful or not.

        :rtype: `bool`
        """
        result = self.query('*TST?')
        try:
            result = int(result)
            return result == 0
        except ValueError:
            return False

    # BASIC SCPI COMMANDS ##

    def reset(self):
        """
        Reset instrument. On many instruments this is a factory reset and will
        revert all settings to default.
        """
        self.sendcmd('*RST')

    def clear(self):
        """
        Clear instrument. Consult manual for specifics related to that
        instrument.
        """
        self.sendcmd('*CLS')

    def trigger(self):
        """
        Send a software trigger event to the instrument. On most instruments
        this will cause some sort of hardware event to start. For example, a
        multimeter might take a measurement.

        This software trigger usually performs the same action as a hardware
        trigger to your instrument.
        """
        self.sendcmd('*TRG')

    def wait_to_continue(self):
        """
        Instruct the instrument to wait until it has completed all received
        commands before continuing.
        """
        self.sendcmd('*WAI')

    # SYSTEM COMMANDS ##

    @property
    def line_frequency(self):
        """
        Gets/sets the power line frequency setting for the instrument.

        :return: The power line frequency
        :units: Hertz
        :type: `~quantities.quantity.Quantity`
        """
        return pq.Quantity(
            float(self.query("SYST:LFR?")),
            "Hz"
        )

    @line_frequency.setter
    def line_frequency(self, newval):
        self.sendcmd("SYST:LFR {}".format(
            assume_units(newval, "Hz").rescale("Hz").magnitude
        ))

    # ERROR QUEUE HANDLING ##
    # NOTE: This functionality is still quite incomplete, and could be fleshed
    #       out significantly still. One good thing would be to add handling
    #       for SCPI-defined error codes.
    #
    #       Another good use of this functionality would be to allow users to
    #       automatically check errors after each command or query.
    class ErrorCodes(IntEnum):

        """
        Enumeration describing error codes as defined by SCPI 1999.0.
        Error codes that are equal to 0 mod 100 are defined to be *generic*.
        """
        # NOTE: this class may be overriden by subclasses, since the only access
        #       to this enumeration from within SCPIInstrument is by "self,"
        #       not by explicit name. Thus, if an instrument supports additional
        #       error codes from the SCPI base, they can be added in a natural
        #       way.
        no_error = 0

        # -100 BLOCK: COMMAND ERRORS ##
        command_error = -100
        invalid_character = -101
        syntax_error = -102
        invalid_separator = -103
        data_type_error = -104
        get_not_allowed = -105
        # -106 and -107 not specified.
        parameter_not_allowed = -108
        missing_parameter = -109
        command_header_error = -110
        header_separator_error = -111
        program_mnemonic_too_long = -112
        undefined_header = -113
        header_suffix_out_of_range = -114
        unexpected_number_of_parameters = -115
        numeric_data_error = -120
        invalid_character_in_number = -121
        exponent_too_large = -123
        too_many_digits = -124
        numeric_data_not_allowed = -128
        suffix_error = -130
        invalid_suffix = -131
        suffix_too_long = -134
        suffix_not_allowed = -138
        character_data_error = -140
        invalid_character_data = -141
        character_data_too_long = -144
        character_data_not_allowed = -148
        string_data_error = -150
        invalid_string_data = -151
        string_data_not_allowed = -158
        block_data_error = -160
        invalid_block_data = -161
        block_data_not_allowed = -168
        expression_error = -170
        invalid_expression = -171
        expression_not_allowed = -178
        macro_error = -180
        invalid_outside_macro_definition = -181
        invalid_inside_macro_definition = -183
        macro_parameter_error = -184

        # pylint: disable=fixme
        # TODO: copy over other blocks.
        # -200 BLOCK: EXECUTION ERRORS ##
        # -300 BLOCK: DEVICE-SPECIFIC ERRORS ##
        # Note that device-specific errors also include all positive numbers.
        # -400 BLOCK: QUERY ERRORS ##

        # OTHER ERRORS ##

        #: Raised when the instrument detects that it has been turned from
        #: off to on.
        power_on = -500  # Yes, SCPI 1999 defines the instrument turning on as
        # an error. Yes, this makes my brain hurt.
        user_request_event = -600
        request_control_event = -700
        operation_complete = -800

    def check_error_queue(self):
        """
        Checks and clears the error queue for this device, returning a list of
        :class:`SCPIInstrument.ErrorCodes` or `int` elements for each error
        reported by the connected instrument.
        """
        # pylint: disable=fixme
        # TODO: use SYST:ERR:ALL instead of SYST:ERR:CODE:ALL to get
        #       messages as well. Should be just a bit more parsing, but the
        #       SCPI standard isn't clear on how the pairs are represented,
        #       so it'd be helpful to have an example first.
        err_list = map(int, self.query("SYST:ERR:CODE:ALL?").split(","))
        return [
            self.ErrorCodes[err] if isinstance(err, self.ErrorCodes) else err
            for err in err_list
            if err != self.ErrorCodes.no_error
        ]

    # DISPLAY COMMANDS ##

    @property
    def display_brightness(self):
        """
        Brightness of the display on the connected instrument, represented as
        a float ranging from 0 (dark) to 1 (full brightness).

        :type: `float`
        """
        return float(self.query("DISP:BRIG?"))

    @display_brightness.setter
    def display_brightness(self, newval):
        if newval < 0 or newval > 1:
            raise ValueError("Display brightness must be a number between 0"
                             " and 1.")
        self.sendcmd("DISP:BRIG {}".format(newval))

    @property
    def display_contrast(self):
        """
        Contrast of the display on the connected instrument, represented as
        a float ranging from 0 (no contrast) to 1 (full contrast).

        :type: `float`
        """
        return float(self.query("DISP:CONT?"))

    @display_contrast.setter
    def display_contrast(self, newval):
        if newval < 0 or newval > 1:
            raise ValueError("Display brightness must be a number between 0"
                             " and 1.")
        self.sendcmd("DISP:CONT {}".format(newval))
