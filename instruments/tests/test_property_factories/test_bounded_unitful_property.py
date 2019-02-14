#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing tests for the bounded unitful property factories
"""

# IMPORTS ####################################################################

from __future__ import absolute_import

import pytest
import quantities as pq

from instruments.util_fns import bounded_unitful_property
from . import MockInstrument
from .. import mock

# TEST CASES #################################################################

# pylint: disable=missing-docstring


def test_bounded_unitful_property_basics():
    class BoundedUnitfulMock(MockInstrument):
        property, property_min, property_max = bounded_unitful_property(
            'MOCK',
            units=pq.hertz
        )

    mock_inst = BoundedUnitfulMock(
        {'MOCK?': '1000', 'MOCK:MIN?': '10', 'MOCK:MAX?': '9999'})

    assert mock_inst.property == 1000 * pq.hertz
    assert mock_inst.property_min == 10 * pq.hertz
    assert mock_inst.property_max == 9999 * pq.hertz

    mock_inst.property = 1000 * pq.hertz


def test_bounded_unitful_property_set_outside_max():
    with pytest.raises(ValueError):
        class BoundedUnitfulMock(MockInstrument):
            property, property_min, property_max = bounded_unitful_property(
                'MOCK',
                units=pq.hertz
            )

        mock_inst = BoundedUnitfulMock(
            {'MOCK?': '1000', 'MOCK:MIN?': '10', 'MOCK:MAX?': '9999'})

        mock_inst.property = 10000 * pq.hertz  # Should raise ValueError


def test_bounded_unitful_property_set_outside_min():
    with pytest.raises(ValueError):
        class BoundedUnitfulMock(MockInstrument):
            property, property_min, property_max = bounded_unitful_property(
                'MOCK',
                units=pq.hertz
            )

        mock_inst = BoundedUnitfulMock(
            {'MOCK?': '1000', 'MOCK:MIN?': '10', 'MOCK:MAX?': '9999'})

        mock_inst.property = 1 * pq.hertz  # Should raise ValueError


def test_bounded_unitful_property_min_fmt_str():
    class BoundedUnitfulMock(MockInstrument):
        property, property_min, property_max = bounded_unitful_property(
            'MOCK',
            units=pq.hertz,
            min_fmt_str="{} MIN?"
        )

    mock_inst = BoundedUnitfulMock({'MOCK MIN?': '10'})

    assert mock_inst.property_min == 10 * pq.Hz
    assert mock_inst.value == 'MOCK MIN?\n'


def test_bounded_unitful_property_max_fmt_str():
    class BoundedUnitfulMock(MockInstrument):
        property, property_min, property_max = bounded_unitful_property(
            'MOCK',
            units=pq.hertz,
            max_fmt_str="{} MAX?"
        )

    mock_inst = BoundedUnitfulMock({'MOCK MAX?': '9999'})

    assert mock_inst.property_max == 9999 * pq.Hz
    assert mock_inst.value == 'MOCK MAX?\n'


def test_bounded_unitful_property_static_range():
    class BoundedUnitfulMock(MockInstrument):
        property, property_min, property_max = bounded_unitful_property(
            'MOCK',
            units=pq.hertz,
            valid_range=(10, 9999)
        )

    mock_inst = BoundedUnitfulMock()

    assert mock_inst.property_min == 10 * pq.Hz
    assert mock_inst.property_max == 9999 * pq.Hz


def test_bounded_unitful_property_static_range_with_units():
    class BoundedUnitfulMock(MockInstrument):
        property, property_min, property_max = bounded_unitful_property(
            'MOCK',
            units=pq.hertz,
            valid_range=(10 * pq.kilohertz, 9999 * pq.kilohertz)
        )

    mock_inst = BoundedUnitfulMock()

    assert mock_inst.property_min == 10 * 1000 * pq.Hz
    assert mock_inst.property_max == 9999 * 1000 * pq.Hz


@mock.patch("instruments.util_fns.unitful_property")
def test_bounded_unitful_property_passes_kwargs(mock_unitful_property):
    bounded_unitful_property(
        command='MOCK',
        units=pq.Hz,
        derp="foobar"
    )
    mock_unitful_property.assert_called_with(
        'MOCK',
        pq.Hz,
        derp="foobar",
        valid_range=(mock.ANY, mock.ANY)
    )


@mock.patch("instruments.util_fns.unitful_property")
def test_bounded_unitful_property_valid_range_none(mock_unitful_property):
    bounded_unitful_property(
        command='MOCK',
        units=pq.Hz,
        valid_range=(None, None)
    )
    mock_unitful_property.assert_called_with(
        'MOCK',
        pq.Hz,
        valid_range=(None, None)
    )


def test_bounded_unitful_property_returns_none():
    class BoundedUnitfulMock(MockInstrument):
        property, property_min, property_max = bounded_unitful_property(
            'MOCK',
            units=pq.hertz,
            valid_range=(None, None)
        )

    mock_inst = BoundedUnitfulMock()

    assert mock_inst.property_min is None
    assert mock_inst.property_max is None
