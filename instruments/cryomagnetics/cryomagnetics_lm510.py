# -*- coding: utf-8 -*-
"""
Contains an implementation of the cryomagnetics LM 510 liquid cryogen level
monitor for InstrumentKit
"""

# IMPORTS #####################################################################
from __future__ import absolute_import

import re
from threading import Lock
from time import sleep

import quantities as pq

from instruments.abstract_instruments import CryomagneticsInstrument

# CLASSES #####################################################################


class CryomagneticsLM510(CryomagneticsInstrument):
    """
    Represents a Cryomagnetics LM-510 liquid cryogen level monitor
    """
    CHANNELS = {1, 2}

    channel_measurement_lock = Lock()  # type: Lock
    querying_lock = Lock()  # type: Lock

    measurement_timeout = 1

    UNITS = {
        "cm": pq.cm,
        "in": pq.inch,
        "%": pq.percent,
        "percent": pq.percent
    }

    @property
    def default_channel(self):
        """
        The Level meter has a default channel that is used to measure
        different cryogen levels. If a channel is not specified for a
        particular command, the command gets sent to the value of the
        default channel instead

        :return: The current default channel
        :rtype: int
        """
        return int(self.query("CHAN?"))

    @default_channel.setter
    def default_channel(self, channel):
        """
        Set the default channel to the desired channel

        :param int channel: The desired channel
        :raises: :exc:`ValueError` if the channel to be set is not in the
        set of allowed channels defined in ``CHANNELS``
        """
        if channel not in self.CHANNELS:
            raise ValueError("Attempted to set channel to %s. Channel must "
                             "be an integer of either 1 or 2", channel)
        command = "CHAN %d" % channel
        self.query(command)

    @property
    def status_byte(self):
        """
        Get a byte array representing the instrument's status byte. The
        status byte describes whether channel 1 or 2 are ready to make a
        measurement. The structure of the status byte is described in
        greater detail in the level meter's operating manual.

        :return: The current value of the status byte
        :rtype: bytes
        """
        byte_as_string = self.query("*STB?")
        return byte_as_string.encode('ascii')

    @property
    def channel_1_data_ready(self):
        """

        :return: ``True`` if channel 1 is ready to measure, otherwise ``False``
        :rtype: bool
        """
        status_byte = self.status_byte
        return (int(status_byte[0]) & 1) > 0

    @property
    def channel_2_data_ready(self):
        """

        :return: ``True`` if channel 2 is ready to measure, otherwise ``False``
        :rtype: bool
        """
        status_byte = self.status_byte
        return (int(status_byte[0]) & 4) > 0

    @property
    def channel_1_measurement(self):
        """
        Make a measurement on channel 1

        :return: The level of the cryogen.
        :rtype: Quantity
        """
        return self._measurement(1)

    @property
    def channel_2_measurement(self):
        """
        Make a measurement on channel 2

        :return: The level of cryogen measured by the probe connected to
            channel 2 in the meter
        :rtype: Quantity
        """
        return self._measurement(2)

    def reset(self):
        """
        Bring the instrument to a safe, known state
        """
        self.query("*RST")

    def _measurement(self, channel_number):
        """
        Make a measurement on a particular channel

        :param int channel_number: The channel on which the measurement is
            to be made
        :return: The measured value on that channel
        :rtype: Quantity
        """
        measurer = self._ChannelMeasurement(channel_number, self)
        response = measurer.measurement

        return self.parse_response(response)

    @staticmethod
    def parse_response(response):
        """
        Extract the value and unit in which the response was returned,
        and match these values to a physical quantity

        :param str response: The response returned by making a measurement
        :return: The measured quantity
        :rtype: Quantity
        """
        value_match = re.search("^(\d|\.)*(?=\s)", response)
        unit_match = re.search("(?<=\s).*(?=$)", response)

        value = float(value_match.group(0))
        unit = CryomagneticsLM510.UNITS[unit_match.group(0)]

        return_value = value * unit

        return return_value

    class _ChannelMeasurement(object):
        """
        Prepares a measurement of a channel, and returns a string stating
        what the measurement was.
        """

        def __init__(
                self, channel_number, instrument
        ):
            """

            :param int channel_number: The number of the channel to measure.
                Must be 1 or 2
            :param Instrument instrument: the managed instrument
            """
            self.channel = channel_number
            self.instrument = instrument

        @property
        def measurement(self):
            """

            :return: The string returned from the level measurement
            :rtype: str
            """
            self.instrument.channel_measurement_lock.acquire()
            sleep(self.instrument.measurement_timeout)

            response = self.instrument.query("MEAS? %d" % self.channel)

            self.instrument.channel_measurement_lock.release()
            return response
