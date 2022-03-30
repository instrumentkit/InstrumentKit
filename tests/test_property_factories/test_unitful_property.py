#!/usr/bin/env python
"""
Module containing tests for the unitful property factories
"""

# IMPORTS ####################################################################


import pytest
import pint

from instruments.util_fns import unitful_property
from instruments.units import ureg as u
from . import MockInstrument

# TEST CASES #################################################################

# pylint: disable=missing-docstring,no-self-use


def test_unitful_property_basics():
    class UnitfulMock(MockInstrument):
        unitful_property = unitful_property("MOCK", units=u.hertz)

    mock_inst = UnitfulMock({"MOCK?": "1000"})

    assert mock_inst.unitful_property == 1000 * u.hertz

    mock_inst.unitful_property = 1000 * u.hertz
    assert mock_inst.value == f"MOCK?\nMOCK {1000:e}\n"


def test_unitful_property_format_code():
    class UnitfulMock(MockInstrument):
        unitful_property = unitful_property("MOCK", u.hertz, format_code="{:f}")

    mock_inst = UnitfulMock()

    mock_inst.unitful_property = 1000 * u.hertz
    assert mock_inst.value == f"MOCK {1000:f}\n"


def test_unitful_property_rescale_units():
    class UnitfulMock(MockInstrument):
        unitful_property = unitful_property("MOCK", u.hertz)

    mock_inst = UnitfulMock()

    mock_inst.unitful_property = 1 * u.kilohertz
    assert mock_inst.value == f"MOCK {1000:e}\n"


def test_unitful_property_no_units_on_set():
    class UnitfulMock(MockInstrument):
        unitful_property = unitful_property("MOCK", u.hertz)

    mock_inst = UnitfulMock()

    mock_inst.unitful_property = 1000
    assert mock_inst.value == f"MOCK {1000:e}\n"


def test_unitful_property_wrong_units():
    with pytest.raises(pint.errors.DimensionalityError):

        class UnitfulMock(MockInstrument):
            unitful_property = unitful_property("MOCK", u.hertz)

        mock_inst = UnitfulMock()

        mock_inst.unitful_property = 1 * u.volt


def test_unitful_property_writeonly_reading_fails():
    with pytest.raises(AttributeError):

        class UnitfulMock(MockInstrument):
            unitful_property = unitful_property("MOCK", u.hertz, writeonly=True)

        mock_inst = UnitfulMock()

        _ = mock_inst.unitful_property


def test_unitful_property_writeonly_writing_passes():
    class UnitfulMock(MockInstrument):
        unitful_property = unitful_property("MOCK", u.hertz, writeonly=True)

    mock_inst = UnitfulMock()

    mock_inst.unitful_property = 1 * u.hertz
    assert mock_inst.value == f"MOCK {1:e}\n"


def test_unitful_property_readonly_writing_fails():
    with pytest.raises(AttributeError):

        class UnitfulMock(MockInstrument):
            unitful_property = unitful_property("MOCK", u.hertz, readonly=True)

        mock_inst = UnitfulMock({"MOCK?": "1"})

        mock_inst.unitful_property = 1 * u.hertz


def test_unitful_property_readonly_reading_passes():
    class UnitfulMock(MockInstrument):
        unitful_property = unitful_property("MOCK", u.hertz, readonly=True)

    mock_inst = UnitfulMock({"MOCK?": "1"})

    assert mock_inst.unitful_property == 1 * u.hertz


def test_unitful_property_valid_range():
    class UnitfulMock(MockInstrument):
        unitful_property = unitful_property("MOCK", u.hertz, valid_range=(0, 10))

    mock_inst = UnitfulMock()

    mock_inst.unitful_property = 0
    mock_inst.unitful_property = 10

    assert mock_inst.value == f"MOCK {0:e}\nMOCK {10:e}\n"


def test_unitful_property_valid_range_functions():
    class UnitfulMock(MockInstrument):
        def min_value(self):
            return 0

        def max_value(self):
            return 10

        unitful_property = unitful_property(
            "MOCK", u.hertz, valid_range=(min_value, max_value)
        )

    mock_inst = UnitfulMock()

    mock_inst.unitful_property = 0
    mock_inst.unitful_property = 10

    assert mock_inst.value == f"MOCK {0:e}\nMOCK {10:e}\n"


def test_unitful_property_minimum_value():
    with pytest.raises(ValueError):

        class UnitfulMock(MockInstrument):
            unitful_property = unitful_property("MOCK", u.hertz, valid_range=(0, 10))

        mock_inst = UnitfulMock()

        mock_inst.unitful_property = -1


def test_unitful_property_maximum_value():
    with pytest.raises(ValueError):

        class UnitfulMock(MockInstrument):
            unitful_property = unitful_property("MOCK", u.hertz, valid_range=(0, 10))

        mock_inst = UnitfulMock()

        mock_inst.unitful_property = 11


def test_unitful_property_input_decoration():
    class UnitfulMock(MockInstrument):
        @staticmethod
        def _input_decorator(_):
            return "1"

        a = unitful_property("MOCK:A", u.hertz, input_decoration=_input_decorator)

    mock_instrument = UnitfulMock({"MOCK:A?": "garbage"})

    assert mock_instrument.a == 1 * u.Hz


def test_unitful_property_input_decoration_not_a_function():
    class UnitfulMock(MockInstrument):

        a = unitful_property("MOCK:A", u.hertz, input_decoration=float)

    mock_instrument = UnitfulMock({"MOCK:A?": ".123"})

    assert mock_instrument.a == 0.123 * u.Hz


def test_unitful_property_output_decoration():
    class UnitfulMock(MockInstrument):
        @staticmethod
        def _output_decorator(_):
            return "1"

        a = unitful_property("MOCK:A", u.hertz, output_decoration=_output_decorator)

    mock_instrument = UnitfulMock()

    mock_instrument.a = 345 * u.hertz

    assert mock_instrument.value == "MOCK:A 1\n"


def test_unitful_property_output_decoration_not_a_function():
    class UnitfulMock(MockInstrument):

        a = unitful_property("MOCK:A", u.hertz, output_decoration=bool)

    mock_instrument = UnitfulMock()

    mock_instrument.a = 1 * u.hertz

    assert mock_instrument.value == "MOCK:A True\n"


def test_unitful_property_split_str():
    class UnitfulMock(MockInstrument):
        unitful_property = unitful_property("MOCK", u.hertz, valid_range=(0, 10))

    mock_inst = UnitfulMock({"MOCK?": "1 kHz"})

    value = mock_inst.unitful_property
    assert value.magnitude == 1000
    assert value.units == u.hertz


def test_unitful_property_name_read_not_none():
    class UnitfulMock(MockInstrument):
        a = unitful_property("MOCK", units=u.hertz, set_cmd="FOOBAR")

    mock_inst = UnitfulMock({"MOCK?": "1000"})
    assert mock_inst.a == 1000 * u.hertz
    mock_inst.a = 1000 * u.hertz

    assert mock_inst.value == f"MOCK?\nFOOBAR {1000:e}\n"
