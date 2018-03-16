#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing tests for util_fns.py
"""

# IMPORTS ####################################################################

from __future__ import absolute_import

from builtins import range

from enum import Enum
import quantities as pq
import pytest

from instruments.util_fns import (
    ProxyList,
    assume_units, convert_temperature,
    setattr_expression
)

# TEST CASES #################################################################

# pylint: disable=protected-access,missing-docstring


def test_ProxyList_basics():
    class ProxyChild(object):

        def __init__(self, parent, name):
            self._parent = parent
            self._name = name

    parent = object()

    proxy_list = ProxyList(parent, ProxyChild, range(10))

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
    assert proxy_list['aa']._name == MockEnum.a.value
    assert proxy_list['b']._name == MockEnum.b.value
    assert proxy_list[MockEnum.a]._name == MockEnum.a.value


def test_ProxyList_length():
    class ProxyChild(object):

        def __init__(self, parent, name):
            self._parent = parent
            self._name = name

    parent = object()

    proxy_list = ProxyList(parent, ProxyChild, range(10))

    assert len(proxy_list) == 10


def test_ProxyList_iterator():
    class ProxyChild(object):

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
        class ProxyChild(object):

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
        class ProxyChild(object):

            def __init__(self, parent, name):
                self._parent = parent
                self._name = name

        parent = object()

        proxy_list = ProxyList(parent, ProxyChild, range(5))

        _ = proxy_list[10]  # Should raise IndexError


def test_assume_units_correct():
    m = pq.Quantity(1, 'm')

    # Check that unitful quantities are kept unitful.
    assert assume_units(m, 'mm').rescale('mm').magnitude == 1000

    # Check that raw scalars are made unitful.
    assert assume_units(1, 'm').rescale('mm').magnitude == 1000


def test_temperature_conversion():
    blo = 70.0 * pq.degF
    out = convert_temperature(blo, pq.degC)
    assert out.magnitude == 21.11111111111111
    out = convert_temperature(blo, pq.degK)
    assert out.magnitude == 294.2055555555555
    out = convert_temperature(blo, pq.degF)
    assert out.magnitude == 70.0

    blo = 20.0 * pq.degC
    out = convert_temperature(blo, pq.degF)
    assert out.magnitude == 68
    out = convert_temperature(blo, pq.degC)
    assert out.magnitude == 20.0
    out = convert_temperature(blo, pq.degK)
    assert out.magnitude == 293.15

    blo = 270 * pq.degK
    out = convert_temperature(blo, pq.degC)
    assert out.magnitude == -3.1499999999999773
    out = convert_temperature(blo, pq.degF)
    assert out.magnitude == 141.94736842105263
    out = convert_temperature(blo, pq.K)
    assert out.magnitude == 270


def test_temperater_conversion_failure():
    with pytest.raises(ValueError):
        blo = 70.0 * pq.degF
        convert_temperature(blo, pq.V)


def test_assume_units_failures():
    with pytest.raises(ValueError):
        assume_units(1, 'm').rescale('s')

def test_setattr_expression_simple():
    class A(object):
        x = 'x'
        y = 'y'
        z = 'z'

    a = A()
    setattr_expression(a, 'x', 'foo')
    assert a.x == 'foo'

def test_setattr_expression_index():
    class A(object):
        x = ['x', 'y', 'z']

    a = A()
    setattr_expression(a, 'x[1]', 'foo')
    assert a.x[1] == 'foo'

def test_setattr_expression_nested():
    class B(object):
        x = 'x'
    class A(object):
        b = None
        def __init__(self):
            self.b = B()

    a = A()
    setattr_expression(a, 'b.x', 'foo')
    assert a.b.x == 'foo'

def test_setattr_expression_both():
    class B(object):
        x = 'x'
    class A(object):
        b = None
        def __init__(self):
            self.b = [B()]

    a = A()
    setattr_expression(a, 'b[0].x', 'foo')
    assert a.b[0].x == 'foo'
