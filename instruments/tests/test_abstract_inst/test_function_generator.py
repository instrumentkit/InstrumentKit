#!/usr/bin/env python
"""
Module containing tests for the abstract function generator class
"""

# IMPORTS ####################################################################


import pytest
from instruments.units import ureg as u

import instruments as ik
from instruments.tests import expected_protocol, unit_eq


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

    mocker.patch(
        "instruments.abstract_instruments.FunctionGenerator.Channel", new=mock_channel
    )
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

    mocker.patch(
        "instruments.abstract_instruments.FunctionGenerator.frequency",
        new=mock_properties[0],
    )
    mocker.patch(
        "instruments.abstract_instruments.FunctionGenerator.function",
        new=mock_properties[1],
    )
    mocker.patch(
        "instruments.abstract_instruments.FunctionGenerator.offset",
        new=mock_properties[2],
    )
    mocker.patch(
        "instruments.abstract_instruments.FunctionGenerator.phase",
        new=mock_properties[3],
    )
    mocker.patch(
        "instruments.abstract_instruments.FunctionGenerator._get_amplitude_",
        new=mock_method,
    )

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

    mocker.patch(
        "instruments.abstract_instruments.FunctionGenerator.Channel", new=mock_channel
    )
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

    mocker.patch(
        "instruments.abstract_instruments.FunctionGenerator.frequency",
        new=mock_properties[0],
    )
    mocker.patch(
        "instruments.abstract_instruments.FunctionGenerator.function",
        new=mock_properties[1],
    )
    mocker.patch(
        "instruments.abstract_instruments.FunctionGenerator.offset",
        new=mock_properties[2],
    )
    mocker.patch(
        "instruments.abstract_instruments.FunctionGenerator.phase",
        new=mock_properties[3],
    )
    mocker.patch(
        "instruments.abstract_instruments.FunctionGenerator._set_amplitude_",
        new=mock_method,
    )

    fg._channel_count = 1
    fg.channel[0].amplitude = 1
    fg.channel[0].frequency = 1
    fg.channel[0].function = 1
    fg.channel[0].offset = 1
    fg.channel[0].phase = 1

    for mock_property in mock_properties:
        mock_property.assert_called_once_with(1)

    mock_method.assert_called_once_with(magnitude=1, units=fg.VoltageMode.peak_to_peak)


def test_func_gen_channel_set_amplitude_dbm(mocker):
    """Get amplitude of channel when units are in dBm."""
    with expected_protocol(ik.abstract_instruments.FunctionGenerator, [], []) as inst:
        value = 3.14
        # mock out the _get_amplitude of parent to return value in dBm
        mocker.patch.object(
            inst,
            "_get_amplitude_",
            return_value=(
                value,
                ik.abstract_instruments.FunctionGenerator.VoltageMode.dBm,
            ),
        )

        channel = inst.channel[0]
        unit_eq(channel.amplitude, u.Quantity(value, u.dBm))


def test_func_gen_channel_sendcmd(mocker):
    """Send a command via parent class function."""
    with expected_protocol(ik.abstract_instruments.FunctionGenerator, [], []) as inst:
        cmd = "COMMAND"
        # mock out parent's send command
        mock_sendcmd = mocker.patch.object(inst, "sendcmd")
        channel = inst.channel[0]
        channel.sendcmd(cmd)
        mock_sendcmd.assert_called_with(cmd)


def test_func_gen__channel_sendcmd(mocker):
    """Send a query via parent class function."""
    with expected_protocol(ik.abstract_instruments.FunctionGenerator, [], []) as inst:
        cmd = "QUERY"
        size = 13
        retval = "ANSWER"
        # mock out parent's query command
        mock_query = mocker.patch.object(inst, "query", return_value=retval)
        channel = inst.channel[0]
        assert channel.query(cmd, size=size) == retval
        mock_query.assert_called_with(cmd, size)
