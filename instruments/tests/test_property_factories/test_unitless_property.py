#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing tests for the unitless property factory
"""

# IMPORTS ####################################################################

from __future__ import absolute_import

import pytest
import quantities as pq

from instruments.util_fns import unitless_property
from . import MockInstrument

# TEST CASES #################################################################

# pylint: disable=missing-docstring


def test_unitless_property_basics():
    class UnitlessMock(MockInstrument):
        mock_property = unitless_property('MOCK')

    mock_inst = UnitlessMock({'MOCK?': '1'})

    assert mock_inst.mock_property == 1

    mock_inst.mock_property = 1
    assert mock_inst.value == 'MOCK?\nMOCK {:e}\n'.format(1)


def test_unitless_property_units():
    with pytest.raises(ValueError):
        class UnitlessMock(MockInstrument):
            mock_property = unitless_property('MOCK')

        mock_inst = UnitlessMock({'MOCK?': '1'})

        mock_inst.mock_property = 1 * pq.volt


def test_unitless_property_format_code():
    class UnitlessMock(MockInstrument):
        mock_property = unitless_property('MOCK', format_code='{:f}')

    mock_inst = UnitlessMock()

    mock_inst.mock_property = 1
    assert mock_inst.value == 'MOCK {:f}\n'.format(1)


def test_unitless_property_writeonly_reading_fails():
    with pytest.raises(AttributeError):
        class UnitlessMock(MockInstrument):
            mock_property = unitless_property('MOCK', writeonly=True)

        mock_inst = UnitlessMock()

        _ = mock_inst.mock_property


def test_unitless_property_writeonly_writing_passes():
    class UnitlessMock(MockInstrument):
        mock_property = unitless_property('MOCK', writeonly=True)

    mock_inst = UnitlessMock()

    mock_inst.mock_property = 1
    assert mock_inst.value == 'MOCK {:e}\n'.format(1)


def test_unitless_property_readonly_writing_fails():
    with pytest.raises(AttributeError):
        class UnitlessMock(MockInstrument):
            mock_property = unitless_property('MOCK', readonly=True)

        mock_inst = UnitlessMock({'MOCK?': '1'})

        mock_inst.mock_property = 1


def test_unitless_property_readonly_reading_passes():
    class UnitlessMock(MockInstrument):
        mock_property = unitless_property('MOCK', readonly=True)

    mock_inst = UnitlessMock({'MOCK?': '1'})

    assert mock_inst.mock_property == 1


def test_unitless_property_set_cmd():
    class UnitlessMock(MockInstrument):
        mock_property = unitless_property('MOCK', set_cmd='FOOBAR')

    mock_inst = UnitlessMock({'MOCK?': '1'})

    assert mock_inst.mock_property == 1
    mock_inst.mock_property = 1

    assert mock_inst.value == 'MOCK?\nFOOBAR {:e}\n'.format(1)
