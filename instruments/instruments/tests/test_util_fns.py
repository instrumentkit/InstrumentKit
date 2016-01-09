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
    ProxyList,
    assume_units
)

from flufl.enum import Enum

## TEST CASES #################################################################

def test_ProxyList_basics():
    class ProxyChild(object):
        def __init__(self, parent, name):
            self._parent = parent
            self._name = name
            
    parent = object()
    
    proxy_list = ProxyList(parent, ProxyChild, xrange(10))
    
    child = proxy_list[0]
    assert child._parent is parent
    assert child._name == 0
    
def test_ProxyList_valid_range_is_enum():
    class ProxyChild(object):
        def __init__(self, parent, name):
            self._parent = parent
            self._name = name
            
    class MockEnum(Enum):
        a = "aa"
        b = "bb"
        
    parent = object()
    
    proxy_list = ProxyList(parent, ProxyChild, MockEnum)
    assert proxy_list['aa']._name == MockEnum.a
    assert proxy_list['b']._name  == MockEnum.b
    assert proxy_list[MockEnum.a]._name == MockEnum.a
    
def test_ProxyList_length():
    class ProxyChild(object):
        def __init__(self, parent, name):
            self._parent = parent
            self._name = name
            
    parent = object()
    
    proxy_list = ProxyList(parent, ProxyChild, xrange(10))
    
    eq_(len(proxy_list), 10)
    
def test_ProxyList_iterator():
    class ProxyChild(object):
        def __init__(self, parent, name):
            self._parent = parent
            self._name = name
            
    parent = object()
    
    proxy_list = ProxyList(parent, ProxyChild, xrange(10))
    
    i = 0
    for item in proxy_list:
        eq_(item._name, i)
        i = i + 1

@raises(IndexError)
def test_ProxyList_invalid_idx_enum():
    class ProxyChild(object):
        def __init__(self, parent, name):
            self._parent = parent
            self._name = name
            
    class MockEnum(Enum):
        a = "aa"
        b = "bb"
        
    parent = object()
    
    proxy_list = ProxyList(parent, ProxyChild, MockEnum)
    
    proxy_list['c'] # Should raise IndexError
    
@raises(IndexError)
def test_ProxyList_invalid_idx():
    class ProxyChild(object):
        def __init__(self, parent, name):
            self._parent = parent
            self._name = name
        
    parent = object()
    
    proxy_list = ProxyList(parent, ProxyChild, xrange(5))
    
    proxy_list[10] # Should raise IndexError

def test_assume_units_correct():
    m = pq.Quantity(1, 'm')
    
    # Check that unitful quantities are kept unitful.
    eq_(assume_units(m, 'mm').rescale('mm').magnitude, 1000)
    
    # Check that raw scalars are made unitful.
    eq_(assume_units(1, 'm').rescale('mm').magnitude, 1000)
    
@raises(ValueError)
def test_assume_units_failures():
    assume_units(1, 'm').rescale('s')
