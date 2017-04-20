#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing tests for util_fns.py
"""

# IMPORTS ####################################################################

from __future__ import absolute_import, unicode_literals

from io import StringIO

import quantities as pq

from instruments import Instrument
from instruments.config import (
    load_instruments, yaml
)

# TEST CASES #################################################################

# pylint: disable=protected-access,missing-docstring

def test_load_test_instrument():
    config_data = StringIO(u"""
test:
    class: !!python/name:instruments.Instrument
    uri: test://
""")
    insts = load_instruments(config_data)
    assert isinstance(insts['test'], Instrument)

def test_load_test_instrument_subtree():
    config_data = StringIO(u"""
instruments:
    test:
        class: !!python/name:instruments.Instrument
        uri: test://
""")
    insts = load_instruments(config_data, conf_path="/instruments")
    assert isinstance(insts['test'], Instrument)

def test_yaml_quantity_tag():
    yaml_data = StringIO(u"""
a:
    b: !Q 37 tesla
    c: !Q 41.2 inches
    d: !Q 98
""")
    data = yaml.load(yaml_data, Loader=yaml.Loader)
    assert data['a']['b'] == pq.Quantity(37, 'tesla')
    assert data['a']['c'] == pq.Quantity(41.2, 'inches')
    assert data['a']['d'] == 98

def test_load_test_instrument_setattr():
    config_data = StringIO(u"""
test:
    class: !!python/name:instruments.Instrument
    uri: test://
    attrs:
        foo: !Q 111 GHz
""")
    insts = load_instruments(config_data)
    assert insts['test'].foo == pq.Quantity(111, 'GHz')
