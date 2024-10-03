#!/usr/bin/env python
"""
Module containing tests for the property factories
"""

# IMPORTS ####################################################################


import pytest

from instruments.util_fns import rproperty
from . import MockInstrument


# TEST CASES #################################################################

# pylint: disable=missing-docstring


def test_rproperty_basic():
    class Mock(MockInstrument):
        def __init__(self):
            super().__init__()
            self._value = 0

        def mockget(self):
            return self._value

        def mockset(self, newval):
            self._value = newval

        mockproperty = rproperty(fget=mockget, fset=mockset)

    mock_inst = Mock()
    mock_inst.mockproperty = 1
    assert mock_inst.mockproperty == 1


def test_rproperty_readonly_writing_fails():
    with pytest.raises(AttributeError):

        class Mock(MockInstrument):
            def __init__(self):
                super().__init__()
                self._value = 0

            def mockset(self, newval):  # pragma: no cover
                self._value = newval

            mockproperty = rproperty(fget=None, fset=mockset, readonly=True)

        mock_inst = Mock()
        mock_inst.mockproperty = 1


def test_rproperty_readonly_reading_passes():
    class Mock(MockInstrument):
        def __init__(self):
            super().__init__()
            self._value = 0

        def mockget(self):
            return self._value

        mockproperty = rproperty(fget=mockget, fset=None, readonly=True)

    mock_inst = Mock()
    assert mock_inst.mockproperty == 0


def test_rproperty_writeonly_reading_fails():
    with pytest.raises(AttributeError):

        class Mock(MockInstrument):
            def __init__(self):
                super().__init__()
                self._value = 0

            def mockget(self):  # pragma: no cover
                return self._value

            mockproperty = rproperty(fget=mockget, fset=None, writeonly=True)

        mock_inst = Mock()
        assert mock_inst.mockproperty == 0


def test_rproperty_writeonly_writing_passes():
    class Mock(MockInstrument):
        def __init__(self):
            super().__init__()
            self._value = 0

        def mockset(self, newval):
            self._value = newval

        mockproperty = rproperty(fget=None, fset=mockset, writeonly=True)

    mock_inst = Mock()
    mock_inst.mockproperty = 1


def test_rproperty_readonly_and_writeonly():
    with pytest.raises(ValueError):
        _ = rproperty(readonly=True, writeonly=True)
