#!/usr/bin/env python
"""
Module containing tests for the string property factories
"""

# IMPORTS ####################################################################


from instruments.util_fns import string_property
from . import MockInstrument

# TEST CASES #################################################################

# pylint: disable=missing-docstring


def test_string_property_basics():
    class StringMock(MockInstrument):
        mock_property = string_property("MOCK")

    mock_inst = StringMock({"MOCK?": '"foobar"'})

    assert mock_inst.mock_property == "foobar"

    mock_inst.mock_property = "foo"
    assert mock_inst.value == 'MOCK?\nMOCK "foo"\n'


def test_string_property_different_bookmark_symbol():
    class StringMock(MockInstrument):
        mock_property = string_property("MOCK", bookmark_symbol="%^")

    mock_inst = StringMock({"MOCK?": "%^foobar%^"})

    assert mock_inst.mock_property == "foobar"

    mock_inst.mock_property = "foo"
    assert mock_inst.value == "MOCK?\nMOCK %^foo%^\n"


def test_string_property_no_bookmark_symbol():
    class StringMock(MockInstrument):
        mock_property = string_property("MOCK", bookmark_symbol="")

    mock_inst = StringMock({"MOCK?": "foobar"})

    assert mock_inst.mock_property == "foobar"

    mock_inst.mock_property = "foo"
    assert mock_inst.value == "MOCK?\nMOCK foo\n"


def test_string_property_set_cmd():
    class StringMock(MockInstrument):
        mock_property = string_property("MOCK", set_cmd="FOOBAR")

    mock_inst = StringMock({"MOCK?": '"derp"'})

    assert mock_inst.mock_property == "derp"

    mock_inst.mock_property = "qwerty"
    assert mock_inst.value == 'MOCK?\nFOOBAR "qwerty"\n'
