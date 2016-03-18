#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing tests for the int property factories
"""

# IMPORTS ####################################################################

from __future__ import absolute_import

from nose.tools import raises, eq_

from instruments.util_fns import int_property
from . import MockInstrument

# TEST CASES #################################################################

# pylint: disable=missing-docstring


@raises(ValueError)
def test_int_property_outside_valid_set():
    class IntMock(MockInstrument):
        mock_property = int_property('MOCK', valid_set=set([1, 2]))

    mock_inst = IntMock()
    mock_inst.mock_property = 3


def test_int_property_valid_set():
    class IntMock(MockInstrument):
        int_property = int_property('MOCK', valid_set=set([1, 2]))

    mock_inst = IntMock({'MOCK?': '1'})

    eq_(mock_inst.int_property, 1)

    mock_inst.int_property = 2
    eq_(mock_inst.value, 'MOCK?\nMOCK 2\n')


def test_int_property_no_set():
    class IntMock(MockInstrument):
        int_property = int_property('MOCK')

    mock_inst = IntMock()

    mock_inst.int_property = 1

    eq_(mock_inst.value, 'MOCK 1\n')


@raises(AttributeError)
def test_int_property_writeonly_reading_fails():
    class IntMock(MockInstrument):
        int_property = int_property('MOCK', writeonly=True)

    mock_inst = IntMock()

    _ = mock_inst.int_property


def test_int_property_writeonly_writing_passes():
    class IntMock(MockInstrument):
        int_property = int_property('MOCK', writeonly=True)

    mock_inst = IntMock()

    mock_inst.int_property = 1
    eq_(mock_inst.value, 'MOCK {:d}\n'.format(1))


@raises(AttributeError)
def test_int_property_readonly_writing_fails():
    class IntMock(MockInstrument):
        int_property = int_property('MOCK', readonly=True)

    mock_inst = IntMock({'MOCK?': '1'})

    mock_inst.int_property = 1


def test_int_property_readonly_reading_passes():
    class IntMock(MockInstrument):
        int_property = int_property('MOCK', readonly=True)

    mock_inst = IntMock({'MOCK?': '1'})

    eq_(mock_inst.int_property, 1)


def test_int_property_format_code():
    class IntMock(MockInstrument):
        int_property = int_property('MOCK', format_code='{:e}')

    mock_inst = IntMock()

    mock_inst.int_property = 1
    eq_(mock_inst.value, 'MOCK {:e}\n'.format(1))
