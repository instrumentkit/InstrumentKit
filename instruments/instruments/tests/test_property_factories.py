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

import quantities as pq
from cStringIO import StringIO

from nose.tools import raises, eq_

from instruments.util_fns import (
    ProxyList, assume_units,
    rproperty, bool_property, enum_property, int_property, string_property
)

from flufl.enum import Enum

## CLASSES ####################################################################

class MockInstrument(object):
    """
    Mock class that admits sendcmd/query but little else such that property
    factories can be tested by deriving from the class.
    """
    
    def __init__(self, responses=None):
        self._buf = StringIO()
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
def test_rproperty_readonly():
    class Mock(MockInstrument):
        def __init__(self):
            self._value = 0
        def mockget(self):
            return self._value
        def mockset(self, newval):
            self._value = newval
        mockproperty = rproperty(fget=mockget, fset=mockset, readonly=True)
    
    mock_inst = Mock()
    eq_(mock_inst.mockproperty, 0) # Reading should pass
    mock_inst.mockproperty = 1 # Writing should raise attr error
    
@raises(AttributeError)
def test_rproperty_writeonly():
    class Mock(MockInstrument):
        def __init__(self):
            self._value = 0
        def mockget(self):
            return self._value
        def mockset(self, newval):
            self._value = newval
        mockproperty = rproperty(fget=mockget, fset=mockset, readonly=True)
    
    mock_inst = Mock()
    mock_inst.mockproperty = 1
    eq_(mock_inst.mockproperty, 0) # Should raise attr error
    
@raises(ValueError)
def test_rproperty_readonly_and_writeonly():
    mockproperty = rproperty(readonly=True, writeonly=True)
    
## Bool Property Factories ##
    
def test_bool_property_basics():
    class BoolMock(MockInstrument):
        mock1 = bool_property('MOCK1', 'ON', 'OFF')
        mock2 = bool_property('MOCK2', 'YES', 'NO')
        
    mock = BoolMock({'MOCK1?': 'OFF', 'MOCK2?': 'YES'})
    
    assert not mock.mock1
    assert mock.mock2
    
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
def test_bool_property_read_only():
    class BoolMock(MockInstrument):
        mock1 = bool_property('MOCK1', 'ON', 'OFF', readonly=True)
    
    mock_instrument = BoolMock({'MOCK1?': 'OFF'})
    
    assert mock_instrument.mock1 == False # Can read
    mock_instrument.mock1 = "Foo" # Should raise AttributeError

@raises(AttributeError)
def test_bool_property_write_only():
    class BoolMock(MockInstrument):
        mock1 = bool_property('MOCK1', 'ON', 'OFF', writeonly=True)
    
    mock_instrument = BoolMock({'MOCK1?': 'OFF'})
    
    mock_instrument.mock1 = "OFF" # Can write
    mock_instrument.mock1 # Should raise AttributeError

## Enum Property Factories ##
    
def test_enum_property():
    class SillyEnum(Enum):
        a = 'aa'
        b = 'bb'
        
    class EnumMock(MockInstrument):
        a = enum_property('MOCK:A', SillyEnum)
        b = enum_property('MOCK:B', SillyEnum)
        
    mock = EnumMock({'MOCK:A?': 'aa', 'MOCK:B?': 'bb'})
    
    assert mock.a is SillyEnum.a
    assert mock.b is SillyEnum.b
    
    # Test EnumValues, string values and string names.
    mock.a = SillyEnum.b
    mock.b = 'a'
    mock.b = 'bb'
    
    eq_(mock.value, 'MOCK:A?\nMOCK:B?\nMOCK:A bb\nMOCK:B aa\nMOCK:B bb\n')
    
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
    
    assert mock_instrument.a is SillyEnum.a
    
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
    
    assert mock_inst.int_property is 1
    
    mock_inst.int_property = 2
    
    eq_(mock_inst.value, 'MOCK?\nMOCK 2\n')

def test_int_property_no_set():
    class IntMock(MockInstrument):
        int_property = int_property('MOCK')
        
    mock_inst = IntMock()
    
    mock_inst.int_property = 1
    
    eq_(mock_inst.value, 'MOCK 1\n')

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
