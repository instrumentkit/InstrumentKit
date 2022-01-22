#!/usr/bin/env python
"""
Module containing tests for the int property factories
"""

# IMPORTS ####################################################################


import pytest

from instruments.util_fns import int_property
from . import MockInstrument

# TEST CASES #################################################################

# pylint: disable=missing-docstring


def test_int_property_outside_valid_set():
    with pytest.raises(ValueError):

        class IntMock(MockInstrument):
            mock_property = int_property("MOCK", valid_set={1, 2})

        mock_inst = IntMock()
        mock_inst.mock_property = 3


def test_int_property_valid_set():
    class IntMock(MockInstrument):
        int_property = int_property("MOCK", valid_set={1, 2})

    mock_inst = IntMock({"MOCK?": "1"})

    assert mock_inst.int_property == 1

    mock_inst.int_property = 2
    assert mock_inst.value == "MOCK?\nMOCK 2\n"


def test_int_property_no_set():
    class IntMock(MockInstrument):
        int_property = int_property("MOCK")

    mock_inst = IntMock()

    mock_inst.int_property = 1

    assert mock_inst.value == "MOCK 1\n"


def test_int_property_writeonly_reading_fails():
    with pytest.raises(AttributeError):

        class IntMock(MockInstrument):
            int_property = int_property("MOCK", writeonly=True)

        mock_inst = IntMock()

        _ = mock_inst.int_property


def test_int_property_writeonly_writing_passes():
    class IntMock(MockInstrument):
        int_property = int_property("MOCK", writeonly=True)

    mock_inst = IntMock()

    mock_inst.int_property = 1
    assert mock_inst.value == f"MOCK {1:d}\n"


def test_int_property_readonly_writing_fails():
    with pytest.raises(AttributeError):

        class IntMock(MockInstrument):
            int_property = int_property("MOCK", readonly=True)

        mock_inst = IntMock({"MOCK?": "1"})

        mock_inst.int_property = 1


def test_int_property_readonly_reading_passes():
    class IntMock(MockInstrument):
        int_property = int_property("MOCK", readonly=True)

    mock_inst = IntMock({"MOCK?": "1"})

    assert mock_inst.int_property == 1


def test_int_property_format_code():
    class IntMock(MockInstrument):
        int_property = int_property("MOCK", format_code="{:e}")

    mock_inst = IntMock()

    mock_inst.int_property = 1
    assert mock_inst.value == f"MOCK {1:e}\n"


def test_int_property_set_cmd():
    class IntMock(MockInstrument):
        int_property = int_property("MOCK", set_cmd="FOOBAR")

    mock_inst = IntMock({"MOCK?": "1"})

    assert mock_inst.int_property == 1
    mock_inst.int_property = 1

    assert mock_inst.value == "MOCK?\nFOOBAR 1\n"
