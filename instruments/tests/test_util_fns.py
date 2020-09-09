#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing tests for util_fns.py
"""

# IMPORTS ####################################################################

from enum import Enum

import pytest

import instruments.units as u
from instruments.util_fns import (
    ProxyList,
    assume_units, convert_temperature,
    setattr_expression,
    bool_property, enum_property, unitless_property, int_property,
    unitful_property, string_property
)


# FIXTURES ###################################################################


@pytest.fixture
def mock_inst(mocker):
    """Intialize a mock instrument to test property factories.

    Include a call to each property factory to be tested. The command
    given to the property factory must be a valid argument returned by
    query. This argument can be asserted later. Also set up are mocker
    spies to assert `query` and `sendcmd` have actually been called.

    :return: Fake instrument class.
    """
    class Inst:
        """Mock instrument class."""
        def __init__(self):
            """Set up the mocker spies and send command placeholder."""
            # spies
            self.spy_query = mocker.spy(self, 'query')
            self.spy_sendcmd = mocker.spy(self, 'sendcmd')

            # variable to set with send command
            self._sendcmd = None

        def query(self, cmd):
            """Return the command minus the ? which is sent along."""
            return f"{cmd[:-1]}"

        def sendcmd(self, cmd):
            """Sets the command to `self._sendcmd`."""
            self._sendcmd = cmd

        class SomeEnum(Enum):
            test = "enum"

        bool_property = bool_property("ON")  # return True

        enum_property = enum_property("enum", SomeEnum)

        unitless_property = unitless_property("42")

        int_property = int_property("42")

        unitful_property = unitful_property("42", u.K)

        string_property = string_property("'STRING'")

    return Inst()


# TEST CASES #################################################################

# pylint: disable=protected-access,missing-docstring,redefined-outer-name


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
    assert assume_units(m, 'mm').rescale('mm').magnitude == 1000

    # Check that raw scalars are made unitful.
    assert assume_units(1, 'm').rescale('mm').magnitude == 1000


def test_temperature_conversion():
    blo = 70.0 * u.degF
    out = convert_temperature(blo, u.degC)
    assert out.magnitude == 21.11111111111111
    out = convert_temperature(blo, u.degK)
    assert out.magnitude == 294.2055555555555
    out = convert_temperature(blo, u.degF)
    assert out.magnitude == 70.0

    blo = 20.0 * u.degC
    out = convert_temperature(blo, u.degF)
    assert out.magnitude == 68
    out = convert_temperature(blo, u.degC)
    assert out.magnitude == 20.0
    out = convert_temperature(blo, u.degK)
    assert out.magnitude == 293.15

    blo = 270 * u.degK
    out = convert_temperature(blo, u.degC)
    assert out.magnitude == -3.1499999999999773
    out = convert_temperature(blo, u.degF)
    assert out.magnitude == 141.94736842105263
    out = convert_temperature(blo, u.K)
    assert out.magnitude == 270


def test_temperater_conversion_failure():
    with pytest.raises(ValueError):
        blo = 70.0 * u.degF
        convert_temperature(blo, u.V)


def test_assume_units_failures():
    with pytest.raises(ValueError):
        assume_units(1, 'm').rescale('s')

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


def test_bool_property_sendcmd_query(mock_inst):
    """Assert that bool_property calls sendcmd, query of parent class."""
    # fixture query should return "On" -> True
    assert mock_inst.bool_property
    mock_inst.spy_query.assert_called()
    # setter
    mock_inst.bool_property = True
    assert mock_inst._sendcmd == "ON ON"
    mock_inst.spy_sendcmd.assert_called()


def test_enum_property_sendcmd_query(mock_inst):
    """Assert that enum_property calls sendcmd, query of parent class."""
    # test getter
    assert mock_inst.enum_property == mock_inst.SomeEnum.test
    mock_inst.spy_query.assert_called()
    # setter
    mock_inst.enum_property = mock_inst.SomeEnum.test
    assert mock_inst._sendcmd == "enum enum"
    mock_inst.spy_sendcmd.assert_called()


def test_unitless_property_sendcmd_query(mock_inst):
    """Assert that unitless_property calls sendcmd, query of parent class."""
    # getter
    assert mock_inst.unitless_property == 42
    mock_inst.spy_query.assert_called()
    # setter
    value = 13
    mock_inst.unitless_property = value
    assert mock_inst._sendcmd == f"42 {value:e}"
    mock_inst.spy_sendcmd.assert_called()


def test_int_property_sendcmd_query(mock_inst):
    """Assert that int_property calls sendcmd, query of parent class."""
    # getter
    assert mock_inst.int_property == 42
    mock_inst.spy_query.assert_called()
    # setter
    value = 13
    mock_inst.int_property = value
    assert mock_inst._sendcmd == f"42 {value}"
    mock_inst.spy_sendcmd.assert_called()


def test_unitful_property_sendcmd_query(mock_inst):
    """Assert that unitful_property calls sendcmd, query of parent class."""
    # getter
    assert mock_inst.unitful_property == u.Quantity(42, u.K)
    mock_inst.spy_query.assert_called()
    # setter
    value = 13
    mock_inst.unitful_property = u.Quantity(value, u.K)
    assert mock_inst._sendcmd == f"42 {value:e}"
    mock_inst.spy_sendcmd.assert_called()


def test_string_property_sendcmd_query(mock_inst):
    """Assert that string_property calls sendcmd, query of parent class."""
    # getter
    assert mock_inst.string_property == "STRING"
    mock_inst.spy_query.assert_called()
    # setter
    value = "forty-two"
    mock_inst.string_property = value
    assert mock_inst._sendcmd == f"'STRING' \"{value}\""
    mock_inst.spy_sendcmd.assert_called()
