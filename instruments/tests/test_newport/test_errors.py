#!/usr/bin/env python
"""
Module containing tests for NewportError class
"""

# IMPORTS ####################################################################


import datetime

from instruments.newport.errors import NewportError


# TESTS ######################################################################


# pylint: disable=protected-access


def test_init_none():
    """Initialized with both arguments as `None`."""
    cls = NewportError()
    assert isinstance(cls._timestamp, datetime.timedelta)
    assert cls._errcode is None
    assert cls._axis is None


def test_init_with_timestamp():
    """Initialized with a time stamp."""
    timestamp = datetime.datetime.now()
    cls = NewportError(timestamp=timestamp)
    assert isinstance(cls._timestamp, datetime.timedelta)


def test_init_with_error_code():
    """Initialize with non-axis specific error code."""
    err_code = 7  # parameter out of range
    cls = NewportError(errcode=err_code)
    assert cls._axis is None
    assert cls._errcode == 7


def test_init_with_error_code_axis():
    """Initialize with axis-specific error code."""
    err_code = 313  # ax 3 not enabled
    cls = NewportError(errcode=err_code)
    assert cls._axis == 3
    assert cls._errcode == 13


def test_get_message():
    """Get the message for a given error code."""
    err_code = "7"
    cls = NewportError()
    assert cls.get_message(err_code) == cls.messageDict[err_code]


def test_timestamp():
    """Get the timestamp for a given error."""
    cls = NewportError()
    assert cls.timestamp == cls._timestamp


def test_errcode():
    """Get the error code reported by device."""
    cls = NewportError(errcode=7)
    assert cls.errcode == cls._errcode


def test_axis():
    """Get axis for given error code."""
    cls = NewportError(errcode=313)
    assert cls.axis == cls._axis
