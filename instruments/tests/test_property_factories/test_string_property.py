#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing tests for the string property factories
"""

# IMPORTS ####################################################################

from __future__ import absolute_import

from nose.tools import eq_

from instruments.util_fns import string_property
from . import MockInstrument

# TEST CASES #################################################################

# pylint: disable=missing-docstring


def test_string_property_basics():
    class StringMock(MockInstrument):
        mock_property = string_property('MOCK')

    mock_inst = StringMock({'MOCK?': '"foobar"'})

    eq_(mock_inst.mock_property, 'foobar')

    mock_inst.mock_property = 'foo'
    eq_(mock_inst.value, 'MOCK?\nMOCK "foo"\n')


def test_string_property_different_bookmark_symbol():
    class StringMock(MockInstrument):
        mock_property = string_property('MOCK', bookmark_symbol='%^')

    mock_inst = StringMock({'MOCK?': '%^foobar%^'})

    eq_(mock_inst.mock_property, 'foobar')

    mock_inst.mock_property = 'foo'
    eq_(mock_inst.value, 'MOCK?\nMOCK %^foo%^\n')


def test_string_property_no_bookmark_symbol():
    class StringMock(MockInstrument):
        mock_property = string_property('MOCK', bookmark_symbol='')

    mock_inst = StringMock({'MOCK?': 'foobar'})

    eq_(mock_inst.mock_property, 'foobar')

    mock_inst.mock_property = 'foo'
    eq_(mock_inst.value, 'MOCK?\nMOCK foo\n')
