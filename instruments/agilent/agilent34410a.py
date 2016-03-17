#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides support for the Agilent 34410a digital multimeter.
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division
from builtins import map

import quantities as pq

from instruments.generic_scpi import SCPIMultimeter

# CLASSES #####################################################################


class Agilent34410a(SCPIMultimeter):  # pylint: disable=abstract-method

    """
    The Agilent 34410a is a very popular 6.5 digit DMM. This class should also
    cover the Agilent 34401a, 34411a, as well as the backwards compatability
    mode in the newer Agilent/Keysight 34460a/34461a. You can find the full
    specifications for these instruments on the `Keysight website`_.

    Example usage:

    >>> import instruments as ik
    >>> import quantities as pq
    >>> dmm = ik.agilent.Agilent34410a.open_gpibusb('/dev/ttyUSB0', 1)
    >>> print(dmm.measure(dmm.Mode.resistance))

    .. _Keysight website: http://www.keysight.com/
    """

    def __init__(self, filelike):
        super(Agilent34410a, self).__init__(filelike)

    # PROPERTIES #

    @property
    def data_point_count(self):
        """
        Gets the total number of readings that are located in reading memory
        (RGD_STORE).

        :rtype: `int`
        """
        return int(self.query('DATA:POIN?'))

    # STATE MANAGEMENT METHODS #

    def init(self):
        """
        Switch device from "idle" state to "wait-for-trigger state".
        Measurements will begin when specified triggering conditions are met,
        following the receipt of the INIT command.

        Note that this command will also clear the previous set of readings
        from memory.
        """
        self.sendcmd('INIT')

    def abort(self):
        """
        Abort all measurements currently in progress.
        """
        self.sendcmd('ABOR')

    # MEMORY MANAGEMENT METHODS #

    def clear_memory(self):
        """
        Clears the non-volatile memory of the Agilent 34410a.
        """
        self.sendcmd('DATA:DEL NVMEM')

    def r(self, count):
        """
        Have the multimeter perform a specified number of measurements and then
        transfer them using a binary transfer method. Data will be cleared from
        instrument memory after transfer is complete. Data is transfered
        from the instrument in 64-bit double floating point precision format.

        :param int count: Number of samples to take.

        :rtype: `~quantities.quantity.Quantity` with `numpy.array`
        """
        mode = self.mode
        units = UNITS[mode]
        if not isinstance(count, int):
            raise TypeError('Parameter "count" must be an integer')
        if count == 0:
            msg = 'R?'
        else:
            msg = 'R? ' + str(count)
        self.sendcmd('FORM:DATA REAL,64')
        self.sendcmd(msg)
        data = self.binblockread(8, fmt=">d")
        return data * units

    # DATA READING METHODS #

    def fetch(self):
        """
        Transfer readings from instrument memory to the output buffer, and
        thus to the computer.
        If currently taking a reading, the instrument will wait until it is
        complete before executing this command.
        Readings are NOT erased from memory when using fetch. Use the R?
        command to read and erase data.
        Note that the data is transfered as ASCII, and thus it is not
        recommended to transfer a large number of
        data points using this method.

        :rtype: `list` of `~quantities.quantity.Quantity` elements
        """
        units = UNITS[self.mode]
        return list(map(float, self.query('FETC?').split(','))) * units

    def read_data(self, sample_count):
        """
        Transfer specified number of data points from reading memory
        (RGD_STORE) to output buffer.
        First data point sent to output buffer is the oldest.
        Data is erased after being sent to output buffer.

        :param int sample_count: Number of data points to be transfered to
            output buffer. If set to -1, all points in memory will be
            transfered.

        :rtype: `list` of `~quantities.quantity.Quantity` elements
        """
        if not isinstance(sample_count, int):
            raise TypeError('Parameter "sample_count" must be an integer.')

        if sample_count == -1:
            sample_count = self.data_point_count
        units = UNITS[self.mode]
        self.sendcmd('FORM:DATA ASC')
        data = self.query('DATA:REM? {}'.format(sample_count)).split(',')
        return list(map(float, data)) * units

    def read_data_nvmem(self):
        """
        Returns all readings in non-volatile memory (NVMEM).

        :rtype: `list` of `~quantities.quantity.Quantity` elements
        """
        units = UNITS[self.mode]
        data = list(map(float, self.query('DATA:DATA? NVMEM').split(',')))
        return data * units

    def read_last_data(self):
        """
        Retrieve the last measurement taken. This can be executed at any time,
        including when the instrument is currently taking measurements.
        If there are no data points available, the value ``9.91000000E+37`` is
        returned.

        :units: As specified by the data returned by the instrument.
        :rtype: `~quantities.quantity.Quantity`
        """
        data = self.query('DATA:LAST?')
        unit_map = {
            "VDC": "V",
            "VAC": "V",
        }

        if data == '9.91000000E+37':
            return int(data)
        else:
            data = data.split(" ")
            data[0] = float(data[0])
            if data[1] in unit_map:
                data[1] = unit_map[data[1]]
            return pq.Quantity(*data)

    def read_meter(self):
        """
        Switch device from "idle" state to "wait-for-trigger" state.
        Immediately after the trigger conditions are met, the data will be sent
        to the output buffer of the instrument.

        This is similar to calling `~Agilent34410a.init` and then immediately
        following `~Agilent34410a.fetch`.

        :rtype: `~quantities.Quantity`
        """
        mode = self.mode
        units = UNITS[mode]
        return float(self.query('READ?')) * units

# UNITS #######################################################################

UNITS = {
    Agilent34410a.Mode.capacitance: pq.farad,
    Agilent34410a.Mode.voltage_dc:  pq.volt,
    Agilent34410a.Mode.voltage_ac:  pq.volt,
    Agilent34410a.Mode.diode:       pq.volt,
    Agilent34410a.Mode.current_ac:  pq.amp,
    Agilent34410a.Mode.current_dc:  pq.amp,
    Agilent34410a.Mode.resistance:  pq.ohm,
    Agilent34410a.Mode.fourpt_resistance: pq.ohm,
    Agilent34410a.Mode.frequency:   pq.hertz,
    Agilent34410a.Mode.period:      pq.second,
    Agilent34410a.Mode.temperature: pq.kelvin,
    Agilent34410a.Mode.continuity:  1,
}
