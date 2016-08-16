#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing tests for the Toptica Topmode
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from datetime import datetime
from nose.tools import raises
import quantities as pq


import instruments as ik
from instruments.tests import expected_protocol

# TESTS #######################################################################


def test_laser_serial_number():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'laser1:serial-number)",
            "(param-ref 'laser2:serial-number)"
        ],
        [
            "(param-ref 'laser1:serial-number)",
            "bloop1",
            "> (param-ref 'laser2:serial-number)",
            "bloop2",
            "> "
        ],
        sep="\r\n"
    ) as tm:
        assert tm.laser[0].serial_number == "bloop1"
        assert tm.laser[1].serial_number == "bloop2"


def test_model():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'laser1:model)",
            "(param-ref 'laser2:model)"
        ],
        [
            "(param-ref 'laser1:model)",
            "bloop1",
            "> (param-ref 'laser2:model)",
            "bloop2",
            "> "
        ],
        sep="\r\n"
    ) as tm:
        assert tm.laser[0].model == "bloop1"
        assert tm.laser[1].model == "bloop2"


def test_wavelength():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'laser1:wavelength)",
            "(param-ref 'laser2:wavelength)"
        ],
        [
            "(param-ref 'laser1:wavelength)",
            "640",
            "> (param-ref 'laser2:wavelength)",
            "405.3",
            "> "
        ],
        sep="\r\n"
    ) as tm:
        assert tm.laser[0].wavelength == 640 * pq.nm
        assert tm.laser[1].wavelength == 405.3 * pq.nm


def test_laser_enable():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'laser1:emission)",
            "(param-ref 'laser1:serial-number)",
            "(param-set! 'laser1:enable-emission #t)"
        ],
        [
            "(param-ref 'laser1:emission)",
            "#f",
            "> (param-ref 'laser1:serial-number)",
            "bloop1",
            "> (param-set! 'laser1:enable-emission #t)",
            "0",
            "> "
        ],
        sep="\r\n"
    ) as tm:
        assert tm.laser[0].enable is False
        tm.laser[0].enable = True


@raises(RuntimeError)
def test_laser_enable_no_laser():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'laser1:serial-number)",
            "(param-set! 'laser1:enable-emission #t)"
        ],
        [
            "(param-ref 'laser1:serial-number)",
            "unknown",
            "> (param-set! 'laser1:enable-emission #t)",
            "0",
            "> "
        ],
        sep="\r\n"
    ) as tm:
        tm.laser[0].enable = True


@raises(TypeError)
def test_laser_enable_error():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'laser1:serial-number)",
            "(param-set! 'laser1:enable-emission #t)"
        ],
        [
            "(param-ref 'laser1:serial-number)",
            "bloop1",
            "> (param-set! 'laser1:enable-emission #t)",
            "0",
            "> "
        ],
        sep="\n"
    ) as tm:
        tm.laser[0].enable = 'True'


def test_laser_tec_status():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'laser1:tec:ready)"
        ],
        [
            "(param-ref 'laser1:tec:ready)",
            "#f",
            "> "
        ],
        sep="\r\n"
    ) as tm:
        assert tm.laser[0].tec_status is False


def test_laser_intensity():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'laser1:intensity)"
        ],
        [
            "(param-ref 'laser1:intensity)",
            "0.666",
            "> "
        ],
        sep="\r\n"
    ) as tm:
        assert tm.laser[0].intensity == 0.666


def test_laser_mode_hop():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'laser1:charm:reg:mh-occurred)"
        ],
        [
            "(param-ref 'laser1:charm:reg:mh-occurred)",
            "#f",
            "> "
        ],
        sep="\r\n"
    ) as tm:
        assert tm.laser[0].mode_hop is False


def test_laser_lock_start():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'laser1:charm:correction-status)",
            "(param-ref 'laser1:charm:reg:started)"
        ],
        [
            "(param-ref 'laser1:charm:correction-status)",
            "2",
            "> (param-ref 'laser1:charm:reg:started)",
            "\"2012-12-01 01:02:01\"",
            "> "
        ],
        sep="\r\n"
    ) as tm:
        _date = datetime(2012, 12, 1, 1, 2, 1)
        assert tm.laser[0].lock_start == _date

@raises(RuntimeError)
def test_laser_lock_start_runtime_error():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'laser1:charm:correction-status)",
            "(param-ref 'laser1:charm:reg:started)"
        ],
        [
            "(param-ref 'laser1:charm:correction-status)",
            "0",
            "> (param-ref 'laser1:charm:reg:started)",
            "\"\"",
            "> "
        ],
        sep="\r\n"
    ) as tm:
        _date = datetime(2012, 12, 1, 1, 2, 1)
        assert tm.laser[0].lock_start == _date


@raises(RuntimeError)
def test_laser_first_mode_hop_time_runtime_error():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'laser1:charm:reg:mh-occurred)",
            "(param-ref 'laser1:charm:reg:first-mh)"
        ],
        [
            "(param-ref 'laser1:charm:reg:mh-occurred)",
            "#f",
            "> (param-ref 'laser1:charm:reg:first-mh)",
            "\"\"",
            "> "
        ],
        sep="\r\n"
    ) as tm:
        assert tm.laser[0].first_mode_hop_time is None


def test_laser_first_mode_hop_time():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'laser1:charm:reg:mh-occurred)",
            "(param-ref 'laser1:charm:reg:first-mh)"
        ],
        [
            "(param-ref 'laser1:charm:reg:mh-occurred)",
            "#t",
            "> (param-ref 'laser1:charm:reg:first-mh)",
            "\"2012-12-01 01:02:01\"",
            "> "
        ],
        sep="\r\n"
    ) as tm:
        _date = datetime(2012, 12, 1, 1, 2, 1)
        assert tm.laser[0].first_mode_hop_time == _date


@raises(RuntimeError)
def test_laser_latest_mode_hop_time_none():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'laser1:charm:reg:mh-occurred)",
            "(param-ref 'laser1:charm:reg:latest-mh)"
        ],
        [
            "(param-ref 'laser1:charm:reg:mh-occurred)",
            "#f",
            "> (param-ref 'laser1:charm:reg:latest-mh)",
            "\"\"",
            "> "
        ],
        sep="\r\n"
    ) as tm:
        assert tm.laser[0].latest_mode_hop_time is None


def test_laser_latest_mode_hop_time():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'laser1:charm:reg:mh-occurred)",
            "(param-ref 'laser1:charm:reg:latest-mh)"
        ],
        [
            "(param-ref 'laser1:charm:reg:mh-occurred)",
            "#t",
            "> (param-ref 'laser1:charm:reg:latest-mh)",
            "\"2012-12-01 01:02:01\"",
            "> "
        ],
        sep="\r\n"
    ) as tm:
        _date = datetime(2012, 12, 1, 1, 2, 1)
        assert tm.laser[0].latest_mode_hop_time == _date


def test_laser_correction_status():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'laser1:charm:correction-status)"
        ],
        [
            "(param-ref 'laser1:charm:correction-status)",
            "0",
            "> "
        ],
        sep="\r\n"
    ) as tm:
        assert tm.laser[
            0].correction_status == ik.toptica.TopMode.CharmStatus.un_initialized


def test_laser_correction():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'laser1:charm:correction-status)",  # 1st
            "(exec 'laser1:charm:start-correction-initial)",
            "(param-ref 'laser1:charm:correction-status)",  # 2nd
            "(exec 'laser1:charm:start-correction)",
            "(param-ref 'laser1:charm:correction-status)",  # 3rd
            "(param-ref 'laser1:charm:correction-status)",  # 4th
            "(exec 'laser1:charm:start-correction)"
        ],
        [
            "(param-ref 'laser1:charm:correction-status)",  # 1st
            "0",
            "> (exec 'laser1:charm:start-correction-initial)",
            "()",
            "> (param-ref 'laser1:charm:correction-status)",  # 3nd
            "1",
            "> (exec 'laser1:charm:start-correction)",
            "()",
            "> (param-ref 'laser1:charm:correction-status)",  # 3rd
            "3",
            "> (param-ref 'laser1:charm:correction-status)",  # 4th
            "2",
            "> (exec 'laser1:charm:start-correction)",
            "()",
            "> ",
        ],
        sep="\r\n"
    ) as tm:
        tm.laser[0].correction()
        tm.laser[0].correction()
        _ = tm.laser[0].correction_status
        tm.laser[0].correction()


def test_reboot_system():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(exec 'reboot-system)"
        ],
        [
            "(exec 'reboot-system)",
            "reboot process started.",
            "> "
        ],
        sep="\r\n"
    ) as tm:
        tm.reboot()


def test_laser_ontime():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'laser1:ontime)"
        ],
        [
            "(param-ref 'laser1:ontime)",
            "10000",
            "> "
        ],
        sep="\r\n"
    ) as tm:
        assert tm.laser[0].on_time == 10000 * pq.s


def test_laser_charm_status():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'laser1:health)"
        ],
        [
            "(param-ref 'laser1:health)",
            "230",
            "> "
        ],
        sep="\r\n"
    ) as tm:
        assert tm.laser[0].charm_status == 1


def test_laser_temperature_control_status():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'laser1:health)"
        ],
        [
            "(param-ref 'laser1:health)",
            "230",
            "> "
        ],
        sep="\r\n"
    ) as tm:
        assert tm.laser[0].temperature_control_status == 1


def test_laser_current_control_status():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'laser1:health)"
        ],
        [
            "(param-ref 'laser1:health)",
            "230",
            "> "
        ],
        sep="\r\n"
    ) as tm:
        assert tm.laser[0].current_control_status == 1


def test_laser_production_date():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'laser1:production-date)"
        ],
        [
            "(param-ref 'laser1:production-date)",
            "2016-01-16",
            "> "
        ],
        sep="\r\n"
    ) as tm:
        assert tm.laser[0].production_date == "2016-01-16"


def test_set_str():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-set! 'blo \"blee\")"
        ],
        [
            "(param-set! 'blo \"blee\")",
            "0",
            "> "
        ],
        sep="\r\n"
    ) as tm:
        tm.set('blo', 'blee')


def test_set_list():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-set! 'blo '(blee blo))"
        ],
        [
            "(param-set! 'blo '(blee blo))",
            "0",
            "> "
        ],
        sep="\r\n"
    ) as tm:
        tm.set('blo', ['blee', 'blo'])


def test_display():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-disp 'blo)"
        ],
        [
            "(param-disp 'blo)",
            "bloop",
            "> "
        ],
        sep="\r\n"
    ) as tm:
        assert tm.display('blo') == "bloop"


def test_enable():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'emission)",
            "(param-set! 'enable-emission #f)"
        ],
        [
            "(param-ref 'emission)",
            "#f",
            "> (param-set! 'enable-emission #f)",
            "0",
            "> "
        ],
        sep="\r\n"
    ) as tm:
        assert tm.enable is False
        tm.enable = False


def test_firmware():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'fw-ver)"
        ],
        [
            "(param-ref 'fw-ver)",
            "1.02.01",
            "> "
        ],
        sep="\r\n"
    ) as tm:
        assert tm.firmware == (1, 2, 1)


def test_serial_number():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'serial-number)"
        ],
        [
            "(param-ref 'serial-number)",
            "010101",
            "> "
        ],
        sep="\r\n"
    ) as tm:
        assert tm.serial_number == '010101'


@raises(TypeError)
def test_enable_error():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-set! 'enable-emission #f)"
        ],
        [
            "(param-set! 'enable-emission #f)",
            ">"
        ],
        sep="\r\n"
    ) as tm:
        tm.enable = "False"


def test_front_key():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'front-key-locked)"
        ],
        [
            "(param-ref 'front-key-locked)",
            "#f",
            "> "
        ],
        sep="\r\n"
    ) as tm:
        assert tm.locked is False


def test_interlock():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'interlock-open)"
        ],
        [
            "(param-ref 'interlock-open)",
            "#f",
            "> "
        ],
        sep="\r\n"
    ) as tm:
        assert tm.interlock is False


def test_fpga_status():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'system-health)"
        ],
        [
            "(param-ref 'system-health)",
            "0",
            "> "
        ],
        sep="\r\n"
    ) as tm:
        assert tm.fpga_status is True


def test_fpga_status_false():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'system-health)"
        ],
        [
            "(param-ref 'system-health)",
            "#f",
            "> "
        ],
        sep="\r\n"
    ) as tm:
        assert tm.fpga_status is False


def test_temperature_status():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'system-health)"
        ],
        [
            "(param-ref 'system-health)",
            "2",
            "> "
        ],
        sep="\r\n"
    ) as tm:
        assert tm.temperature_status is False


def test_current_status():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'system-health)"
        ],
        [
            "(param-ref 'system-health)",
            "4",
            "> "
        ],
        sep="\r\n"
    ) as tm:
        assert tm.current_status is False
