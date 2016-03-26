#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing tests for the Toptica Topmode
"""

# IMPORTS #####################################################################

from __future__ import absolute_import

from nose.tools import raises
import quantities as pq

import instruments as ik
from instruments.tests import expected_protocol

# TESTS #######################################################################


def test_serial_number():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'laser1:serial-number)",
            "(param-ref 'laser2:serial-number)"
        ],
        [
            "(param-ref 'laser1:serial-number)\r",
            "bloop1",
            "> (param-ref 'laser2:serial-number)\r",
            "bloop2",
            "> "
        ],
        sep="\n"
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
            "(param-ref 'laser1:model)\r",
            "bloop1",
            "> (param-ref 'laser2:model)\r",
            "bloop2",
            "> "
        ],
        sep="\n"
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
            "(param-ref 'laser1:wavelength)\r",
            "640",
            "> (param-ref 'laser2:wavelength)\r",
            "405.3",
            "> "
        ],
        sep="\n"
    ) as tm:
        assert tm.laser[0].wavelength == 640 * pq.nm
        assert tm.laser[1].wavelength == 405.3 * pq.nm


def test_laser_enable():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'laser1:emission)",
            "(param-set! 'laser1:enable-emission #t)"
        ],
        [
            "(param-ref 'laser1:emission)\r",
            "#f",
            "> (param-set! 'laser1:enable-emission #t)\r",
            "0",
            "> "
        ],
        sep="\n"
    ) as tm:
        assert tm.laser[0].enable is False
        tm.laser[0].enable = True


@raises(TypeError)
def test_laser_enable_error():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-set! 'laser1:enable-emission #t)"
        ],
        [
            "(param-set! 'laser1:enable-emission #t)\r",
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
            "(param-ref 'laser1:tec:ready)\r",
            "#f",
            "> "
        ],
        sep="\n"
    ) as tm:
        assert tm.laser[0].tec_status is False


def test_laser_intensity():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'laser1:intensity)"
        ],
        [
            "(param-ref 'laser1:intensity)\r",
            "0.666",
            "> "
        ],
        sep="\n"
    ) as tm:
        assert tm.laser[0].intensity == 0.666


def test_laser_mode_hop():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'laser1:charm:reg:mh-occured)"
        ],
        [
            "(param-ref 'laser1:charm:reg:mh-occured)\r",
            "#f",
            "> "
        ],
        sep="\n"
    ) as tm:
        assert tm.laser[0].mode_hop is False


def test_laser_lock_start():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'laser1:charm:reg:started)"
        ],
        [
            "(param-ref 'laser1:charm:reg:started)\r",
            "\"\"",
            "> "
        ],
        sep="\n"
    ) as tm:
        assert tm.laser[0].lock_start is None


def test_laser_first_mode_hop_time():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'laser1:charm:reg:first-mh)"
        ],
        [
            "(param-ref 'laser1:charm:reg:first-mh)\r",
            "\"\"",
            "> "
        ],
        sep="\n"
    ) as tm:
        assert tm.laser[0].first_mode_hop_time is None


def test_laser_latest_mode_hop_time():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'laser1:charm:reg:latest-mh)"
        ],
        [
            "(param-ref 'laser1:charm:reg:latest-mh)\r",
            "\"\"",
            "> "
        ],
        sep="\n"
    ) as tm:
        assert tm.laser[0].latest_mode_hop_time is None


def test_laser_correction_status():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'laser1:charm:correction-status)"
        ],
        [
            "(param-ref 'laser1:charm:correction-status)\r",
            "0",
            "> "
        ],
        sep="\n"
    ) as tm:
        assert tm.laser[
            0].correction_status == ik.toptica.TopMode.CharmStatus.un_initialized


def test_laser_correction():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'laser1:charm:correction-status)",
            "(exec 'laser1:charm:start-correction-initial)",
            "(param-ref 'laser1:charm:correction-status)",
            "(exec 'laser1:charm:start-correction)"
        ],
        [
            "(param-ref 'laser1:charm:correction-status)\r",
            "0",
            "> (exec 'laser1:charm:start-correction-initial)\r",
            "> (param-ref 'laser1:charm:correction-status)\r",
            "1",
            "> (exec 'laser1:charm:start-correction)\r",
            "> "
        ],
        sep="\n"
    ) as tm:
        tm.laser[0].correction()
        tm.laser[0].correction()


def test_reboot_system():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(exec 'reboot-system)"
        ],
        [
            "(exec 'reboot-system)\r",
            "> "
        ],
        sep="\n"
    ) as tm:
        tm.reboot()


def test_laser_ontime():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'laser1:ontime)"
        ],
        [
            "(param-ref 'laser1:ontime)\r",
            "10000",
            "> "
        ],
        sep="\n"
    ) as tm:
        assert tm.laser[0].on_time == 10000 * pq.s


def test_laser_charm_status():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'laser1:health)"
        ],
        [
            "(param-ref 'laser1:health)\r",
            "230",
            "> "
        ],
        sep="\n"
    ) as tm:
        assert tm.laser[0].charm_status == 1


def test_laser_temperature_control_status():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'laser1:health)"
        ],
        [
            "(param-ref 'laser1:health)\r",
            "230",
            "> "
        ],
        sep="\n"
    ) as tm:
        assert tm.laser[0].temperature_control_status == 1


def test_laser_current_control_status():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'laser1:health)"
        ],
        [
            "(param-ref 'laser1:health)\r",
            "230",
            "> "
        ],
        sep="\n"
    ) as tm:
        assert tm.laser[0].current_control_status == 1


def test_laser_production_date():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'laser1:production-date)"
        ],
        [
            "(param-ref 'laser1:production-date)\r",
            "2016-01-16",
            "> "
        ],
        sep="\n"
    ) as tm:
        assert tm.laser[0].production_date == "2016-01-16"


def test_set_str():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-set! 'blo \"blee\")"
        ],
        [
            "(param-set! 'blo \"blee\")\r",
            "0",
            "> "
        ],
        sep="\n"
    ) as tm:
        tm.set('blo', 'blee')


def test_set_list():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-set! 'blo '(blee blo))"
        ],
        [
            "(param-set! 'blo '(blee blo))\r",
            "0",
            "> "
        ],
        sep="\n"
    ) as tm:
        tm.set('blo', ['blee', 'blo'])


def test_display():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-disp 'blo)"
        ],
        [
            "(param-disp 'blo)\r",
            "bloop",
            "> "
        ],
        sep="\n"
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
            "(param-ref 'emission)\r",
            "#f",
            "> (param-set! 'enable-emission #f)\r",
            "0",
            "> "
        ],
        sep="\n"
    ) as tm:
        assert tm.enable is False
        tm.enable = False


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
        sep="\n"
    ) as tm:
        tm.enable = "False"


def test_front_key():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'front-key-locked)"
        ],
        [
            "(param-ref 'front-key-locked)\r",
            "#f",
            "> "
        ],
        sep="\n"
    ) as tm:
        assert tm.locked is False


def test_interlock():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'interlock-open)"
        ],
        [
            "(param-ref 'interlock-open)\r",
            "#f",
            "> "
        ],
        sep="\n"
    ) as tm:
        assert tm.interlock is False


def test_fpga_status():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'system-health)"
        ],
        [
            "(param-ref 'system-health)\r",
            "0",
            "> "
        ],
        sep="\n"
    ) as tm:
        assert tm.fpga_status is True


def test_temperature_status():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'system-health)"
        ],
        [
            "(param-ref 'system-health)\r",
            "2",
            "> "
        ],
        sep="\n"
    ) as tm:
        assert tm.temperature_status is False


def test_current_status():
    with expected_protocol(
        ik.toptica.TopMode,
        [
            "(param-ref 'system-health)"
        ],
        [
            "(param-ref 'system-health)\r",
            "4",
            "> "
        ],
        sep="\n"
    ) as tm:
        assert tm.current_status is False
