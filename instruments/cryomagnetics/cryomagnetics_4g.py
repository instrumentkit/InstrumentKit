# -*- coding: utf-8 -*-
"""
Implements the cryomagnetics 4G superconducting magnet power supply
"""

# IMPORTS #####################################################################
from __future__ import absolute_import

import re
from time import sleep

import quantities as pq

from instruments.abstract_instruments.cryomagnetics_instrument \
    import CryomagneticsInstrument

# CLASSES #####################################################################


class Cryomagnetics4G(CryomagneticsInstrument):
    """
    Implements a Cryomagnetics 4G Superconducting magnet power supply.
    """
    CHANNELS = {1, 2}

    UNITS = {
        "A": pq.amp,
        "G": pq.gauss
    }

    REVERSE_UNITS = {
        pq.amp: "A",
        pq.gauss: "G"
    }

    instrument_measurement_wait = 0.5

    @property
    def unit(self):
        """
        The power supply is capable of expressing the output current going
        into the magnet in amperes, but it can also convert the current to a
        predicted magnetic field using a particular relation.

        :return: The units in which the power supply expresses its measurement
        """
        response = self.query("UNITS?")
        return self.UNITS[response]

    @unit.setter
    def unit(self, unit_to_set):
        """
        Set the unit to either amperes or gauss. The valid units to which
        this value can be set are the keys in the ``UNITS`` dictionary of
        this object

        :param str unit_to_set: The unit to set
        :raises: :exc:`ValueError` if the unit cannot be set
        """
        if unit_to_set not in self.UNITS.keys():
            raise ValueError("Attempted to set unit to an invalid value")
        self.query("UNITS %s" % unit_to_set)

    @property
    def current(self):
        """

        :return: The current in amperes being sent out of the power supply
        """
        self.unit = self.REVERSE_UNITS[pq.amp]
        sleep(self.instrument_measurement_wait)

        return self.parse_current_response(self.query("IOUT?"))

    @staticmethod
    def parse_current_response(response):
        """
        Extract the value and units out of the output current for the power
        supply.

        :param str response: The raw response coming out of the device
        :return: A physical quantity which represents the current or
            magnetic field that was measured
        :rtype: Quantity
        """
        value_match = re.search(r"^(\d|\.)*(?=(A|G))", response)
        unit_match = re.search(r".(?=$)", response)

        value = float(value_match.group(0))
        unit = Cryomagnetics4G.UNITS[unit_match.group(0)]

        return value * unit
