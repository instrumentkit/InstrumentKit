#!/usr/bin/env python
"""
Module containing tests for the enum property factories
"""

# IMPORTS ####################################################################


from enum import Enum, IntEnum
import pytest

from instruments.util_fns import enum_property
from . import MockInstrument

# TEST CASES #################################################################

# pylint: disable=missing-docstring


def test_enum_property():
    class SillyEnum(Enum):
        a = "aa"
        b = "bb"

    class EnumMock(MockInstrument):
        a = enum_property("MOCK:A", SillyEnum)
        b = enum_property("MOCK:B", SillyEnum)

    mock_inst = EnumMock({"MOCK:A?": "aa", "MOCK:B?": "bb"})

    assert mock_inst.a == SillyEnum.a
    assert mock_inst.b == SillyEnum.b

    # Test EnumValues, string values and string names.
    mock_inst.a = SillyEnum.b
    mock_inst.b = "a"
    mock_inst.b = "bb"

    assert mock_inst.value == "MOCK:A?\nMOCK:B?\nMOCK:A bb\nMOCK:B aa\nMOCK:B bb\n"


def test_enum_property_invalid():
    with pytest.raises(ValueError):

        class SillyEnum(Enum):
            a = "aa"
            b = "bb"

        class EnumMock(MockInstrument):
            a = enum_property("MOCK:A", SillyEnum)

        mock_inst = EnumMock({"MOCK:A?": "aa", "MOCK:B?": "bb"})

        mock_inst.a = "c"


def test_enum_property_set_fmt():
    class SillyEnum(Enum):
        a = "aa"

    class EnumMock(MockInstrument):
        a = enum_property("MOCK:A", SillyEnum, set_fmt="{}={}")

    mock_instrument = EnumMock()

    mock_instrument.a = "aa"
    assert mock_instrument.value == "MOCK:A=aa\n"


def test_enum_property_input_decoration():
    class SillyEnum(Enum):
        a = "aa"

    class EnumMock(MockInstrument):
        @staticmethod
        def _input_decorator(_):
            return "aa"

        a = enum_property("MOCK:A", SillyEnum, input_decoration=_input_decorator)

    mock_instrument = EnumMock({"MOCK:A?": "garbage"})

    assert mock_instrument.a == SillyEnum.a


def test_enum_property_input_decoration_not_a_function():
    class SillyEnum(IntEnum):
        a = 1

    class EnumMock(MockInstrument):

        a = enum_property("MOCK:A", SillyEnum, input_decoration=int)

    mock_instrument = EnumMock({"MOCK:A?": "1"})

    assert mock_instrument.a == SillyEnum.a


def test_enum_property_output_decoration():
    class SillyEnum(Enum):
        a = "aa"

    class EnumMock(MockInstrument):
        @staticmethod
        def _output_decorator(_):
            return "foobar"

        a = enum_property("MOCK:A", SillyEnum, output_decoration=_output_decorator)

    mock_instrument = EnumMock()

    mock_instrument.a = SillyEnum.a

    assert mock_instrument.value == "MOCK:A foobar\n"


def test_enum_property_output_decoration_not_a_function():
    class SillyEnum(Enum):
        a = ".23"

    class EnumMock(MockInstrument):

        a = enum_property("MOCK:A", SillyEnum, output_decoration=float)

    mock_instrument = EnumMock()

    mock_instrument.a = SillyEnum.a

    assert mock_instrument.value == "MOCK:A 0.23\n"


def test_enum_property_writeonly_reading_fails():
    with pytest.raises(AttributeError):

        class SillyEnum(Enum):
            a = "aa"

        class EnumMock(MockInstrument):
            a = enum_property("MOCK:A", SillyEnum, writeonly=True)

        mock_instrument = EnumMock()

        _ = mock_instrument.a


def test_enum_property_writeonly_writing_passes():
    class SillyEnum(Enum):
        a = "aa"

    class EnumMock(MockInstrument):
        a = enum_property("MOCK:A", SillyEnum, writeonly=True)

    mock_instrument = EnumMock()

    mock_instrument.a = SillyEnum.a
    assert mock_instrument.value == "MOCK:A aa\n"


def test_enum_property_readonly_writing_fails():
    with pytest.raises(AttributeError):

        class SillyEnum(Enum):
            a = "aa"

        class EnumMock(MockInstrument):
            a = enum_property("MOCK:A", SillyEnum, readonly=True)

        mock_instrument = EnumMock({"MOCK:A?": "aa"})

        mock_instrument.a = SillyEnum.a


def test_enum_property_readonly_reading_passes():
    class SillyEnum(Enum):
        a = "aa"

    class EnumMock(MockInstrument):
        a = enum_property("MOCK:A", SillyEnum, readonly=True)

    mock_instrument = EnumMock({"MOCK:A?": "aa"})

    assert mock_instrument.a == SillyEnum.a
    assert mock_instrument.value == "MOCK:A?\n"


def test_enum_property_set_cmd():
    class SillyEnum(Enum):
        a = "aa"

    class EnumMock(MockInstrument):
        a = enum_property("MOCK:A", SillyEnum, set_cmd="FOOBAR:A")

    mock_inst = EnumMock({"MOCK:A?": "aa"})

    assert mock_inst.a == SillyEnum.a
    mock_inst.a = SillyEnum.a

    assert mock_inst.value == "MOCK:A?\nFOOBAR:A aa\n"
