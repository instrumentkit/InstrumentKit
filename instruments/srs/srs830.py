#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides support for the SRS 830 lock-in amplifier.
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division

import math
import time
import warnings

from builtins import range, map
from enum import Enum, IntEnum

import numpy as np
import quantities as pq

from instruments.generic_scpi import SCPIInstrument
from instruments.abstract_instruments.comm import (
    GPIBCommunicator,
    SerialCommunicator,
    LoopbackCommunicator
)
from instruments.util_fns import (
    bool_property, bounded_unitful_property, enum_property, unitful_property
)

# CONSTANTS ###################################################################

VALID_SAMPLE_RATES = [2.0**n for n in range(-4, 10)]
VALID_SAMPLE_RATES += ["trigger"]

# CLASSES #####################################################################


class SRS830(SCPIInstrument):

    """
    Communicates with a Stanford Research Systems 830 Lock-In Amplifier.

    Example usage:

    >>> import instruments as ik
    >>> import quantities as pq
    >>> srs = ik.srs.SRS830.open_gpibusb('/dev/ttyUSB0', 1)
    >>> srs.frequency = 1000 * pq.hertz # Lock-In frequency
    >>> data = srs.take_measurement(1, 10) # 1Hz sample rate, 10 samples total
    """

    def __init__(self, filelike, outx_mode=None):  # pragma: no cover
        """
        Class initialization method.

        :param int outx_mode: Manually over-ride which ``OUTX`` command to send
            at startup. This is a command that needs to be sent as specified
            by the SRS830 manual. If left default, the correct ``OUTX`` command
            will be sent depending on what type of communicator self._file is.
        """
        super(SRS830, self).__init__(filelike)
        if outx_mode is 1:
            self.sendcmd("OUTX 1")
        elif outx_mode is 2:
            self.sendcmd("OUTX 2")
        else:
            if isinstance(self._file, GPIBCommunicator):
                self.sendcmd("OUTX 1")
            elif isinstance(self._file, SerialCommunicator):
                self.sendcmd("OUTX 2")
            elif isinstance(self._file, LoopbackCommunicator):
                pass
            else:
                warnings.warn("OUTX command has not been set. Instrument "
                              "behavour is unknown.", UserWarning)
    # ENUMS #

    class FreqSource(IntEnum):

        """
        Enum for the SRS830 frequency source settings.
        """
        external = 0
        internal = 1

    class Coupling(IntEnum):

        """
        Enum for the SRS830 channel coupling settings.
        """
        ac = 0
        dc = 1

    class BufferMode(IntEnum):
        """
        Enum for the SRS830 buffer modes.
        """
        one_shot = 0
        loop = 1

    class Mode(Enum):
        """
        Enum containing valid modes for the SRS 830
        """
        x = "x"
        y = "y"
        r = "r"
        theta = "theta"
        xnoise = "xnoise"
        ynoise = "ynoise"
        aux1 = "aux1"
        aux2 = "aux2"
        aux3 = "aux3"
        aux4 = "aux4"
        ref = "ref"
        ch1 = "ch1"
        ch2 = "ch2"
        none = "none"

    # CONSTANTS #

    _XYR_MODE_MAP = {Mode.x: 1, Mode.y: 2, Mode.r: 3}

    # PROPERTIES #

    frequency_source = enum_property(
        "FMOD",
        FreqSource,
        input_decoration=int,
        doc="""
        Gets/sets the frequency source used. This is either an external source,
            or uses the internal reference.

        :type: `SRS830.FreqSource`
        """
    )

    frequency = unitful_property(
        "FREQ",
        pq.hertz,
        valid_range=(0, None),
        doc="""
        Gets/sets the lock-in amplifier reference frequency.

        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of units Hertz.
        :type: `~quantities.Quantity` with units Hertz.
        """
    )

    phase, phase_min, phase_max = bounded_unitful_property(
        "PHAS",
        pq.degrees,
        valid_range=(-360 * pq.degrees, 730 * pq.degrees),
        doc="""
        Gets/set the phase of the internal reference signal.

        Set value should be -360deg <= newval < +730deg.

        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of units degrees.
        :type: `~quantities.Quantity` with units degrees.
        """
    )

    amplitude, amplitude_min, amplitude_max = bounded_unitful_property(
        "SLVL",
        pq.volt,
        valid_range=(0.004 * pq.volt, 5 * pq.volt),
        doc="""
        Gets/set the amplitude of the internal reference signal.

        Set value should be 0.004 <= newval <= 5.000

        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of units volts. Value should be specified as peak-to-peak.
        :type: `~quantities.Quantity` with units volts peak-to-peak.
        """
    )

    input_shield_ground = bool_property(
        "IGND",
        inst_true="1",
        inst_false="0",
        doc="""
        Function sets the input shield grounding to either 'float' or 'ground'.

        :type: `bool`
        """
    )

    coupling = enum_property(
        "ICPL",
        Coupling,
        input_decoration=int,
        doc="""
        Gets/sets the input coupling to either 'ac' or 'dc'.

        :type: `SRS830.Coupling`
        """
    )

    @property
    def sample_rate(self):
        r"""
        Gets/sets the data sampling rate of the lock-in.

        Acceptable set values are :math:`2^n` where :math:`n \in \{-4...+9\}` or
        the string `trigger`.

        :type: `~quantities.Quantity` with units Hertz.
        """
        value = int(self.query('SRAT?'))
        if value == 14:
            return "trigger"
        return pq.Quantity(VALID_SAMPLE_RATES[value], pq.Hz)

    @sample_rate.setter
    def sample_rate(self, newval):
        if isinstance(newval, str):
            newval = newval.lower()

        if newval in VALID_SAMPLE_RATES:
            self.sendcmd('SRAT {}'.format(VALID_SAMPLE_RATES.index(newval)))
        else:
            raise ValueError('Valid samples rates given by {} '
                             'and "trigger".'.format(VALID_SAMPLE_RATES))

    buffer_mode = enum_property(
        "SEND",
        BufferMode,
        input_decoration=int,
        doc="""
        Gets/sets the end of buffer mode.

        This sets the behaviour of the instrument when the data storage buffer
        is full. Setting to `one_shot` will stop acquisition, while `loop`
        will repeat from the start.

        :type: `SRS830.BufferMode`
        """
    )

    @property
    def num_data_points(self):
        """
        Gets the number of data sets in the SRS830 buffer.

        :type: `int`
        """
        resp = None
        i = 0
        while not resp and i < 10:
            resp = self.query('SPTS?').strip()
            i += 1
        if not resp:  # pragma: no cover
            raise IOError(
                "Expected integer response from instrument, got {}".format(
                    repr(resp))
            )
        return int(resp)

    data_transfer = bool_property(
        "FAST",
        inst_true="2",
        inst_false="0",
        doc="""
        Gets/sets the data transfer status.

        Note that this function only makes use of 2 of the 3 data transfer modes
        supported by the SRS830. The supported modes are FAST0 and FAST2. The
        other, FAST1, is for legacy systems which this package does not support.

        :type: `bool`
        """
    )

    # AUTO- METHODS #

    def auto_offset(self, mode):
        """
        Sets a specific channel mode to auto offset. This is the same as
        pressing the auto offset key on the display.

        It sets the offset of the mode specified to zero.

        :param mode: Target mode of auto_offset function. Valid inputs are
            {X|Y|R}.
        :type mode: `~SRS830.Mode` or `str`
        """
        if isinstance(mode, str):
            mode = mode.lower()
            mode = SRS830.Mode[mode]

        if mode not in self._XYR_MODE_MAP:
            raise ValueError('Specified mode not valid for this function.')

        mode = self._XYR_MODE_MAP[mode]

        self.sendcmd('AOFF {}'.format(mode))

    def auto_phase(self):
        """
        Sets the lock-in to auto phase.
        This does the same thing as pushing the auto phase button.

        Do not send this message again without waiting the correct amount
        of time for the lock-in to finish.
        """
        self.sendcmd('APHS')

    # META-METHODS #

    def init(self, sample_rate, buffer_mode):
        r"""
        Wrapper function to prepare the SRS830 for measurement.
        Sets both the data sampling rate and the end of buffer mode

        :param sample_rate: The desired sampling
            rate. Acceptable set values are :math:`2^n` where
            :math:`n \in \{-4...+9\}` in units Hertz or the string `trigger`.
        :type sample_rate: `~quantities.Quantity` or `str`

        :param `SRS830.BufferMode` buffer_mode: This sets the behaviour of the
            instrument when the data storage buffer is full. Setting to
            `one_shot` will stop acquisition, while `loop` will repeat from
            the start.
        """
        self.clear_data_buffer()
        self.sample_rate = sample_rate
        self.buffer_mode = buffer_mode

    def start_data_transfer(self):
        """
        Wrapper function to start the actual data transfer.
        Sets the transfer mode to FAST2, and triggers the data transfer
        to start after a delay of 0.5 seconds.
        """
        self.data_transfer = True
        self.start_scan()

    def take_measurement(self, sample_rate, num_samples):
        """
        Wrapper function that allows you to easily take measurements with a
        specified sample rate and number of desired samples.

        Function will call time.sleep() for the required amount of time it will
        take the instrument to complete this sampling operation.

        Returns a list containing two items, each of which are lists containing
        the channel data. The order is [[Ch1 data], [Ch2 data]].

        :param `int` sample_rate: Set the desired sample rate of the
            measurement. See `~SRS830.sample_rate` for more information.

        :param `int` num_samples: Number of samples to take.

        :rtype: `list`
        """
        if num_samples > 16383:
            raise ValueError('Number of samples cannot exceed 16383.')

        sample_time = math.ceil(num_samples / sample_rate)

        self.init(sample_rate, SRS830.BufferMode['one_shot'])
        self.start_data_transfer()

        if not self._testing:
            time.sleep(sample_time + 0.1)

        self.pause()

        # The following should fail. We do this to force the instrument
        # to flush its internal buffers.
        # Note that this causes a redundant transmission, and should be fixed
        # in future versions.
        try:
            self.num_data_points
        except IOError:  # pragma: no cover
            pass

        ch1 = self.read_data_buffer('ch1')
        ch2 = self.read_data_buffer('ch2')

        return np.array([ch1, ch2])

    # OTHER METHODS #

    def set_offset_expand(self, mode, offset, expand):
        """
        Sets the channel offset and expand parameters.
        Offset is a percentage, and expand is given as a multiplication
        factor of 1, 10, or 100.

        :param mode: The channel mode that you wish to change the
            offset and/or the expand of. Valid modes are X, Y, and R.
        :type mode: `SRS830.Mode` or `str`

        :param float offset: Offset of the mode, given as a percent.
            offset = <-105...+105>.

        :param int expand: Expansion factor for the measurement. Valid input
            is {1|10|100}.
        """
        if isinstance(mode, str):
            mode = mode.lower()
            mode = SRS830.Mode[mode]

        if mode not in self._XYR_MODE_MAP:
            raise ValueError('Specified mode not valid for this function.')

        mode = self._XYR_MODE_MAP[mode]

        if not isinstance(offset, (int, float)):
            raise TypeError('Offset parameter must be an integer or a float.')
        if not isinstance(expand, (int, float)):
            raise TypeError('Expand parameter must be an integer or a float.')

        if (offset > 105) or (offset < -105):
            raise ValueError('Offset mustbe -105 <= offset <= +105.')

        valid = [1, 10, 100]
        if expand in valid:
            expand = valid.index(expand)
        else:
            raise ValueError('Expand must be 1, 10, 100.')

        self.sendcmd('OEXP {},{},{}'.format(mode, int(offset), expand))

    def start_scan(self):
        """
        After setting the data transfer on via the dataTransfer function,
        this is used to start the scan. The scan starts after a delay of
        0.5 seconds.
        """
        self.sendcmd('STRD')

    def pause(self):
        """
        Has the instrument pause data capture.
        """
        self.sendcmd('PAUS')

    _data_snap_modes = {
        Mode.x: 1, Mode.y: 2, Mode.r: 3, Mode.theta: 4, Mode.aux1: 5,
        Mode.aux2: 6, Mode.aux3: 7, Mode.aux4: 8, Mode.ref: 9,
        Mode.ch1: 10, Mode.ch2: 11
    }

    def data_snap(self, mode1, mode2):
        """
        Takes a snapshot of the current parameters are defined by variables
        mode1 and mode2.

        For combinations (X,Y) and (R,THETA), they are taken at the same
        instant. All other combinations are done sequentially, and may
        not represent values taken from the same timestamp.

        Returns a list of floats, arranged in the order that they are
        given in the function input parameters.

        :param mode1: Mode to take data snap for channel 1. Valid inputs are
            given by: {X|Y|R|THETA|AUX1|AUX2|AUX3|AUX4|REF|CH1|CH2}
        :type mode1: `~SRS830.Mode` or `str`
        :param mode2: Mode to take data snap for channel 2. Valid inputs are
            given by: {X|Y|R|THETA|AUX1|AUX2|AUX3|AUX4|REF|CH1|CH2}
        :type mode2: `~SRS830.Mode` or `str`

        :rtype: `list`
        """
        if isinstance(mode1, str):
            mode1 = mode1.lower()
            mode1 = SRS830.Mode[mode1]
        if isinstance(mode2, str):
            mode2 = mode2.lower()
            mode2 = SRS830.Mode[mode2]

        if ((mode1 not in self._data_snap_modes) or
                (mode2 not in self._data_snap_modes)):
            raise ValueError('Specified mode not valid for this function.')

        mode1 = self._XYR_MODE_MAP[mode1]
        mode2 = self._XYR_MODE_MAP[mode2]

        if mode1 == mode2:
            raise ValueError('Both parameters for the data snapshot are the '
                             'same.')

        result = self.query('SNAP? {},{}'.format(mode1, mode2))
        return list(map(float, result.split(',')))

    _valid_read_data_buffer = {Mode.ch1: 1, Mode.ch2: 2}

    def read_data_buffer(self, channel):
        """
        Reads the entire data buffer for a specific channel.
        Transfer is done in ASCII mode. Although binary would be faster,
        this is not currently implemented.

        Returns a list of floats containing instrument's measurements.

        :param channel: Channel data buffer to read from. Valid channels are
            given by {CH1|CH2}.
        :type channel: `SRS830.Mode` or `str`

        :rtype: `list`
        """
        if isinstance(channel, str):
            channel = channel.lower()
            channel = SRS830.Mode[channel]

        if channel not in self._valid_read_data_buffer:
            raise ValueError('Specified mode not valid for this function.')

        channel = self._valid_read_data_buffer[channel]

        N = self.num_data_points  # Retrieve number of data points stored

        # Query device for entire buffer, returning in ASCII, then
        # converting to a list of floats before returning to the
        # calling method
        return np.fromstring(
            self.query('TRCA?{},0,{}'.format(channel, N)).strip(),
            sep=','
        )

    def clear_data_buffer(self):
        """
        Clears the data buffer of the SRS830.
        """
        self.sendcmd('REST')

    _valid_channel_display = [
        {  # channel1
            Mode.x: 0, Mode.r: 1, Mode.xnoise: 2, Mode.aux1: 3, Mode.aux2: 4
        },
        {  # channel2
            Mode.y: 0, Mode.theta: 1, Mode.ynoise: 2, Mode.aux3: 3,
            Mode.aux4: 4
        }
    ]

    _valid_channel_ratio = [
        {Mode.none: 0, Mode.aux1: 1, Mode.aux2: 2},  # channel1
        {Mode.none: 0, Mode.aux3: 1, Mode.aux4: 2}  # channel2
    ]

    _valid_channel = {Mode.ch1: 1, Mode.ch2: 2}

    def set_channel_display(self, channel, display, ratio):
        """
        Sets the display of the two channels.
        Channel 1 can display X, R, X Noise, Aux In 1, Aux In 2
        Channel 2 can display Y, Theta, Y Noise, Aux In 3, Aux In 4

        Channel 1 can have ratio of None, Aux In 1, Aux In 2
        Channel 2 can have ratio of None, Aux In 3, Aux In 4

        :param channel: Channel you wish to set the display of. Valid input is
            one of {CH1|CH2}.
        :type channel: `~SRS830.Mode` or `str`

        :param display: Setting the channel will be changed to. Valid
            input is one of {X|Y|R|THETA|XNOISE|YNOISE|AUX1|AUX2|AUX3|AUX4}
        :type display: `~SRS830.Mode` or `str`

        :param ratio: Desired ratio setting for this channel. Valid input
            is one of {NONE|AUX1|AUX2|AUX3|AUX4}
        :type ratio: `~SRS830.Mode` or `str`
        """
        if isinstance(channel, str):
            channel = channel.lower()
            channel = SRS830.Mode[channel]
        if isinstance(display, str):
            display = display.lower()
            display = SRS830.Mode[display]
        if isinstance(ratio, str):
            ratio = ratio.lower()
            ratio = SRS830.Mode[ratio]

        if channel not in self._valid_channel:
            raise ValueError('Specified channel not valid for this function.')

        channel = self._valid_channel[channel]

        if display not in self._valid_channel_display[channel - 1]:
            raise ValueError('Specified display mode not valid for this '
                             'function.')
        if ratio not in self._valid_channel_ratio[channel - 1]:
            raise ValueError('Specified display ratio not valid for this '
                             'function.')

        display = self._valid_channel_display[channel - 1][display]
        ratio = self._valid_channel_ratio[channel - 1][ratio]

        self.sendcmd('DDEF {},{},{}'.format(channel, display, ratio))
