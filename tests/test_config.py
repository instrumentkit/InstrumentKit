#!/usr/bin/env python
"""
Module containing tests for util_fns.py
"""

# IMPORTS ####################################################################


from io import StringIO

import pytest

from instruments.units import ureg as u

import instruments as ik
from instruments import Instrument
from instruments.config import load_instruments, yaml

# TEST CASES #################################################################

# pylint: disable=protected-access,missing-docstring


def test_load_test_instrument():
    config_data = StringIO(
        """
test:
    class: !!python/name:instruments.Instrument
    uri: test://
"""
    )
    insts = load_instruments(config_data)
    assert isinstance(insts["test"], Instrument)


def test_load_test_instrument_from_file(tmp_path):
    """Load an instrument from a `.yml` file with filename as string."""
    conf_file = tmp_path.joinpath("config.yml")
    conf_file.write_text(
        """
test:
    class: !!python/name:instruments.Instrument
    uri: test://
"""
    )
    insts = load_instruments(str(conf_file.absolute()))
    assert isinstance(insts["test"], Instrument)


def test_load_test_instrument_subtree():
    config_data = StringIO(
        """
instruments:
    test:
        class: !!python/name:instruments.Instrument
        uri: test://
"""
    )
    insts = load_instruments(config_data, conf_path="/instruments")
    assert isinstance(insts["test"], Instrument)


def test_yaml_quantity_tag():
    yaml_data = StringIO(
        """
a:
    b: !Q 37 tesla
    c: !Q 41.2 inches
    d: !Q 98
"""
    )
    data = yaml.load(yaml_data)
    assert data["a"]["b"] == u.Quantity(37, "tesla")
    assert data["a"]["c"] == u.Quantity(41.2, "inches")
    assert data["a"]["d"] == 98


def test_load_test_instrument_setattr():
    config_data = StringIO(
        """
test:
    class: !!python/name:instruments.Instrument
    uri: test://
    attrs:
        foo: !Q 111 GHz
"""
    )
    insts = load_instruments(config_data)
    assert insts["test"].foo == u.Quantity(111, "GHz")


def test_load_test_instrument_oserror(mocker):
    """Raise warning and continue in case loading test instrument fails with OSError."""
    config_data = StringIO(
        """
test:
    class: !!python/name:instruments.Instrument
    uri: test://
"""
    )

    mocker.patch.object(Instrument, "open_from_uri", side_effect=OSError)

    with pytest.warns(RuntimeWarning):
        _ = load_instruments(config_data)
