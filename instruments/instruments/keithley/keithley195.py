#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Driver for the Keithley 195 digital multimeter
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division

import time
import struct
from enum import Enum, IntEnum

import quantities as pq

from instruments.abstract_instruments import Multimeter

# CLASSES #####################################################################


class Keithley195(Multimeter):

    """
    The Keithley 195 is a 5 1/2 digit auto-ranging digital multimeter. You can
    find the full specifications list in the `Keithley 195 user's guide`_.

    Example usage:

    >>> import instruments as ik
    >>> import quantities as pq
    >>> dmm = ik.keithley.Keithley195.open_gpibusb('/dev/ttyUSB0', 12)
    >>> print dmm.measure(dmm.Mode.resistance)

    .. _Keithley 195 user's guide: http://www.keithley.com/data?asset=803
    """

    def __init__(self, filelike):
        super(Keithley195, self).__init__(filelike)
        self.sendcmd('YX')  # Removes the termination CRLF
        self.sendcmd('G1DX')  # Disable returning prefix and suffix

    # ENUMS ##

    class Mode(IntEnum):
        """
        Enum containing valid measurement modes for the Keithley 195
        """
        voltage_dc = 0
        voltage_ac = 1
        resistance = 2
        current_dc = 3
        current_ac = 4

    class TriggerMode(IntEnum):
        """
        Enum containing valid trigger modes for the Keithley 195
        """
        talk_continuous = 0
        talk_one_shot = 1
        get_continuous = 2
        get_one_shot = 3
        x_continuous = 4
        x_one_shot = 5
        ext_continuous = 6
        ext_one_shot = 7

    class ValidRange(Enum):
        """
        Enum containing valid range settings for the Keithley 195
        """
        voltage_dc = (20e-3, 200e-3, 2, 20, 200, 1000)
        voltage_ac = (20e-3, 200e-3, 2, 20, 200, 700)
        current_dc = (20e-6, 200e-6, 2e-3, 20e-3, 200e-3, 2)
        current_ac = (20e-6, 200e-6, 2e-3, 20e-3, 200e-3, 2, 2)
        resistance = (20, 200, 2000, 20e3, 200e3, 2e6, 20e6)

    # PROPERTIES #

    @property
    def mode(self):
        """
        Gets/sets the measurement mode for the Keithley 195. The base model
        only has DC voltage and resistance measurements. In order to use AC
        voltage, DC current, and AC current measurements your unit must be
        equiped with option 1950.

        Example use:

        >>> import instruments as ik
        >>> dmm = ik.keithley.Keithley195.open_gpibusb('/dev/ttyUSB0', 12)
        >>> dmm.mode = dmm.Mode.resistance

        :type: `Keithley195.Mode`
        """
        return self.parse_status_word(self.get_status_word())['mode']

    @mode.setter
    def mode(self, newval):
        if isinstance(newval, str):
            newval = self.Mode[newval]
        if not isinstance(newval, Keithley195.Mode):
            raise TypeError("Mode must be specified as a Keithley195.Mode "
                            "value, got {} instead.".format(newval))
        self.sendcmd('F{}DX'.format(newval.value))

    @property
    def trigger_mode(self):
        """
        Gets/sets the trigger mode of the Keithley 195.

        There are two different trigger settings for four different sources.
        This means there are eight different settings for the trigger mode.

        The two types are continuous and one-shot. Continuous has the instrument
        continuously sample the resistance. One-shot performs a single
        resistance measurement.

        The three trigger sources are on talk, on GET, and on "X". On talk
        refers to addressing the instrument to talk over GPIB. On GET is when
        the instrument receives the GPIB command byte for "group execute
        trigger". On "X" is when one sends the ASCII character "X" to the
        instrument. This character is used as a general execute to confirm
        commands send to the instrument. In InstrumentKit, "X" is sent after
        each command so it is not suggested that one uses on "X" triggering.
        Last, is external triggering. This is the port on the rear of the
        instrument. Refer to the manual for electrical characteristics of this
        port.

        :type: `Keithley195.TriggerMode`
        """
        return self.parse_status_word(self.get_status_word())['trigger']

    @trigger_mode.setter
    def trigger_mode(self, newval):
        if isinstance(newval, str):
            newval = Keithley195.TriggerMode[newval]
        if not isinstance(newval, Keithley195.TriggerMode):
            raise TypeError('Drive must be specified as a '
                            'Keithley195.TriggerMode, got {} '
                            'instead.'.format(newval))
        self.sendcmd('T{}X'.format(newval.value))

    @property
    def relative(self):
        """
        Gets/sets the zero command (relative measurement) mode of the
        Keithley 195.

        As stated in the manual: The zero mode serves as a means for a baseline
        suppression. When the correct zero command is send over the bus, the
        instrument will enter the zero mode, as indicated by the front panel
        ZERO indicator light. All reading displayed or send over the bus while
        zero is enabled are the difference between the stored baseline adn the
        actual voltage level. For example, if a 100mV baseline is stored, 100mV
        will be subtracted from all subsequent readings as long as the zero mode
        is enabled. The value of the stored baseline can be as little as a few
        microvolts or as large as the selected range will permit.

        See the manual for more information.

        :type: `bool`
        """
        return self.parse_status_word(self.get_status_word())['relative']

    @relative.setter
    def relative(self, newval):
        if not isinstance(newval, bool):
            raise TypeError('Relative mode must be a boolean.')
        self.sendcmd('Z{}DX'.format(int(newval)))

    @property
    def input_range(self):
        """
        Gets/sets the range of the Keithley 195 input terminals. The valid range
        settings depends on the current mode of the instrument. They are listed
        as follows:

        #) voltage_dc = ``(20e-3, 200e-3, 2, 20, 200, 1000)``

        #) voltage_ac = ``(20e-3, 200e-3, 2, 20, 200, 700)``

        #) current_dc = ``(20e-6, 200e-6, 2e-3, 20e-3, 200e-3, 2)``

        #) current_ac = ``(20e-6, 200e-6, 2e-3, 20e-3, 200e-3, 2)``

        #) resistance = ``(20, 200, 2000, 20e3, 200e3, 2e6, 20e6)``

        All modes will also accept the string ``auto`` which will set the 195
        into auto ranging mode.

        :rtype: `~quantities.quantity.Quantity` or `str`
        """
        index = self.parse_status_word(self.get_status_word())['range']
        if index == 0:
            return 'auto'
        else:
            mode = self.mode
            value = Keithley195.ValidRange[mode.name].value[index - 1]
            units = UNITS2[mode]
            return value * units

    @input_range.setter
    def input_range(self, newval):
        if isinstance(newval, str):
            if newval.lower() == 'auto':
                self.sendcmd('R0DX')
                return
            else:
                raise ValueError('Only "auto" is acceptable when specifying '
                                 'the input range as a string.')
        if isinstance(newval, pq.quantity.Quantity):
            newval = float(newval)

        mode = self.mode
        valid = Keithley195.ValidRange[mode.name].value
        if isinstance(newval, (float, int)):
            if newval in valid:
                newval = valid.index(newval) + 1
            else:
                raise ValueError('Valid range settings for mode {} '
                                 'are: {}'.format(mode, valid))
        else:
            raise TypeError('Range setting must be specified as a float, int, '
                            'or the string "auto", got {}'.format(type(newval)))
        self.sendcmd('R{}DX'.format(newval))

    # METHODS #

    def measure(self, mode=None):
        """
        Instruct the Keithley 195 to perform a one time measurement. The
        instrument will use default parameters for the requested measurement.
        The measurement will immediately take place, and the results are
        directly sent to the instrument's output buffer.

        Method returns a Python quantity consisting of a numpy array with the
        instrument value and appropriate units.

        With the 195, it is HIGHLY recommended that you seperately set the
        mode and let the instrument settle into the new mode. This can sometimes
        take longer than the 2 second delay added in this method. In our testing
        the 2 seconds seems to be sufficient but we offer no guarentee.

        Example usage:

        >>> import instruments as ik
        >>> import quantities as pq
        >>> dmm = ik.keithley.Keithley195.open_gpibusb('/dev/ttyUSB0', 12)
        >>> print(dmm.measure(dmm.Mode.resistance))

        :param mode: Desired measurement mode. This must always be specified
            in order to provide the correct return units.
        :type mode: `Keithley195.Mode`

        :return: A measurement from the multimeter.
        :rtype: `~quantities.quantity.Quantity`
        """
        if mode is not None:
            current_mode = self.mode
            if mode != current_mode:
                self.mode = mode
                if not self._testing:
                    time.sleep(2)  # Gives the instrument a moment to settle
        else:
            mode = self.mode
        value = self.query('')
        return float(value) * UNITS2[mode]

    def get_status_word(self):
        """
        Retreive the status word from the instrument. This contains information
        regarding the various settings of the instrument.

        The function `~Keithley195.parse_status_word` is designed to parse
        the return string from this function.

        :return: String containing setting information of the instrument
        :rtype: `str`
        """
        return self.query('U0DX')

    @staticmethod
    def parse_status_word(statusword):  # pylint: disable=too-many-locals
        """
        Parse the status word returned by the function
        `~Keithley195.get_status_word`.

        Returns a `dict` with the following keys:
        ``{trigger,mode,range,eoi,buffer,rate,srqmode,relative,delay,multiplex,
        selftest,dataformat,datacontrol,filter,terminator}``

        :param statusword: Byte string to be unpacked and parsed
        :type: `str`

        :return: A parsed version of the status word as a Python dictionary
        :rtype: `dict`
        """
        if statusword[:3] != '195':
            raise ValueError('Status word starts with wrong prefix, expected '
                             '195, got {}'.format(statusword))

        (trigger, function, input_range, eoi, buf, rate, srqmode, relative,
         delay, multiplex, selftest, data_fmt, data_ctrl, filter_mode,
         terminator) = struct.unpack('@4c2s3c2s5c2s', statusword[4:])

        return {'trigger': Keithley195.TriggerMode(int(trigger)),
                'mode': Keithley195.Mode(int(function)),
                'range': int(input_range),
                'eoi': (eoi == '1'),
                'buffer': buf,
                'rate': rate,
                'srqmode': srqmode,
                'relative': (relative == '1'),
                'delay': delay,
                'multiplex': (multiplex == '1'),
                'selftest': selftest,
                'dataformat': data_fmt,
                'datacontrol': data_ctrl,
                'filter': filter_mode,
                'terminator': terminator}

    def trigger(self):
        """
        Tell the Keithley 195 to execute all commands that it has received.

        Do note that this is different from the standard SCPI ``*TRG`` command
        (which is not supported by the 195 anyways).
        """
        self.sendcmd('X')

    def auto_range(self):
        """
        Turn on auto range for the Keithley 195.

        This is the same as calling ``Keithley195.input_range = 'auto'``
        """
        self.input_range = 'auto'

# UNITS #######################################################################

UNITS = {
    'DCV':  pq.volt,
    'ACV':  pq.volt,
    'ACA':  pq.amp,
    'DCA':  pq.amp,
    'OHM':  pq.ohm,
}

UNITS2 = {
    Keithley195.Mode.voltage_dc:  pq.volt,
    Keithley195.Mode.voltage_ac:  pq.volt,
    Keithley195.Mode.current_dc:  pq.amp,
    Keithley195.Mode.current_ac:  pq.amp,
    Keithley195.Mode.resistance:  pq.ohm,
}
