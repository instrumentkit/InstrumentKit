#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides an abstract base class for file-like communication layer classes
"""

# IMPORTS ####################################################################

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc
import logging

from future.utils import with_metaclass

# CLASSES ####################################################################


class AbstractCommunicator(with_metaclass(abc.ABCMeta, object)):

    """
    Abstract base class for electrometer instruments.

    All applicable concrete instruments should inherit from this ABC to
    provide a consistent interface to the user.
    """

    # INITIALIZER #

    def __init__(self, *args, **kwargs):  # pylint: disable=unused-argument
        self._debug = False

        # Create a new logger for the module containing the concrete
        # subclass that we're a part of.
        self._logger = logging.getLogger(type(self).__module__)

        # Ensure that there's at least something setup to receive logs.
        self._logger.addHandler(logging.NullHandler())

    # FORMATTING METHODS #

    def __repr__(self):
        return "<{} object at 0x{:X} "\
            "connected to {}>".format(
                type(self).__name__, id(self), repr(self.address))

    # CONCRETE PROPERTIES #

    @property
    def debug(self):
        """
        Enables or disables debug support. If active, all messages sent to
        or received from this communicator are logged to the Python logging
        service, with the logger name given by the module of the current
        communicator.
        Generating log messages for each exchanged command is slow, so these
        log messages are suppressed by default.

        Note that you must turn on logging to at least the DEBUG level in order
        to see these messages. For instance:

        >>> import logging
        >>> logging.basicConfig(level=logging.DEBUG)
        """
        return self._debug

    @debug.setter
    def debug(self, newval):
        self._debug = bool(newval)

    # ABSTRACT PROPERTIES #

    @property
    @abc.abstractmethod
    def address(self):
        """
        Reads or changes the current address for this communicator.
        """
        raise NotImplementedError

    @address.setter
    @abc.abstractmethod
    def address(self, newval):
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def terminator(self):
        """
        Reads or changes the EOS termination.
        """
        raise NotImplementedError

    @terminator.setter
    @abc.abstractmethod
    def terminator(self, newval):
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def timeout(self):
        """
        Get the connection interface timeout.
        """
        raise NotImplementedError

    @timeout.setter
    @abc.abstractmethod
    def timeout(self, newval):
        raise NotImplementedError

    # ABSTRACT METHODS #

    @abc.abstractmethod
    def read_raw(self, size=-1):
        """
        Read bytes in from the connection.

        :param int size: The number of bytes to read in from the
            connection.

        :return: The read bytes
        :rtype: `bytes`
        """
        pass

    @abc.abstractmethod
    def write_raw(self, msg):
        """
        Write bytes to the connection.

        :param bytes msg: Bytes to be sent to the instrument over the
            connection.
        """
        pass

    @abc.abstractmethod
    def _sendcmd(self, msg):
        """
        Sends a message to the connected device, handling all proper
        termination characters and secondary commands as required.

        Note that this is called by :class:`AbstractCommunicator.sendcmd`,
        which also handles debug, event and capture support.
        """
        pass

    @abc.abstractmethod
    def _query(self, msg, size=-1):
        """
        Send a string to the connected instrument using sendcmd and read the
        response. This is an abstract method because there are situations where
        information contained in the sent command is needed for reading logic.

        An example of this is the Galvant Industries GPIB adapter where if
        you are connected to an older instrument and the query command does not
        contain a `?`, then the command `+read` needs to be send to force the
        instrument to send its response.

        Note that this is called by :class:`AbstractCommunicator.query`,
        which also handles debug, event and capture support.
        """
        pass

    @abc.abstractmethod
    def flush_input(self):
        """
        Instruct the communicator to flush the input buffer, discarding the
        entirety of its contents.
        """
        raise NotImplementedError

    # CONCRETE METHODS #

    def write(self, msg, encoding="utf-8"):
        """
        Write a string to the connection. This string will be converted
        to `bytes` using the provided encoding method.

        .. seealso:: To send `bytes` in Python 3, see `write_raw`.

        :param str msg: String to be sent to the instrument over the
            connection.
        :param str encoding: Encoding to apply on msg to convert the message
            into bytes
        """
        self.write_raw(msg.encode(encoding))

    def read(self, size=-1, encoding="utf-8"):
        """
        Read bytes in from the connection, returning a decoded string
        using the provided encoding method.

        .. seealso:: To read `bytes` in Python 3, see `read_raw`.

        :param int size: The number of bytes to read in from the
            connection.
        :param str encoding: Encoding that will be applied to the read bytes

        :return: The read string from the connection
        :rtype: `str`
        """
        return self.read_raw(size).decode(encoding)

    def sendcmd(self, msg):
        """
        Sends the incoming msg down to the wrapped file-like object
        but appends any other commands or termination characters required
        by the communication.

        This differs from the communicator .write method which directly exposes
        the communication channel without appending other data.
        """
        if self.debug:
            self._logger.debug(" <- %s", repr(msg))
        self._sendcmd(msg)

    def query(self, msg, size=-1):
        """
        Send a string to the connected instrument using sendcmd and read the
        response. This is an abstract method because there are situations where
        information contained in the sent command is needed for reading logic.

        An example of this is the Galvant Industries GPIB adapter where if
        you are connected to an older instrument and the query command does not
        contain a `?`, then the command `+read` needs to be send to force the
        instrument to send its response.
        """
        if self.debug:
            self._logger.debug(" <- %s", repr(msg))
        resp = self._query(msg, size)
        if self.debug:
            self._logger.debug(" -> %s", repr(resp))
        return resp
