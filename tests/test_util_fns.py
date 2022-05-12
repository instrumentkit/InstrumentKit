#!/usr/bin/env python
"""
Module containing tests for util_fns.py
"""

# IMPORTS ####################################################################

from enum import Enum

import pint
import pytest

from instruments.units import ureg as u
from instruments.util_fns import (
    assume_units,
    bool_property,
    enum_property,
    int_property,
    ProxyList,
    setattr_expression,
    string_property,
    unitful_property,
    unitless_property,
)

from tests import unit_eq


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
            self.spy_query = mocker.spy(self, "query")
            self.spy_sendcmd = mocker.spy(self, "sendcmd")

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

        unitful_property_limited = unitful_property(
            "42", u.m, valid_range=(1 * u.m, 100 * u.m)
        )

        unitful_property = unitful_property("42", u.m)

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
    assert proxy_list["aa"]._name == MockEnum.a.value
    assert proxy_list["b"]._name == MockEnum.b.value
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

        _ = proxy_list["c"]  # Should raise IndexError


def test_ProxyList_invalid_idx():
    with pytest.raises(IndexError):

        class ProxyChild:
            def __init__(self, parent, name):
                self._parent = parent
                self._name = name

        parent = object()

        proxy_list = ProxyList(parent, ProxyChild, range(5))

        _ = proxy_list[10]  # Should raise IndexError


@pytest.mark.parametrize(
    "input, out",
    (
        (1, u.Quantity(1, "m")),
        (5 * u.mm, u.Quantity(5, "mm")),
        ("7.3 km", u.Quantity(7.3, "km")),
        (u.Quantity(9, "nm"), 9 * u.nm),
        ([1, 5], u.Quantity([1, 5], u.m)),
    ),
)
def test_assume_units_correct(input, out):
    unit_eq(assume_units(input, "m"), out)


def test_setattr_expression_simple():
    class A:
        x = "x"
        y = "y"
        z = "z"

    a = A()
    setattr_expression(a, "x", "foo")
    assert a.x == "foo"


def test_setattr_expression_index():
    class A:
        x = ["x", "y", "z"]

    a = A()
    setattr_expression(a, "x[1]", "foo")
    assert a.x[1] == "foo"


def test_setattr_expression_nested():
    class B:
        x = "x"

    class A:
        b = None

        def __init__(self):
            self.b = B()

    a = A()
    setattr_expression(a, "b.x", "foo")
    assert a.b.x == "foo"


def test_setattr_expression_both():
    class B:
        x = "x"

    class A:
        b = None

        def __init__(self):
            self.b = [B()]

    a = A()
    setattr_expression(a, "b[0].x", "foo")
    assert a.b[0].x == "foo"


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


class Test_unitful_property:
    def test_unitful_property_sendcmd_query(self, mock_inst):
        """Assert that unitful_property calls sendcmd, query of parent class."""
        # getter
        assert mock_inst.unitful_property == u.Quantity(42, u.m)
        mock_inst.spy_query.assert_called()
        # setter
        value = 13
        mock_inst.unitful_property = u.Quantity(value, u.m)
        assert mock_inst._sendcmd == f"42 {value:e}"
        mock_inst.spy_sendcmd.assert_called()

    def test_unitful_property_sendcmd_query_unitless(self, mock_inst):
        """Assert that unitful_property calls sendcmd, query of parent class.
        Here for a unitless input
        """
        # getter
        assert mock_inst.unitful_property == u.Quantity(42, u.m)
        mock_inst.spy_query.assert_called()
        # setter
        value = 13
        mock_inst.unitful_property = value
        assert mock_inst._sendcmd == f"42 {value:e}"
        mock_inst.spy_sendcmd.assert_called()

    @pytest.mark.parametrize("value", (0.1, 200, 0.1 * u.m, 200 * u.m))
    def test_unitful_property_sendcmd_limited_unfit(self, mock_inst, value):
        """Assert that unitful_property calls sendcmd, query of parent class.
        Here an input out of bounds for limited property."""
        # setter
        with pytest.raises(ValueError):
            mock_inst.unitful_property_limited = value

    @pytest.mark.parametrize("value", (13 * u.m, 17 * u.m, 55 * u.m))
    def test_unitful_property_sendcmd_limited_pass_un(self, mock_inst, value):
        """Assert that unitful_property calls sendcmd, query of parent class.
        Here an input fit for limited property."""
        # setter
        mock_inst.unitful_property_limited = value
        assert mock_inst._sendcmd == f"42 {value.magnitude:e}"
        mock_inst.spy_sendcmd.assert_called()

    @pytest.mark.parametrize("value", (13, 17, 55, 99))
    def test_unitful_property_sendcmd_limited_pass_ul(self, mock_inst, value):
        """Assert that unitful_property calls sendcmd, query of parent class.
        Here an input fit for limited property."""
        # setter
        mock_inst.unitful_property_limited = value
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
