# -*- coding: utf-8 -*-
"""
Cryomagnetics is interesting when it comes to serial communication.
Cryomagnetics devices will echo the command sent to the device, followed by
``\\r\\n``, followed by the response, followed by another ``\\r\\n``.
Consequently, the vanilla serial communicator needs to be subclassed in order
to allow proper serial communication to happen
"""

# IMPORTS #####################################################################
from __future__ import absolute_import

import re
from threading import Lock
from instruments.abstract_instruments.comm.serial_communicator \
        import SerialCommunicator

# CLASSES #####################################################################


class CryomagneticsSerialCommunicator(SerialCommunicator):
    """
    Subclasses the serial communicator and provides the correct logic to query
    the instrument
    """
    _querying_lock = Lock()

    def __init__(self, conn):
        SerialCommunicator.__init__(self, conn)
        self._maximum_message_size = 140

    # PROPERTIES #

    @property
    def maximum_message_size(self):
        """
        The largest expected message size, in number of bytes,
        that is to be returned by a Cryomagnetics instrument. The message
        size includes both the echoed command, terminators, and the
        instrument response. By default, this is 140 bytes. This corresponds
        to a message limit of 140 ASCII characters.

        .. note::

            Several commands can be sent at once to a cryomagnetics
            instrument, with each command separated by a semicolon. This can
            push the response length over 140 characters. In that case, the
            maximum message size may need to be set higher

        .. todo::

            Investigate a batching system to place multiple commands sent
            within a short timespan into a single command, and return the
            responses appropriately. The query method would then likely be
            based on a priority queue

        :return: The maximum message size in characters
        :rtype: int
        """
        return self._maximum_message_size

    # METHODS #

    @maximum_message_size.setter
    def maximum_message_size(self, new_size):
        """
        Set the maximum message size that will be read out by the communicator

        :param int new_size: The new size to be read out
        """
        self._maximum_message_size = new_size

    def seek(self, offset):
        """
        Go to a particular point in the data stream. This is not implemented
        in this communicator

        :param offset: The amount of bytes to fast forward
        """
        raise NotImplementedError

    def tell(self):
        """
        Get the current positional offset for the data stream. This is not
        implemented in this communicator
        """
        raise NotImplementedError

    def _query(self, msg, size=-1):
        """
        This is the implementation of ``query`` for communicating with
        Cryomagnetics instruments over serial connections. This function is,
        in turn, wrapped by the concrete method `AbstractCommunicator.query` to
        provide consistent logging functionality across all communication
        layers.

        :param str msg: The query message to send to the instrument
        :param int size: The number of bytes to read back from the
            instrument response. If the size is -1, the size will be assumed
            to be equal to
            `CryomagneticsSerialCommunicator.maximum_message_size`
        :return: The instrument response to the query
        :rtype: `str`
        """
        size_to_read = self._get_required_message_size(size)

        self._querying_lock.acquire()
        self.terminator = '\r'
        self.write(msg + self.terminator)
        self.terminator = '\r\n'
        response = self.read(size=size_to_read)
        self._querying_lock.release()

        return self._parse_query(msg, response)

    def _get_required_message_size(self, size):
        """
        If the size is not negative, return the message size. Otherwise,
        return the current maximum message size

        :param int size: The size value to parse
        :return: The number of bytes that will be read out of the serial port
        :rtype: int
        """
        if size < 0:
            return self.maximum_message_size
        else:
            return size

    def _parse_query(self, command, response):
        """
        After receiving the response from the device, extract the echoed
        command and the device response. Check that the echoed command
        matches the command sent to the device, and return the response

        :param str command: The command which was sent to the instrument
        :param str response: The raw response from the device, with echoed
            command and terminators
        :return: The response
        :rtype: str
        :raises `RuntimeError` if the response or query cannot be retrieved,
            or if the echoed command does not match the actual device command
        """
        echoed_command = re.search(r"^.*(?=\r\n)", response)
        response_from_instrument = re.search(
            r"(?<=\r\n).*?(?=\r\n$)", response
        )

        if echoed_command is None:
            raise RuntimeError(
                "Cryomagnetics serial communicator %s did find echoed "
                "command %s." % (self, command)
            )
        elif response_from_instrument is None:
            raise RuntimeError(
                "Cryomagnetics serial communicator %s did not find an "
                "instrument response in response %s" % (self, response)
            )

        if command != echoed_command.group(0):
            raise RuntimeError(
                "The echoed command %s from cryomagnetics serial "
                "communicator %s does not match the command %s sent to the "
                "device" % (echoed_command.group(0), self, command)
            )

        return response_from_instrument.group(0)
