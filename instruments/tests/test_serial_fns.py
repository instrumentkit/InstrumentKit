#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing tests for the serial helper functions.
"""
from __future__ import absolute_import
from mock import patch
from serial.tools.list_ports_common import ListPortInfo

from instruments import Device


def fake_comports():
    dev = ListPortInfo()
    dev.vid = 0
    dev.pid = 1000
    dev.serial_number = 'a1'
    dev.device = 'COM1'
    return [dev]


@patch('instruments.serial_fns.comports', new=fake_comports)
def test_comparison():
    hardware = Device(vid=0, pid=1000)
    hardware2 = Device(vid=0, pid=1000, serial_number='a0')
    assert hardware.port == 'COM1'
    assert hardware2.port is None

