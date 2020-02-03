#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing tests for the abstract function generator class
"""

# IMPORTS ####################################################################


import pytest
import instruments.units as u

import instruments as ik


# TESTS ######################################################################

# pylint: disable=missing-function-docstring,redefined-outer-name,protected-access

@pytest.fixture
def fg():
    return ik.abstract_instruments.FunctionGenerator.open_test()


def test_func_gen_default_channel_count(fg):
    assert fg._channel_count == 1


def test_func_gen_raises_not_implemented_error_one_channel_getting(fg):
    fg._channel_count = 1
    with pytest.raises(NotImplementedError):
        _ = fg.amplitude
    with pytest.raises(NotImplementedError):
        _ = fg.frequency
    with pytest.raises(NotImplementedError):
        _ = fg.function
    with pytest.raises(NotImplementedError):
        _ = fg.offset
    with pytest.raises(NotImplementedError):
        _ = fg.phase


def test_func_gen_raises_not_implemented_error_one_channel_setting(fg):
    fg._channel_count = 1
    with pytest.raises(NotImplementedError):
        fg.amplitude = 1
    with pytest.raises(NotImplementedError):
        fg.frequency = 1
    with pytest.raises(NotImplementedError):
        fg.function = 1
    with pytest.raises(NotImplementedError):
        fg.offset = 1
    with pytest.raises(NotImplementedError):
        fg.phase = 1


def test_func_gen_raises_not_implemented_error_two_channel_getting(fg):
    fg._channel_count = 2
    with pytest.raises(NotImplementedError):
        _ = fg.channel[0].amplitude
    with pytest.raises(NotImplementedError):
        _ = fg.channel[0].frequency
    with pytest.raises(NotImplementedError):
        _ = fg.channel[0].function
    with pytest.raises(NotImplementedError):
        _ = fg.channel[0].offset
    with pytest.raises(NotImplementedError):
        _ = fg.channel[0].phase


def test_func_gen_raises_not_implemented_error_two_channel_setting(fg):
    fg._channel_count = 2
    with pytest.raises(NotImplementedError):
        fg.channel[0].amplitude = 1
    with pytest.raises(NotImplementedError):
        fg.channel[0].frequency = 1
    with pytest.raises(NotImplementedError):
        fg.channel[0].function = 1
    with pytest.raises(NotImplementedError):
        fg.channel[0].offset = 1
    with pytest.raises(NotImplementedError):
        fg.channel[0].phase = 1


def test_func_gen_two_channel_passes_thru_call_getter(fg, mocker):
    mock_channel = mocker.MagicMock()
    mock_properties = [mocker.PropertyMock(return_value=1) for _ in range(5)]

    mocker.patch("instruments.abstract_instruments.FunctionGenerator.Channel", new=mock_channel)
    type(mock_channel()).amplitude = mock_properties[0]
    type(mock_channel()).frequency = mock_properties[1]
    type(mock_channel()).function = mock_properties[2]
    type(mock_channel()).offset = mock_properties[3]
    type(mock_channel()).phase = mock_properties[4]

    fg._channel_count = 2
    _ = fg.amplitude
    _ = fg.frequency
    _ = fg.function
    _ = fg.offset
    _ = fg.phase

    for mock_property in mock_properties:
        mock_property.assert_called_once_with()


def test_func_gen_one_channel_passes_thru_call_getter(fg, mocker):
    mock_properties = [mocker.PropertyMock(return_value=1) for _ in range(4)]
    mock_method = mocker.MagicMock(return_value=(1, u.V))

    mocker.patch("instruments.abstract_instruments.FunctionGenerator.frequency", new=mock_properties[0])
    mocker.patch("instruments.abstract_instruments.FunctionGenerator.function", new=mock_properties[1])
    mocker.patch("instruments.abstract_instruments.FunctionGenerator.offset", new=mock_properties[2])
    mocker.patch("instruments.abstract_instruments.FunctionGenerator.phase", new=mock_properties[3])
    mocker.patch("instruments.abstract_instruments.FunctionGenerator._get_amplitude_", new=mock_method)

    fg._channel_count = 1
    _ = fg.channel[0].amplitude
    _ = fg.channel[0].frequency
    _ = fg.channel[0].function
    _ = fg.channel[0].offset
    _ = fg.channel[0].phase

    for mock_property in mock_properties:
        mock_property.assert_called_once_with()

    mock_method.assert_called_once_with()


def test_func_gen_two_channel_passes_thru_call_setter(fg, mocker):
    mock_channel = mocker.MagicMock()
    mock_properties = [mocker.PropertyMock() for _ in range(5)]

    mocker.patch("instruments.abstract_instruments.FunctionGenerator.Channel", new=mock_channel)
    type(mock_channel()).amplitude = mock_properties[0]
    type(mock_channel()).frequency = mock_properties[1]
    type(mock_channel()).function = mock_properties[2]
    type(mock_channel()).offset = mock_properties[3]
    type(mock_channel()).phase = mock_properties[4]

    fg._channel_count = 2
    fg.amplitude = 1
    fg.frequency = 1
    fg.function = 1
    fg.offset = 1
    fg.phase = 1

    for mock_property in mock_properties:
        mock_property.assert_called_once_with(1)


def test_func_gen_one_channel_passes_thru_call_setter(fg, mocker):
    mock_properties = [mocker.PropertyMock() for _ in range(4)]
    mock_method = mocker.MagicMock()

    mocker.patch("instruments.abstract_instruments.FunctionGenerator.frequency", new=mock_properties[0])
    mocker.patch("instruments.abstract_instruments.FunctionGenerator.function", new=mock_properties[1])
    mocker.patch("instruments.abstract_instruments.FunctionGenerator.offset", new=mock_properties[2])
    mocker.patch("instruments.abstract_instruments.FunctionGenerator.phase", new=mock_properties[3])
    mocker.patch("instruments.abstract_instruments.FunctionGenerator._set_amplitude_", new=mock_method)

    fg._channel_count = 1
    fg.channel[0].amplitude = 1
    fg.channel[0].frequency = 1
    fg.channel[0].function = 1
    fg.channel[0].offset = 1
    fg.channel[0].phase = 1

    for mock_property in mock_properties:
        mock_property.assert_called_once_with(1)

    mock_method.assert_called_once_with(magnitude=1, units=fg.VoltageMode.peak_to_peak)
