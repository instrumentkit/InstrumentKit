#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing tests for the property factories
"""

# IMPORTS ####################################################################

from __future__ import absolute_import

from io import BytesIO

from enum import Enum
from nose.tools import raises, eq_
import mock
import quantities as pq

from instruments.util_fns import (
    rproperty, bool_property, enum_property, int_property, string_property,
    unitful_property, unitless_property, bounded_unitful_property
)


# CLASSES ####################################################################

# pylint: disable=missing-docstring

class MockInstrument(object):

    """
    Mock class that admits sendcmd/query but little else such that property
    factories can be tested by deriving from the class.
    """

    def __init__(self, responses=None):
        self._buf = BytesIO()
        self._responses = responses if responses is not None else {}

    @property
    def value(self):
        return self._buf.getvalue()

    def sendcmd(self, cmd):
        self._buf.write("{}\n".format(cmd))

    def query(self, cmd):
        self.sendcmd(cmd)
        return self._responses[cmd.strip()]

# TEST CASES #################################################################

# rproperty ##


def test_rproperty_basic():
    class Mock(MockInstrument):

        def __init__(self):
            super(Mock, self).__init__()
            self._value = 0

        def mockget(self):
            return self._value

        def mockset(self, newval):
            self._value = newval
        mockproperty = rproperty(fget=mockget, fset=mockset)

    mock_inst = Mock()
    mock_inst.mockproperty = 1
    eq_(mock_inst.mockproperty, 1)


@raises(AttributeError)
def test_rproperty_readonly_writing_fails():
    class Mock(MockInstrument):

        def __init__(self):
            super(Mock, self).__init__()
            self._value = 0

        def mockset(self, newval):  # pragma: no cover
            self._value = newval
        mockproperty = rproperty(fget=None, fset=mockset, readonly=True)

    mock_inst = Mock()
    mock_inst.mockproperty = 1


def test_rproperty_readonly_reading_passes():
    class Mock(MockInstrument):

        def __init__(self):
            super(Mock, self).__init__()
            self._value = 0

        def mockget(self):
            return self._value
        mockproperty = rproperty(fget=mockget, fset=None, readonly=True)

    mock_inst = Mock()
    eq_(mock_inst.mockproperty, 0)


@raises(AttributeError)
def test_rproperty_writeonly_reading_fails():
    class Mock(MockInstrument):

        def __init__(self):
            super(Mock, self).__init__()
            self._value = 0

        def mockget(self):  # pragma: no cover
            return self._value
        mockproperty = rproperty(fget=mockget, fset=None, writeonly=True)

    mock_inst = Mock()
    eq_(mock_inst.mockproperty, 0)


def test_rproperty_writeonly_writing_passes():
    class Mock(MockInstrument):

        def __init__(self):
            super(Mock, self).__init__()
            self._value = 0

        def mockset(self, newval):
            self._value = newval
        mockproperty = rproperty(fget=None, fset=mockset, writeonly=True)

    mock_inst = Mock()
    mock_inst.mockproperty = 1


@raises(ValueError)
def test_rproperty_readonly_and_writeonly():
    _ = rproperty(readonly=True, writeonly=True)
