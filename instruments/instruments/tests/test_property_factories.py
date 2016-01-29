#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# test_util_fns.py: Tests various utility functions.
##
# © 2013-2015 Steven Casagrande (scasagrande@galvant.ca).
#
# This file is a part of the InstrumentKit project.
# Licensed under the AGPL version 3.
##
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
##

## IMPORTS ####################################################################

from __future__ import absolute_import

import quantities as pq
from io import BytesIO

from nose.tools import raises, eq_

from instruments.util_fns import (
    ProxyList, assume_units,
    rproperty, bool_property, enum_property, int_property, string_property,
    unitful_property, unitless_property
)

from enum import Enum

## CLASSES ####################################################################

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
        
## TEST CASES #################################################################

## rproperty ##

def test_rproperty_basic():
    class Mock(MockInstrument):
        def __init__(self):
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
            self._value = 0
        def mockset(self, newval): # pragma: no cover
            self._value = newval
        mockproperty = rproperty(fget=None, fset=mockset, readonly=True)
    
    mock_inst = Mock()
    mock_inst.mockproperty = 1

def test_rproperty_readonly_reading_passes():
    class Mock(MockInstrument):
        def __init__(self):
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
            self._value = 0
        def mockget(self): # pragma: no cover
            return self._value
        mockproperty = rproperty(fget=mockget, fset=None, writeonly=True)
    
    mock_inst = Mock()
    eq_(mock_inst.mockproperty, 0)

def test_rproperty_writeonly_writing_passes():
    class Mock(MockInstrument):
        def __init__(self):
            self._value = 0
        def mockset(self, newval):
            self._value = newval
        mockproperty = rproperty(fget=None, fset=mockset, writeonly=True)
    
    mock_inst = Mock()
    mock_inst.mockproperty = 1
    
@raises(ValueError)
def test_rproperty_readonly_and_writeonly():
    mockproperty = rproperty(readonly=True, writeonly=True)
    
## Bool Property Factories ##
    
def test_bool_property_basics():
    class BoolMock(MockInstrument):
        mock1 = bool_property('MOCK1', 'ON', 'OFF')
        mock2 = bool_property('MOCK2', 'YES', 'NO')
        
    mock = BoolMock({'MOCK1?': 'OFF', 'MOCK2?': 'YES'})
    
    eq_(mock.mock1, False)
    eq_(mock.mock2, True)
    
    mock.mock1 = True
    mock.mock2 = False
    
    eq_(mock.value, 'MOCK1?\nMOCK2?\nMOCK1 ON\nMOCK2 NO\n')
    
def test_bool_property_set_fmt():
    class BoolMock(MockInstrument):
        mock1 = bool_property('MOCK1', 'ON', 'OFF', set_fmt="{}={}")
    
    mock_instrument = BoolMock({'MOCK1?': 'OFF'})
    
    mock_instrument.mock1 = True
    
    eq_(mock_instrument.value, 'MOCK1=ON\n')

@raises(AttributeError)    
def test_bool_property_readonly_writing_fails():
    class BoolMock(MockInstrument):
        mock1 = bool_property('MOCK1', 'ON', 'OFF', readonly=True)
    
    mock_instrument = BoolMock({'MOCK1?': 'OFF'})
    
    mock_instrument.mock1 = True
    
def test_bool_property_readonly_reading_passes():
    class BoolMock(MockInstrument):
        mock1 = bool_property('MOCK1', 'ON', 'OFF', readonly=True)
    
    mock_instrument = BoolMock({'MOCK1?': 'OFF'})
    
    eq_(mock_instrument.mock1, False)

@raises(AttributeError)
def test_bool_property_writeonly_reading_fails():
    class BoolMock(MockInstrument):
        mock1 = bool_property('MOCK1', 'ON', 'OFF', writeonly=True)
    
    mock_instrument = BoolMock({'MOCK1?': 'OFF'})
    
    mock_instrument.mock1

def test_bool_property_writeonly_writing_passes():
    class BoolMock(MockInstrument):
        mock1 = bool_property('MOCK1', 'ON', 'OFF', writeonly=True)
    
    mock_instrument = BoolMock({'MOCK1?': 'OFF'})
    
    mock_instrument.mock1 = False

## Enum Property Factories ##
    
def test_enum_property():
    class SillyEnum(Enum):
        a = 'aa'
        b = 'bb'
        
    class EnumMock(MockInstrument):
        a = enum_property('MOCK:A', SillyEnum)
        b = enum_property('MOCK:B', SillyEnum)
        
    mock = EnumMock({'MOCK:A?': 'aa', 'MOCK:B?': 'bb'})
    
    eq_(mock.a, SillyEnum.a)
    eq_(mock.b, SillyEnum.b)
    
    # Test EnumValues, string values and string names.
    mock.a = SillyEnum.b
    mock.b = 'a'
    mock.b = 'bb'
    
    eq_(mock.value, 'MOCK:A?\nMOCK:B?\nMOCK:A bb\nMOCK:B aa\nMOCK:B bb\n')

@raises(ValueError)
def test_enum_property_invalid():
    class SillyEnum(Enum):
        a = 'aa'
        b = 'bb'

    class EnumMock(MockInstrument):
        a = enum_property('MOCK:A', SillyEnum)

    mock = EnumMock({'MOCK:A?': 'aa', 'MOCK:B?': 'bb'})

    mock.a = 'c'

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
        def input_decorator(input):
            return 'aa'
        a = enum_property('MOCK:A', SillyEnum, input_decoration=input_decorator)
    
    mock_instrument = EnumMock({'MOCK:A?': 'garbage'})
    
    eq_(mock_instrument.a, SillyEnum.a)
    
def test_enum_property_output_decoration():
    class SillyEnum(Enum):
        a = 'aa'
        
    class EnumMock(MockInstrument):
        def output_decorator(input):
            return 'foobar'
        a = enum_property('MOCK:A', SillyEnum, output_decoration=output_decorator)
        
    mock_instrument = EnumMock()
    
    mock_instrument.a = SillyEnum.a
    
    eq_(mock_instrument.value, 'MOCK:A foobar\n')

@raises(AttributeError)
def test_enum_property_writeonly_reading_fails():
    class SillyEnum(Enum):
        a = 'aa'
        
    class EnumMock(MockInstrument):
        a = enum_property('MOCK:A', SillyEnum, writeonly=True)
    
    mock_instrument = EnumMock()
    
    mock_instrument.a

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
    
    mock_instrument = EnumMock({'MOCK:A?':'aa'})
    
    mock_instrument.a = SillyEnum.a

def test_enum_property_readonly_reading_passes():
    class SillyEnum(Enum):
        a = 'aa'
        
    class EnumMock(MockInstrument):
        a = enum_property('MOCK:A', SillyEnum, readonly=True)
    
    mock_instrument = EnumMock({'MOCK:A?':'aa'})
    
    eq_(mock_instrument.a, SillyEnum.a)
    eq_(mock_instrument.value, 'MOCK:A?\n')
    
## Unitless Property ##

def test_unitless_property_basics():
    class UnitlessMock(MockInstrument):
        unitless_property = unitless_property('MOCK')
        
    mock_inst = UnitlessMock({'MOCK?':'1'})
    
    eq_(mock_inst.unitless_property, 1)
    
    mock_inst.unitless_property = 1
    eq_(mock_inst.value, 'MOCK?\nMOCK {:e}\n'.format(1))

@raises(ValueError)
def test_unitless_property_units():
    class UnitlessMock(MockInstrument):
        unitless_property = unitless_property('MOCK')
        
    mock_inst = UnitlessMock({'MOCK?':'1'})
    
    mock_inst.unitless_property = 1 * pq.volt

def test_unitless_property_format_code():
    class UnitlessMock(MockInstrument):
        unitless_property = unitless_property('MOCK', format_code='{:f}')

    mock_inst = UnitlessMock()
    
    mock_inst.unitless_property = 1
    eq_(mock_inst.value, 'MOCK {:f}\n'.format(1))
    
@raises(AttributeError)
def test_unitless_property_writeonly_reading_fails():
    class UnitlessMock(MockInstrument):
        unitless_property = unitless_property('MOCK', writeonly=True)
    
    mock_inst = UnitlessMock()
    
    mock_inst.unitless_property
    
def test_unitless_property_writeonly_writing_passes():
    class UnitlessMock(MockInstrument):
        unitless_property = unitless_property('MOCK', writeonly=True)
    
    mock_inst = UnitlessMock()
    
    mock_inst.unitless_property = 1
    eq_(mock_inst.value, 'MOCK {:e}\n'.format(1))
    
@raises(AttributeError)
def test_unitless_property_readonly_writing_fails():
    class UnitlessMock(MockInstrument):
        unitless_property = unitless_property('MOCK', readonly=True)
    
    mock_inst = UnitlessMock({'MOCK?':'1'})
    
    mock_inst.unitless_property = 1
    
def test_unitless_property_readonly_reading_passes():
    class UnitlessMock(MockInstrument):
        unitless_property = unitless_property('MOCK', readonly=True)
    
    mock_inst = UnitlessMock({'MOCK?':'1'})
    
    eq_(mock_inst.unitless_property, 1)

## Int Property Factories ##

@raises(ValueError)
def test_int_property_outside_valid_set():
    class IntMock(MockInstrument):
        mock = int_property('MOCK', valid_set=set([1, 2]))
        
    mock = IntMock()
    mock.mock = 3

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
    
    mock_inst.int_property
    
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
    
    mock_inst = IntMock({'MOCK?':'1'})
    
    mock_inst.int_property = 1
    
def test_int_property_readonly_reading_passes():
    class IntMock(MockInstrument):
        int_property = int_property('MOCK', readonly=True)
    
    mock_inst = IntMock({'MOCK?':'1'})
    
    eq_(mock_inst.int_property, 1)
    
def test_int_property_format_code():
    class IntMock(MockInstrument):
        int_property = int_property('MOCK', format_code='{:e}')
        
    mock_inst = IntMock()
    
    mock_inst.int_property = 1
    eq_(mock_inst.value, 'MOCK {:e}\n'.format(1))

## Unitful Property ##

def test_unitful_property_basics():
    class UnitfulMock(MockInstrument):
        unitful_property = unitful_property('MOCK', units=pq.hertz)
        
    mock_inst = UnitfulMock({'MOCK?':'1000'})
    
    eq_(mock_inst.unitful_property, 1000 * pq.hertz)
    
    mock_inst.unitful_property = 1000 * pq.hertz
    eq_(mock_inst.value, 'MOCK?\nMOCK {:e}\n'.format(1000))
    
def test_unitful_property_format_code():
    class UnitfulMock(MockInstrument):
        unitful_property = unitful_property('MOCK', pq.hertz, format_code='{:f}')

    mock_inst = UnitfulMock()
    
    mock_inst.unitful_property = 1000 * pq.hertz
    eq_(mock_inst.value, 'MOCK {:f}\n'.format(1000))
    
def test_unitful_property_rescale_units():
    class UnitfulMock(MockInstrument):
        unitful_property = unitful_property('MOCK', pq.hertz)

    mock_inst = UnitfulMock()
    
    mock_inst.unitful_property = 1 * pq.kilohertz
    eq_(mock_inst.value, 'MOCK {:e}\n'.format(1000))
    
def test_unitful_property_no_units_on_set():
    class UnitfulMock(MockInstrument):
        unitful_property = unitful_property('MOCK', pq.hertz)

    mock_inst = UnitfulMock()
    
    mock_inst.unitful_property = 1000
    eq_(mock_inst.value, 'MOCK {:e}\n'.format(1000))

@raises(ValueError)
def test_unitful_property_wrong_units():
    class UnitfulMock(MockInstrument):
        unitful_property = unitful_property('MOCK', pq.hertz)

    mock_inst = UnitfulMock()
    
    mock_inst.unitful_property = 1 * pq.volt
    
@raises(AttributeError)
def test_unitful_property_writeonly_reading_fails():
    class UnitfulMock(MockInstrument):
        unitful_property = unitful_property('MOCK', pq.hertz, writeonly=True)
    
    mock_inst = UnitfulMock()
    
    mock_inst.unitful_property
    
def test_unitful_property_writeonly_writing_passes():
    class UnitfulMock(MockInstrument):
        unitful_property = unitful_property('MOCK', pq.hertz, writeonly=True)
    
    mock_inst = UnitfulMock()
    
    mock_inst.unitful_property = 1 * pq.hertz
    eq_(mock_inst.value, 'MOCK {:e}\n'.format(1))
    
@raises(AttributeError)
def test_unitful_property_readonly_writing_fails():
    class UnitfulMock(MockInstrument):
        unitful_property = unitful_property('MOCK', pq.hertz, readonly=True)
    
    mock_inst = UnitfulMock({'MOCK?':'1'})
    
    mock_inst.unitful_property = 1 * pq.hertz
    
def test_unitful_property_readonly_reading_passes():
    class UnitfulMock(MockInstrument):
        unitful_property = unitful_property('MOCK', pq.hertz, readonly=True)
    
    mock_inst = UnitfulMock({'MOCK?':'1'})
    
    eq_(mock_inst.unitful_property, 1 * pq.hertz)

def test_unitful_property_valid_range():
    class UnitfulMock(MockInstrument):
        unitful_property = unitful_property('MOCK', pq.hertz, valid_range=(0, 10))

    mock_inst = UnitfulMock()

    mock_inst.unitful_property = 0
    mock_inst.unitful_property = 10

    eq_(mock_inst.value, 'MOCK {:e}\nMOCK {:e}\n'.format(0, 10))

@raises(ValueError)
def test_unitful_property_minimum_value():
    class UnitfulMock(MockInstrument):
        unitful_property = unitful_property('MOCK', pq.hertz, valid_range=(0, 10))

    mock_inst = UnitfulMock()

    mock_inst.unitful_property = -1

@raises(ValueError)
def test_unitful_property_maximum_value():
    class UnitfulMock(MockInstrument):
        unitful_property = unitful_property('MOCK', pq.hertz, valid_range=(0, 10))

    mock_inst = UnitfulMock()

    mock_inst.unitful_property = 11

def test_unitful_property_input_decoration():
    class UnitfulMock(MockInstrument):
        def input_decorator(input):
            return '1'
        a = unitful_property('MOCK:A', pq.hertz, input_decoration=input_decorator)

    mock_instrument = UnitfulMock({'MOCK:A?': 'garbage'})

    eq_(mock_instrument.a, 1 * pq.Hz)

def test_unitful_property_output_decoration():
    class UnitfulMock(MockInstrument):
        def output_decorator(input):
            return '1'
        a = unitful_property('MOCK:A', pq.hertz, output_decoration=output_decorator)

    mock_instrument = UnitfulMock()

    mock_instrument.a = 345 * pq.hertz

    eq_(mock_instrument.value, 'MOCK:A 1\n')

## String Property ##

def test_string_property_basics():
    class StringMock(MockInstrument):
        string_property = string_property('MOCK')
        
    mock_inst = StringMock({'MOCK?': '"foobar"'})
    
    eq_(mock_inst.string_property, 'foobar')
    
    mock_inst.string_property = 'foo'    
    eq_(mock_inst.value, 'MOCK?\nMOCK "foo"\n')
    
def test_string_property_different_bookmark_symbol():
    class StringMock(MockInstrument):
        string_property = string_property('MOCK', bookmark_symbol='%^')
        
    mock_inst = StringMock({'MOCK?': '%^foobar%^'})
    
    eq_(mock_inst.string_property, 'foobar')
    
    mock_inst.string_property = 'foo'    
    eq_(mock_inst.value, 'MOCK?\nMOCK %^foo%^\n')
    
def test_string_property_no_bookmark_symbol():
    class StringMock(MockInstrument):
        string_property = string_property('MOCK', bookmark_symbol='')
        
    mock_inst = StringMock({'MOCK?': 'foobar'})
    
    eq_(mock_inst.string_property, 'foobar')
    
    mock_inst.string_property = 'foo'    
    eq_(mock_inst.value, 'MOCK?\nMOCK foo\n')
