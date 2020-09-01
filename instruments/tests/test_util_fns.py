#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing tests for util_fns.py
"""

# IMPORTS ####################################################################

from enum import Enum

import pint
import pytest

from instruments.units import ureg as u
from instruments.util_fns import (
    ProxyList,
    assume_units,
    setattr_expression
)

# TEST CASES #################################################################

# pylint: disable=protected-access,missing-docstring


def test_ProxyList_basics():
    class ProxyChild:

        def __init__(self, parent, name):
            self._parent = parent
            self._name = name

    parent = object()

    proxy_list = ProxyList(parent, ProxyChild, range(10))

    child = proxy_list[0]
    assert child._parent is parent
    assert child._name == 0


def test_ProxyList_valid_range_is_enum():
    class ProxyChild:

        def __init__(self, parent, name):
            self._parent = parent
            self._name = name

    class MockEnum(Enum):
        a = "aa"
        b = "bb"

    parent = object()

    proxy_list = ProxyList(parent, ProxyChild, MockEnum)
    assert proxy_list['aa']._name == MockEnum.a.value
    assert proxy_list['b']._name == MockEnum.b.value
    assert proxy_list[MockEnum.a]._name == MockEnum.a.value


def test_ProxyList_length():
    class ProxyChild:

        def __init__(self, parent, name):
            self._parent = parent
            self._name = name

    parent = object()

    proxy_list = ProxyList(parent, ProxyChild, range(10))

    assert len(proxy_list) == 10


def test_ProxyList_iterator():
    class ProxyChild:

        def __init__(self, parent, name):
            self._parent = parent
            self._name = name

    parent = object()

    proxy_list = ProxyList(parent, ProxyChild, range(10))

    i = 0
    for item in proxy_list:
        assert item._name == i
        i = i + 1


def test_ProxyList_invalid_idx_enum():
    with pytest.raises(IndexError):
        class ProxyChild:

            def __init__(self, parent, name):
                self._parent = parent
                self._name = name

        class MockEnum(Enum):
            a = "aa"
            b = "bb"

        parent = object()

        proxy_list = ProxyList(parent, ProxyChild, MockEnum)

        _ = proxy_list['c']  # Should raise IndexError


def test_ProxyList_invalid_idx():
    with pytest.raises(IndexError):
        class ProxyChild:

            def __init__(self, parent, name):
                self._parent = parent
                self._name = name

        parent = object()

        proxy_list = ProxyList(parent, ProxyChild, range(5))

        _ = proxy_list[10]  # Should raise IndexError


def test_assume_units_correct():
    m = u.Quantity(1, 'm')

    # Check that unitful quantities are kept unitful.
    assert assume_units(m, 'mm').to('mm').magnitude == 1000

    # Check that raw scalars are made unitful.
    assert assume_units(1, 'm').to('mm').magnitude == 1000


def test_assume_units_failures():
    with pytest.raises(pint.errors.DimensionalityError):
        assume_units(1, 'm').to('s')

def test_setattr_expression_simple():
    class A:
        x = 'x'
        y = 'y'
        z = 'z'

    a = A()
    setattr_expression(a, 'x', 'foo')
    assert a.x == 'foo'

def test_setattr_expression_index():
    class A:
        x = ['x', 'y', 'z']

    a = A()
    setattr_expression(a, 'x[1]', 'foo')
    assert a.x[1] == 'foo'

def test_setattr_expression_nested():
    class B:
        x = 'x'
    class A:
        b = None
        def __init__(self):
            self.b = B()

    a = A()
    setattr_expression(a, 'b.x', 'foo')
    assert a.b.x == 'foo'

def test_setattr_expression_both():
    class B:
        x = 'x'
    class A:
        b = None
        def __init__(self):
            self.b = [B()]

    a = A()
    setattr_expression(a, 'b[0].x', 'foo')
    assert a.b[0].x == 'foo'
