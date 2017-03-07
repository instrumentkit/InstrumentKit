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
from contextlib import contextmanager

import quantities as pq

from instruments.abstract_instruments import CryomagneticsInstrument

# CLASSES #####################################################################


class CryomagneticsLM510(CryomagneticsInstrument):
    """
    Represents a Cryomagnetics LM-510 liquid cryogen level monitor
    """
    CHANNELS = {1, 2}

    _channel_measurement_lock = Lock()  # type: Lock

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
            raise ValueError(
                "Attempted to set channel to {0}. Channel must "
                "be an integer of either 1 or 2".format(channel))
        command = "CHAN {0}".format(channel)
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
    def channel(self):
        """

        :return: The measurement channels for levels available to the level
        meter.
        """
        return self.Channel(1, self), self.Channel(2, self)

    def reset(self):
        """
        Bring the instrument to a safe, known state
        """
        self.query("*RST")

    @contextmanager
    def context_managed_measuring_lock(self):
        """
        Acquire the lock, and yield to the next function. Upon entry back
        into the function, release the channel measurement lock, no matter
        what exception was thrown in the process.

        This method prevents exceptions from creating hardware deadlocks.
        It is the recommended way to isolate channels during measurement.
        """
        self._channel_measurement_lock.acquire()
        try:
            yield
        finally:
            self._channel_measurement_lock.release()

    class Channel(object):
        """
        Contains methods for working with a single measurement channel on
        the level meter. This class is meant to be accessed using the
        ``channel`` property in `CryomagneticsLM510`
        """

        def __init__(
                self, channel_number, instrument
        ):
            """

            :param int channel_number: The number of the channel to measure.
                Must be 1 or 2
            :param Instrument instrument: the managed instrument
            """
            self._check_channel_number(channel_number)
            self.measurement_channel = channel_number
            self.instrument = instrument

        @property
        def data_ready(self):
            """

            :return: ``True`` if data is ready to be measured from the
                channel, otherwise ``False``.
            :raises: `RuntimeError` if the device measurement channel is not
                ``1`` or ``2``

            .. note::
                The variable ``data_ready_bit_index`` is used to take a
                bitwise ``&`` with the instrument status byte, in order to
                obtain the value of the correct bit to indicate whether the
                bit is ready or not.
            """
            status_byte = self.instrument.status_byte
            if self.measurement_channel == 1:
                data_ready_bit_index = 1
            elif self.measurement_channel == 2:
                data_ready_bit_index = 4
            else:
                raise RuntimeError(
                    "The channel was not 1 or 2. This is not allowed"
                )

            return (int(status_byte[0]) & data_ready_bit_index) > 0

        @property
        def measurement(self):
            """

            :return: The measured value of the level of cryogen
            :rtype: Quantity
            """
            with self.instrument.context_managed_measuring_lock():
                sleep(self.instrument.measurement_timeout)
                response = self.instrument.query(
                    "MEAS? {0}".format(self.measurement_channel)
                )

            return self.parse_response(response)

        @staticmethod
        def _check_channel_number(channel_number):
            """
            Check that the channel number is 1 or 2. If it isn't, throw a
            `RuntimeError`

            :param int channel_number: The number to check
            """
            if channel_number not in CryomagneticsLM510.CHANNELS:
                raise RuntimeError(
                    "The channel number of {0} is not a member of the "
                    "allowed channel set {1}".format(
                        channel_number, CryomagneticsLM510.CHANNELS)
                )

        @staticmethod
        def parse_response(response):
            """
            Extract the value and unit in which the response was returned,
            and match these values to a physical quantity

            :param str response: The response returned by making a measurement
            :return: The measured quantity
            :rtype: Quantity
            """
            value_match = re.search(r"^(\d|\.)*(?=\s)", response)
            unit_match = re.search(r"(?<=\s).*(?=$)", response)

            value = float(value_match.group(0))
            unit = CryomagneticsLM510.UNITS[unit_match.group(0)]

            return value * unit
