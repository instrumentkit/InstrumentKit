#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides a loopback communicator, used for creating unit tests or for opening
test connections to explore the InstrumentKit API.
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import io
import sys

from builtins import input

from instruments.abstract_instruments.comm import AbstractCommunicator

# CLASSES #####################################################################


class LoopbackCommunicator(io.IOBase, AbstractCommunicator):

    """
    Used to provide a loopback connection for an instrument class. The most
    common use cases for this communicator are writing unit tests, opening
    test connections to explore the API without having the physical instrument
    connected, and testing the behaviour of code under development.
    """

    def __init__(self, stdin=None, stdout=None):
        AbstractCommunicator.__init__(self)
        self._terminator = '\n'
        self._stdout = stdout
        self._stdin = stdin

    # PROPERTIES #

    @property
    def address(self):
        """
        Gets the name of ``stdin``

        :return: `sys.stdin.name`
        """
        return sys.stdin.name

    @address.setter
    def address(self, newval):
        raise NotImplementedError()

    @property
    def terminator(self):
        """
        Gets/sets the termination character for the loopback communicator.
        This should be specified as a single character string.

        :type: `str`
        :return: The termination character
        """
        return self._terminator

    @terminator.setter
    def terminator(self, newval):
        if not isinstance(newval, str):
            raise TypeError("Terminator must be specified "
                            "as a single character string.")
        if len(newval) > 1:
            raise ValueError("Terminator for LoopbackCommunicator must only be "
                             "1 character long.")
        self._terminator = newval

    @property
    def timeout(self):
        """
        Gets the timeout for the loopback communicator. This will always
        return 0.

        :type: `int`
        """
        return 0

    @timeout.setter
    def timeout(self, newval):
        pass

    # FILE-LIKE METHODS #

    def close(self):
        """
        Close connection to stdin
        """
        try:
            self._stdin.close()
        except IOError:
            pass

    def read(self, size=-1):
        """
        Gets desired response command from stdin. If ``stdin`` is `None`, then
        the user will be prompted to enter a mock response in the Python
        interpreter.

        :param int size: Number of characters to read. Default value of -1
            will read until termination character is found.
        :rtype: `str`
        """
        if self._stdin is not None:
            if size >= 0:
                input_var = self._stdin.read(size)
                return input_var
            elif size == -1:
                result = bytearray()
                c = 0
                while c != self._terminator:
                    c = self._stdin.read(1)
                    if c == '':
                        break
                    if c != self._terminator:
                        result += c
                return bytes(result)
            else:
                raise ValueError('Must read a positive value of characters.')
        else:
            input_var = input("Desired Response: ")
        return input_var

    def write(self, msg):
        """
        Write message to the loopback communicator's stdout. If ``stdout`` is
        `None` then it will be simply printed to the Python interpreter
        console.

        :param str msg: The string to be written
        """
        if self._stdout is not None:
            self._stdout.write(msg)
        else:
            print(" <- {} ".format(repr(msg)))

    def seek(self, offset):  # pylint: disable=unused-argument,no-self-use
        """
        Go to a specific offset for the input data source.

        Not implemented for loopback communicator.
        """
        return NotImplemented

    def tell(self):  # pylint: disable=no-self-use
        """
        Get the current positional offset for the input data source.

        Not implemented for loopback communicator.
        """
        return NotImplemented

    def flush_input(self):
        """
        Flush the input buffer, discarding all remaining input contents.

        For the loopback communicator, this will do nothing and just `pass`.
        """
        pass

    # METHODS #

    def _sendcmd(self, msg):
        """
        This is the implementation of ``sendcmd`` for the loopback communicator.
        This function is in turn wrapped by the concrete method
        `AbstractCommunicator.sendcmd` to provide consistent logging
        functionality across all communication layers.

        :param str msg: The command message to send to the instrument
        """
        if msg is not '':
            msg = "{}{}".format(msg, self._terminator)
            self.write(msg)

    def _query(self, msg, size=-1):
        """
        This is the implementation of ``query`` for communicating with
        the loopback communicator. This function is in turn wrapped by
        the concrete method `AbstractCommunicator.query` to provide consistent
        logging functionality across all communication layers.

        :param str msg: The query message to send to the instrument
        :param int size: The number of bytes to read back from the instrument
            response.
        :return: The instrument response to the query
        :rtype: `str`
        """
        self.sendcmd(msg)
        resp = self.read(size)
        return resp
