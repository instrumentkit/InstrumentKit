#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing tests for the unitful property factories
"""

# IMPORTS ####################################################################

from __future__ import absolute_import

from nose.tools import raises, eq_
import quantities as pq

from instruments.util_fns import unitful_property
from . import MockInstrument

# TEST CASES #################################################################

# pylint: disable=missing-docstring,no-self-use


def test_unitful_property_basics():
    class UnitfulMock(MockInstrument):
        unitful_property = unitful_property('MOCK', units=pq.hertz)

    mock_inst = UnitfulMock({'MOCK?': '1000'})

    eq_(mock_inst.unitful_property, 1000 * pq.hertz)

    mock_inst.unitful_property = 1000 * pq.hertz
    eq_(mock_inst.value, 'MOCK?\nMOCK {:e}\n'.format(1000))


def test_unitful_property_format_code():
    class UnitfulMock(MockInstrument):
        unitful_property = unitful_property(
            'MOCK', pq.hertz, format_code='{:f}')

    mock_inst = UnitfulMock()

    mock_inst.unitful_property = 1000 * pq.hertz
    eq_(mock_inst.value, 'MOCK {:f}\n'.format(1000))


def test_unitful_property_rescale_units():
    class UnitfulMock(MockInstrument):
        unitful_property = unitful_property('MOCK', pq.hertz)

    mock_inst = UnitfulMock()

    mock_inst.unitful_property = 1 * pq.kilohertz
    eq_(mock_inst.value, 'MOCK {:e}\n'.format(1000))


def test_unitful_property_no_units_on_set():
    class UnitfulMock(MockInstrument):
        unitful_property = unitful_property('MOCK', pq.hertz)

    mock_inst = UnitfulMock()

    mock_inst.unitful_property = 1000
    eq_(mock_inst.value, 'MOCK {:e}\n'.format(1000))


@raises(ValueError)
def test_unitful_property_wrong_units():
    class UnitfulMock(MockInstrument):
        unitful_property = unitful_property('MOCK', pq.hertz)

    mock_inst = UnitfulMock()

    mock_inst.unitful_property = 1 * pq.volt


@raises(AttributeError)
def test_unitful_property_writeonly_reading_fails():
    class UnitfulMock(MockInstrument):
        unitful_property = unitful_property('MOCK', pq.hertz, writeonly=True)

    mock_inst = UnitfulMock()

    _ = mock_inst.unitful_property


def test_unitful_property_writeonly_writing_passes():
    class UnitfulMock(MockInstrument):
        unitful_property = unitful_property('MOCK', pq.hertz, writeonly=True)

    mock_inst = UnitfulMock()

    mock_inst.unitful_property = 1 * pq.hertz
    eq_(mock_inst.value, 'MOCK {:e}\n'.format(1))


@raises(AttributeError)
def test_unitful_property_readonly_writing_fails():
    class UnitfulMock(MockInstrument):
        unitful_property = unitful_property('MOCK', pq.hertz, readonly=True)

    mock_inst = UnitfulMock({'MOCK?': '1'})

    mock_inst.unitful_property = 1 * pq.hertz


def test_unitful_property_readonly_reading_passes():
    class UnitfulMock(MockInstrument):
        unitful_property = unitful_property('MOCK', pq.hertz, readonly=True)

    mock_inst = UnitfulMock({'MOCK?': '1'})

    eq_(mock_inst.unitful_property, 1 * pq.hertz)


def test_unitful_property_valid_range():
    class UnitfulMock(MockInstrument):
        unitful_property = unitful_property(
            'MOCK', pq.hertz, valid_range=(0, 10))

    mock_inst = UnitfulMock()

    mock_inst.unitful_property = 0
    mock_inst.unitful_property = 10

    eq_(mock_inst.value, 'MOCK {:e}\nMOCK {:e}\n'.format(0, 10))


def test_unitful_property_valid_range_functions():
    class UnitfulMock(MockInstrument):

        def min_value(self):
            return 0

        def max_value(self):
            return 10

        unitful_property = unitful_property(
            'MOCK', pq.hertz, valid_range=(min_value, max_value))

    mock_inst = UnitfulMock()

    mock_inst.unitful_property = 0
    mock_inst.unitful_property = 10

    eq_(mock_inst.value, 'MOCK {:e}\nMOCK {:e}\n'.format(0, 10))


@raises(ValueError)
def test_unitful_property_minimum_value():
    class UnitfulMock(MockInstrument):
        unitful_property = unitful_property(
            'MOCK', pq.hertz, valid_range=(0, 10))

    mock_inst = UnitfulMock()

    mock_inst.unitful_property = -1


@raises(ValueError)
def test_unitful_property_maximum_value():
    class UnitfulMock(MockInstrument):
        unitful_property = unitful_property(
            'MOCK', pq.hertz, valid_range=(0, 10))

    mock_inst = UnitfulMock()

    mock_inst.unitful_property = 11


def test_unitful_property_input_decoration():
    class UnitfulMock(MockInstrument):

        @staticmethod
        def _input_decorator(_):
            return '1'
        a = unitful_property(
            'MOCK:A',
            pq.hertz,
            input_decoration=_input_decorator
        )

    mock_instrument = UnitfulMock({'MOCK:A?': 'garbage'})

    eq_(mock_instrument.a, 1 * pq.Hz)


def test_unitful_property_input_decoration_not_a_function():
    class UnitfulMock(MockInstrument):

        a = unitful_property(
            'MOCK:A',
            pq.hertz,
            input_decoration=float
        )

    mock_instrument = UnitfulMock({'MOCK:A?': '.123'})

    eq_(mock_instrument.a, 0.123 * pq.Hz)


def test_unitful_property_output_decoration():
    class UnitfulMock(MockInstrument):

        @staticmethod
        def _output_decorator(_):
            return '1'
        a = unitful_property(
            'MOCK:A',
            pq.hertz,
            output_decoration=_output_decorator
        )

    mock_instrument = UnitfulMock()

    mock_instrument.a = 345 * pq.hertz

    eq_(mock_instrument.value, 'MOCK:A 1\n')


def test_unitful_property_output_decoration_not_a_function():
    class UnitfulMock(MockInstrument):

        a = unitful_property(
            'MOCK:A',
            pq.hertz,
            output_decoration=bool
        )

    mock_instrument = UnitfulMock()

    mock_instrument.a = 1 * pq.hertz

    eq_(mock_instrument.value, 'MOCK:A True\n')


def test_unitful_property_split_str():
    class UnitfulMock(MockInstrument):
        unitful_property = unitful_property(
            'MOCK', pq.hertz, valid_range=(0, 10))

    mock_inst = UnitfulMock({"MOCK?": "1 kHz"})

    value = mock_inst.unitful_property
    assert value.magnitude == 1000
    assert value.units == pq.hertz
