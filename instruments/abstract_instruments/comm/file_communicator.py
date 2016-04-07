#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides a communication layer for an instrument with a file on the filesystem
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import errno
import io
import time
import logging

from builtins import str, bytes

from instruments.abstract_instruments.comm import AbstractCommunicator

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# CLASSES #####################################################################


class FileCommunicator(io.IOBase, AbstractCommunicator):

    """
    Wraps a `file` object, providing ``sendcmd`` and ``query`` methods,
    while passing everything else through.

    :param filelike: File or name of a file to be wrapped as a communicator.
        Any file-like object wrapped by this class **must** support both
        reading and writing. If using the `open` builtin function, the mode
        ``rb+`` is recommended, and has been tested to work with character
        devices under Linux.
    :type filelike: `str` or `file`
    """

    def __init__(self, filelike):
        super(FileCommunicator, self).__init__(self)
        if isinstance(filelike, str):  # pragma: no cover
            filelike = open(filelike, 'rb+')

        self._filelike = filelike
        self._terminator = "\n"
        self._testing = False

    # PROPERTIES #

    @property
    def address(self):
        """
        Gets the name of the filesystem file that this communicator has been
        opened against.

        :type: `str`
        """
        if hasattr(self._filelike, 'name'):
            return self._filelike.name
        else:
            return None

    @address.setter
    def address(self, newval):
        raise NotImplementedError("Changing addresses of a file communicator"
                                  " is not yet supported.")

    @property
    def terminator(self):
        """
        Gets/sets the end-of-line termination character.

        :type: `str`
        """
        return self._terminator

    @terminator.setter
    def terminator(self, newval):
        if isinstance(newval, bytes):
            newval = newval.decode("utf-8")
        if not isinstance(newval, str) or len(newval) > 1:
            raise TypeError("Terminator for socket communicator must be "
                            "specified as a single character string.")
        self._terminator = newval

    @property
    def timeout(self):
        """
        Getting and setting the timeout property for `FileCommunicator` is
        not supported.
        """
        raise NotImplementedError

    @timeout.setter
    def timeout(self, newval):
        raise NotImplementedError

    # FILE-LIKE METHODS #

    def close(self):
        """
        Close connection to the filesystem file.
        """
        try:
            self._filelike.close()
        except IOError as e:  # pragma: no cover
            logger.warning("Failed to close file, exception: %s", repr(e))

    def read_raw(self, size=-1):
        """
        Read bytes in from the file.

        :param int size: The number of bytes to be read in from the file
        :rtype: `bytes`
        """
        if size >= 0:
            return self._filelike.read(size)
        elif size == -1:
            result = bytes()
            c = b''
            while c != self._terminator.encode("utf-8"):
                c = self._filelike.read(1)
                if c == b'':
                    break
                if c != self._terminator.encode("utf-8"):
                    result += c
            return result
        else:
            raise ValueError("Must read a positive value of characters.")

    def write_raw(self, msg):
        """
        Write bytes to the file.

        :param bytes msg: Bytes to be written to file
        """
        self._filelike.write(msg)

    def seek(self, offset):
        """
        Seek to a specified offset in the file. Useful for when using a static
        file, but less so when communicating with a physical instrument
        via a unix socket.

        :param int offset: The offset to seek to
        """
        self._filelike.seek(offset)

    def tell(self):
        """
        Gets the file's current position.

        :rtype: `int`
        """
        return self._filelike.tell()

    def flush_input(self):
        """
        Flush the internal buffer to make sure everything has actually been
        written to the file. This can be equivalent to a no-op on some
        filelike objects.
        """
        self._filelike.flush()

    # METHODS #

    def _sendcmd(self, msg):
        """
        This is the implementation of ``sendcmd`` for communicating with
        files on a unix system. This function is in turn wrapped by the
        concrete method `AbstractCommunicator.sendcmd` to provide consistent
        logging functionality across all communication layers.

        :param str msg: The command message to send to the instrument
        """
        msg += self._terminator
        self.write(msg)
        try:
            self.flush()
        except IOError as e:
            logger.warning("Exception %s occured during flush().", repr(e))

    def _query(self, msg, size=-1):
        """
        This is the implementation of ``query`` for communicating with
        files on a unix system. This function is in turn wrapped by the
        concrete method `AbstractCommunicator.query` to provide consistent
        logging functionality across all communication layers.

        :param str msg: The query message to send to the instrument
        :param int size: The number of bytes to read back from the instrument
            response.
        :return: The instrument response to the query
        :rtype: `str`
        """
        self.sendcmd(msg)
        if not self._testing:
            time.sleep(0.02)  # Give the bus time to respond.
        resp = b""
        try:
            # FIXME: this is slow, but we do it to avoid unreliable
            #        filelike devices such as some usbtmc-class devices.
            while True:
                nextchar = self._filelike.read(1)
                if not nextchar:
                    break
                resp += nextchar
                if nextchar.endswith(self._terminator.encode("utf-8")):
                    resp = resp[:-len(self._terminator)]
                    break
        except IOError as ex:
            if ex.errno == errno.ETIMEDOUT:
                # We don't mind timeouts if resp is nonempty,
                # and will just return what we have.
                if not resp:
                    raise
            elif ex.errno != errno.EPIPE:
                raise  # Reraise the existing exception.
            else:  # Give a more helpful and specific exception.
                raise IOError(
                    "Pipe broken when reading from {}; this probably "
                    "indicates that the driver "
                    "providing the device file is unable to communicate with "
                    "the instrument. Consider restarting the instrument.".format(
                        self.address
                    ))
        return resp.decode("utf-8")
