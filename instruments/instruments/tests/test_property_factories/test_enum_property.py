#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing tests for the enum property factories
"""

# IMPORTS ####################################################################

from __future__ import absolute_import

from enum import Enum, IntEnum
from nose.tools import raises, eq_

from instruments.util_fns import enum_property
from . import MockInstrument

# TEST CASES #################################################################

# pylint: disable=missing-docstring


def test_enum_property():
    class SillyEnum(Enum):
        a = 'aa'
        b = 'bb'

    class EnumMock(MockInstrument):
        a = enum_property('MOCK:A', SillyEnum)
        b = enum_property('MOCK:B', SillyEnum)

    mock_inst = EnumMock({'MOCK:A?': 'aa', 'MOCK:B?': 'bb'})

    eq_(mock_inst.a, SillyEnum.a)
    eq_(mock_inst.b, SillyEnum.b)

    # Test EnumValues, string values and string names.
    mock_inst.a = SillyEnum.b
    mock_inst.b = 'a'
    mock_inst.b = 'bb'

    eq_(mock_inst.value, 'MOCK:A?\nMOCK:B?\nMOCK:A bb\nMOCK:B aa\nMOCK:B bb\n')


@raises(ValueError)
def test_enum_property_invalid():
    class SillyEnum(Enum):
        a = 'aa'
        b = 'bb'

    class EnumMock(MockInstrument):
        a = enum_property('MOCK:A', SillyEnum)

    mock_inst = EnumMock({'MOCK:A?': 'aa', 'MOCK:B?': 'bb'})

    mock_inst.a = 'c'


def test_enum_property_set_fmt():
    class SillyEnum(Enum):
        a = 'aa'

    class EnumMock(MockInstrument):
        a = enum_property('MOCK:A', SillyEnum, set_fmt="{}={}")

    mock_instrument = EnumMock()

    mock_instrument.a = 'aa'
    eq_(mock_instrument.value, 'MOCK:A=aa\n')


def test_enum_property_input_decoration():
    class SillyEnum(Enum):
        a = 'aa'

    class EnumMock(MockInstrument):

        @staticmethod
        def _input_decorator(_):
            return 'aa'
        a = enum_property(
            'MOCK:A',
            SillyEnum,
            input_decoration=_input_decorator
        )

    mock_instrument = EnumMock({'MOCK:A?': 'garbage'})

    eq_(mock_instrument.a, SillyEnum.a)


def test_enum_property_input_decoration_not_a_function():
    class SillyEnum(IntEnum):
        a = 1

    class EnumMock(MockInstrument):

        a = enum_property(
            'MOCK:A',
            SillyEnum,
            input_decoration=int
        )

    mock_instrument = EnumMock({'MOCK:A?': '1'})

    eq_(mock_instrument.a, SillyEnum.a)


def test_enum_property_output_decoration():
    class SillyEnum(Enum):
        a = 'aa'

    class EnumMock(MockInstrument):

        @staticmethod
        def _output_decorator(_):
            return 'foobar'
        a = enum_property(
            'MOCK:A',
            SillyEnum,
            output_decoration=_output_decorator
        )

    mock_instrument = EnumMock()

    mock_instrument.a = SillyEnum.a

    eq_(mock_instrument.value, 'MOCK:A foobar\n')


def test_enum_property_output_decoration_not_a_function():
    class SillyEnum(Enum):
        a = '.23'

    class EnumMock(MockInstrument):

        a = enum_property(
            'MOCK:A',
            SillyEnum,
            output_decoration=float
        )

    mock_instrument = EnumMock()

    mock_instrument.a = SillyEnum.a

    eq_(mock_instrument.value, 'MOCK:A 0.23\n')


@raises(AttributeError)
def test_enum_property_writeonly_reading_fails():
    class SillyEnum(Enum):
        a = 'aa'

    class EnumMock(MockInstrument):
        a = enum_property('MOCK:A', SillyEnum, writeonly=True)

    mock_instrument = EnumMock()

    _ = mock_instrument.a


def test_enum_property_writeonly_writing_passes():
    class SillyEnum(Enum):
        a = 'aa'

    class EnumMock(MockInstrument):
        a = enum_property('MOCK:A', SillyEnum, writeonly=True)

    mock_instrument = EnumMock()

    mock_instrument.a = SillyEnum.a
    eq_(mock_instrument.value, 'MOCK:A aa\n')


@raises(AttributeError)
def test_enum_property_readonly_writing_fails():
    class SillyEnum(Enum):
        a = 'aa'

    class EnumMock(MockInstrument):
        a = enum_property('MOCK:A', SillyEnum, readonly=True)

    mock_instrument = EnumMock({'MOCK:A?': 'aa'})

    mock_instrument.a = SillyEnum.a


def test_enum_property_readonly_reading_passes():
    class SillyEnum(Enum):
        a = 'aa'

    class EnumMock(MockInstrument):
        a = enum_property('MOCK:A', SillyEnum, readonly=True)

    mock_instrument = EnumMock({'MOCK:A?': 'aa'})

    eq_(mock_instrument.a, SillyEnum.a)
    eq_(mock_instrument.value, 'MOCK:A?\n')
