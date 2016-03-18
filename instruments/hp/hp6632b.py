#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# hp6632b.py: Python class for the HP6632b power supply
#
# © 2014 Willem Dijkstra (wpd@xs4all.nl).
#
# This file is a part of the InstrumentKit project.
# Licensed under the AGPL version 3.
#
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
#
"""
Driver for the HP6632b DC power supply

Originally contributed and copyright held by Willem Dijkstra (wpd@xs4all.nl)

An unrestricted license has been provided to the maintainers of the Instrument
Kit project.
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division
from builtins import range

from enum import Enum, IntEnum
import quantities as pq

from instruments.generic_scpi.scpi_instrument import SCPIInstrument
from instruments.hp.hp6652a import HP6652a
from instruments.util_fns import (unitful_property, unitless_property,
                                  bool_property, enum_property, int_property)

# CLASSES #####################################################################


class HP6632b(SCPIInstrument, HP6652a):

    """
    The HP6632b is a system dc power supply with an output rating of 0-20V/0-5A,
    precision low current measurement and low output noise.

    According to the manual this class MIGHT be usable for any HP power supply
    with a model number

    - HP663Xb with X in {1, 2, 3, 4},
    - HP661Xc with X in {1,2, 3, 4} and
    - HP663X2A for X in {1, 3}, without the additional measurement capabilities.

    HOWEVER, it has only been tested by the author with HP6632b supplies.

    Example usage:

    >>> import instruments as ik
    >>> psu = ik.hp.HP6632b.open_gpibusb('/dev/ttyUSB0', 6)
    >>> psu.voltage = 10             # Sets voltage to 10V.
    >>> psu.output = True            # Enable output
    >>> psu.voltage
    array(10.0) * V
    >>> psu.voltage_trigger = 20     # Set transient trigger voltage
    >>> psu.init_output_trigger()    # Prime instrument to initiated state, ready for trigger
    >>> psu.trigger()                # Send trigger
    >>> psu.voltage
    array(10.0) * V
    """

    def __init__(self, filelike):
        super(HP6632b, self).__init__(filelike)

    # ENUMS ##

    class ALCBandwidth(IntEnum):
        """
        Enum containing valid ALC bandwidth modes for the hp6632b
        """
        normal = 1.5e4
        fast = 6e4

    class DigitalFunction(Enum):
        """
        Enum containing valid digital function modes for the hp6632b
        """
        remote_inhibit = 'RIDF'
        data = 'DIG'

    class DFISource(Enum):
        """
        Enum containing valid DFI sources for the hp6632b
        """
        questionable = 'QUES'
        operation = 'OPER'
        event_status_bit = 'ESB'
        request_service_bit = 'RQS'
        off = 'OFF'

    class ErrorCodes(IntEnum):
        """
        Enum containing generic-SCPI error codes along with codes specific
        to the HP6632b.
        """
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
        macro_error_180 = -180
        invalid_outside_macro_definition = -181
        invalid_inside_macro_definition = -183
        macro_parameter_error = -184

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

        # -200 BLOCK: EXECUTION ERRORS
        execution_error = -200
        data_out_of_range = -222
        too_much_data = -223
        illegal_parameter_value = -224
        out_of_memory = -225
        macro_error_270 = -270
        macro_execution_error = -272
        illegal_macro_label = -273
        macro_recursion_error = -276
        macro_redefinition_not_allowed = -277

        # -300 BLOCK: DEVICE-SPECIFIC ERRORS
        system_error = -310
        too_many_errors = -350

        # -400 BLOCK: QUERY ERRORS
        query_error = -400
        query_interrupted = -410
        query_unterminated = -420
        query_deadlocked = -430
        query_unterminated_after_indefinite_response = -440

        # DEVICE ERRORS
        ram_rd0_checksum_failed = 1
        ram_config_checksum_failed = 2
        ram_cal_checksum_failed = 3
        ram_state_checksum_failed = 4
        ram_rst_checksum_failed = 5
        ram_selftest = 10
        vdac_idac_selftest1 = 11
        vdac_idac_selftest2 = 12
        vdac_idac_selftest3 = 13
        vdac_idac_selftest4 = 14
        ovdac_selftest = 15
        digital_io_selftest = 80
        ingrd_recv_buffer_overrun = 213
        rs232_recv_framing_error = 216
        rs232_recv_parity_error = 217
        rs232_recv_overrun_error = 218
        front_panel_uart_overrun = 220
        front_panel_uart_framing = 221
        front_panel_uart_parity = 222
        front_panel_uart_buffer_overrun = 223
        front_panel_uart_timeout = 224
        cal_switch_prevents_cal = 401
        cal_password_incorrect = 402
        cal_not_enabled = 403
        computed_readback_cal_const_incorrect = 404
        computed_prog_cal_constants_incorrect = 405
        incorrect_seq_cal_commands = 406
        cv_or_cc_status_incorrect = 407
        output_mode_must_be_normal = 408
        too_many_sweep_points = 601
        command_only_applic_rs232 = 602
        curr_or_volt_fetch_incompat_with_last_acq = 603
        measurement_overrange = 604

    class RemoteInhibit(Enum):
        """
        Enum containing vlaid remote inhibit modes for the hp6632b.
        """
        latching = 'LATC'
        live = 'LIVE'
        off = 'OFF'

    class SenseWindow(Enum):
        """
        Enum containing valid sense window modes for the hp6632b.
        """
        hanning = 'HANN'
        rectangular = 'RECT'

    # PROPERTIES ##

    voltage_alc_bandwidth = enum_property(
        "VOLT:ALC:BAND",
        ALCBandwidth,
        input_decoration=lambda x: int(float(x)),
        readonly=True,
        doc="""
        Get the "automatic level control bandwidth" which for the HP66332A and
        HP6631-6634 determines if the output capacitor is in circuit. `Normal`
        denotes that it is, and `Fast` denotes that it is not.

        :type: `~HP6632b.ALCBandwidth`
        """
    )

    voltage_trigger = unitful_property(
        "VOLT:TRIG",
        pq.volt,
        doc="""
        Gets/sets the pending triggered output voltage.

        Note there is no bounds checking on the value specified.

        :units: As specified, or assumed to be :math:`\\text{V}` otherwise.
        :type: `float` or `~quantities.Quantity`
        """
    )

    current_trigger = unitful_property(
        "CURR:TRIG",
        pq.amp,
        doc="""
        Gets/sets the pending triggered output current.

        Note there is no bounds checking on the value specified.

        :units: As specified, or assumed to be :math:`\\text{A}` otherwise.
        :type: `float` or `~quantities.Quantity`
        """
    )

    init_output_continuous = bool_property(
        "INIT:CONT:SEQ1",
        "1",
        "0",
        doc="""
        Get/set the continuous output trigger. In this state, the power supply
        will remain in the initiated state, and respond continuously on new
        incoming triggers by applying the set voltage and current trigger
        levels.

        :type: `bool`
        """
    )

    current_sense_range = unitful_property(
        'SENS:CURR:RANGE',
        pq.ampere,
        doc="""
        Get/set the sense current range by the current max value.

        A current of 20mA or less selects the low-current range, a current
        value higher than that selects the high-current range. The low current
        range increases the low current measurement sensitivity and accuracy.

        :units: As specified, or assumed to be :math:`\\text{A}` otherwise.
        :type: `float` or `~quantities.quantity.Quantity`
        """
    )

    output_dfi = bool_property(
        'OUTP:DFI',
        '1',
        '0',
        doc="""
        Get/set the discrete fault indicator (DFI) output from the dc
        source. The DFI is an open-collector logic signal connected to the read
        panel FLT connection, that can be used to signal external devices when
        a fault is detected.

        :type: `bool`
        """
    )

    output_dfi_source = enum_property(
        "OUTP:DFI:SOUR",
        DFISource,
        doc="""
        Get/set the source for discrete fault indicator (DFI) events.

        :type: `~HP6632b.DFISource`
        """
    )

    output_remote_inhibit = enum_property(
        "OUTP:RI:MODE",
        RemoteInhibit,
        doc="""
        Get/set the remote inhibit signal. Remote inhibit is an external,
        chassis-referenced logic signal routed through the rear panel INH
        connection, which allows an external device to signal a fault.

        :type: `~HP6632b.RemoteInhibit`
        """
    )

    digital_function = enum_property(
        "DIG:FUNC",
        DigitalFunction,
        doc="""
        Get/set the inhibit+fault port to digital in+out or vice-versa.

        :type: `~HP6632b.DigitalFunction`
        """
    )

    digital_data = int_property(
        "DIG:DATA",
        valid_set=range(0, 8),
        doc="""
        Get/set digital in+out port to data. Data can be an integer from 0-7.

        :type: `int`
        """
    )

    sense_sweep_points = unitless_property(
        "SENS:SWE:POIN",
        doc="""
        Get/set the number of points in a measurement sweep.

        :type: `int`
        """
    )

    sense_sweep_interval = unitful_property(
        "SENS:SWE:TINT",
        pq.second,
        doc="""
        Get/set the digitizer sample spacing. Can be set from 15.6 us to 31200
        seconds, the interval will be rounded to the nearest 15.6 us increment.

        :units: As specified, or assumed to be :math:`\\text{s}` otherwise.
        :type: `float` or `~quantities.Quantity`
        """
    )

    sense_window = enum_property(
        "SENS:WIND",
        SenseWindow,
        doc="""
        Get/set the measurement window function.

        :type: `~HP6632b.SenseWindow`
        """
    )

    output_protection_delay = unitful_property(
        "OUTP:PROT:DEL",
        pq.second,
        doc="""
        Get/set the time between programming of an output change that produces
        a constant current condition and the recording of that condigition in
        the Operation Status Condition register. This command also delays over
        current protection, but not overvoltage protection.

        :units: As specified, or assumed to be :math:`\\text{s}` otherwise.
        :type: `float` or `~quantities.Quantity`
        """
    )

    # FUNCTIONS ##

    def init_output_trigger(self):
        """
        Set the output trigger system to the initiated state. In this state,
        the power supply will respond to the next output trigger command.
        """
        self.sendcmd('INIT:NAME TRAN')

    def abort_output_trigger(self):
        """
        Set the output trigger system to the idle state.
        """
        self.sendcmd('ABORT')

    # SCPIInstrument commands that need local overrides

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

    def check_error_queue(self):
        """
        Checks and clears the error queue for this device, returning a list of
        :class:`~SCPIInstrument.ErrorCodes` or `int` elements for each error
        reported by the connected instrument.
        """
        done = False
        result = []
        while not done:
            err = int(self.query('SYST:ERR?').split(',')[0])
            if err == self.ErrorCodes.no_error:
                done = True
            else:
                result.append(
                    self.ErrorCodes(err) if err in self.ErrorCodes else err)

        return result
