#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# __init__.py: Tests for HP instruments.
##
# © 2014 Steven Casagrande (scasagrande@galvant.ca).
#
# This file is a part of the InstrumentKit project.
# Licensed under the AGPL version 3.
##
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
##

## IMPORTS ####################################################################

from __future__ import absolute_import

import quantities as pq
import numpy as np

import instruments as ik
from instruments.tests import expected_protocol, make_name_test, unit_eq

## TESTS ######################################################################

test_scpi_multimeter_name = make_name_test(ik.hp.HP6632b)

def test_hp6632b_display_textmode():
    with expected_protocol(
        ik.hp.HP6632b,
        [
            "DISP:MODE?",
            "DISP:MODE TEXT"
        ] , [
            "NORM"
        ]
    ) as psu:
        assert psu.display_textmode == False
        psu.display_textmode = True

def test_hp6632b_display_text():
    with expected_protocol(
        ik.hp.HP6632b,
        [
            'DISP:TEXT "TEST"',
        ] , [
            ""
        ]
    ) as psu:
        assert psu.display_text("TEST") == "TEST"

def test_hp6632b_output():
    with expected_protocol(
        ik.hp.HP6632b,
        [
            "OUTP?",
            "OUTP 1"
        ] , [
            "0"
        ]
    ) as psu:
        assert psu.output == False
        psu.output = True

def test_hp6632b_voltage():
    with expected_protocol(
        ik.hp.HP6632b,
        [
            "VOLT?",
            "VOLT {:e}".format(1)
        ] , [
            "10.0"
        ]
    ) as psu:
        unit_eq(psu.voltage, 10*pq.volt)
        psu.voltage = 1.0 * pq.volt

def test_hp6632b_voltage_sense():
    with expected_protocol(
        ik.hp.HP6632b,
        [
            "MEAS:VOLT?",
        ] , [
            "10.0"
        ]
    ) as psu:
        unit_eq(psu.voltage_sense, 10*pq.volt)

def test_hp6632b_overvoltage():
    with expected_protocol(
        ik.hp.HP6632b,
        [
            "VOLT:PROT?",
            "VOLT:PROT {:e}".format(1)
        ] , [
            "10.0"
        ]
    ) as psu:
        unit_eq(psu.overvoltage, 10*pq.volt)
        psu.overvoltage = 1.0 * pq.volt

def test_hp6632b_current():
    with expected_protocol(
        ik.hp.HP6632b,
        [
            "CURR?",
            "CURR {:e}".format(1)
        ] , [
            "10.0"
        ]
    ) as psu:
        unit_eq(psu.current, 10*pq.amp)
        psu.current = 1.0 * pq.amp

def test_hp6632b_current_sense():
    with expected_protocol(
        ik.hp.HP6632b,
        [
            "MEAS:CURR?",
        ] , [
            "10.0"
        ]
    ) as psu:
        unit_eq(psu.current_sense, 10*pq.amp)

def test_hp6632b_overcurrent():
    with expected_protocol(
        ik.hp.HP6632b,
        [
            "CURR:PROT:STAT?",
            "CURR:PROT:STAT 1"
        ] , [
            "0"
        ]
    ) as psu:
        assert psu.overcurrent == False
        psu.overcurrent = True

def test_hp6632b_current_sense_range():
    with expected_protocol(
        ik.hp.HP6632b,
        [
            "SENS:CURR:RANGE?",
            "SENS:CURR:RANGE {:e}".format(1)
        ] , [
            "0.05"
        ]
    ) as psu:
        unit_eq(psu.current_sense_range, 0.05*pq.amp)
        psu.current_sense_range = 1 * pq.amp

def test_hp6632b_output_dfi_source():
    with expected_protocol(
        ik.hp.HP6632b,
        [
            "OUTP:DFI:SOUR?",
            "OUTP:DFI:SOUR QUES"
        ] , [
            "OPER"
        ]
    ) as psu:
        assert psu.output_dfi_source == psu.DFISource.operation
        psu.output_dfi_source = psu.DFISource.questionable

def test_hp6632b_output_remote_inhibit():
    with expected_protocol(
        ik.hp.HP6632b,
        [
            "OUTP:RI:MODE?",
            "OUTP:RI:MODE LATC"
        ] , [
            "LIVE"
        ]
    ) as psu:
        assert psu.output_remote_inhibit == psu.RemoteInhibit.live
        psu.output_remote_inhibit = psu.RemoteInhibit.latching

def test_hp6632b_digital_function():
    with expected_protocol(
        ik.hp.HP6632b,
        [
            "DIG:FUNC?",
            "DIG:FUNC DIG"
        ] , [
            "RIDF"
        ]
    ) as psu:
        assert psu.digital_function == psu.DigitalFunction.remote_inhibit
        psu.digital_function = psu.DigitalFunction.data

def test_hp6632b_digital_data():
    with expected_protocol(
        ik.hp.HP6632b,
        [
            "DIG:DATA?",
            "DIG:DATA 1"
        ] , [
            "5"
        ]
    ) as psu:
        assert psu.digital_data == 5
        psu.digital_data = 1

def test_hp6632b_sense_sweep_points():
    with expected_protocol(
        ik.hp.HP6632b,
        [
            "SENS:SWE:POIN?",
            "SENS:SWE:POIN {:e}".format(2048)
        ] , [
            "5"
        ]
    ) as psu:
        assert psu.sense_sweep_points == 5
        psu.sense_sweep_points = 2048

def test_hp6632b_sense_sweep_interval():
    with expected_protocol(
        ik.hp.HP6632b,
        [
            "SENS:SWE:TINT?",
            "SENS:SWE:TINT {:e}".format(1e-05)
        ] , [
            "1.56e-05"
        ]
    ) as psu:
        unit_eq(psu.sense_sweep_interval, 1.56e-05 * pq.second)
        psu.sense_sweep_interval = 1e-05 * pq.second

def test_hp6632b_sense_window():
    with expected_protocol(
        ik.hp.HP6632b,
        [
            "SENS:WIND?",
            "SENS:WIND RECT"
        ] , [
            "HANN"
        ]
    ) as psu:
        assert psu.sense_window == psu.SenseWindow.hanning
        psu.sense_window = psu.SenseWindow.rectangular

def test_hp6632b_output_protection_delay():
    with expected_protocol(
        ik.hp.HP6632b,
        [
            "OUTP:PROT:DEL?",
            "OUTP:PROT:DEL {:e}".format(5e-02)
        ] , [
            "8e-02"
        ]
    ) as psu:
        unit_eq(psu.output_protection_delay, 8e-02 * pq.second)
        psu.output_protection_delay = 5e-02 * pq.second

def test_hp6632b_voltage_alc_bandwidth():
    with expected_protocol(
        ik.hp.HP6632b,
        [
            "VOLT:ALC:BAND?",
        ] , [
            "6e4"
        ]
    ) as psu:
        assert psu.voltage_alc_bandwidth == psu.ALCBandwidth.fast

def test_hp6632b_voltage_trigger():
    with expected_protocol(
        ik.hp.HP6632b,
        [
            "VOLT:TRIG?",
            "VOLT:TRIG {:e}".format(1)
        ] , [
            "1e+0"
        ]
    ) as psu:
        unit_eq(psu.voltage_trigger, 1 * pq.volt)
        psu.voltage_trigger = 1 * pq.volt

def test_hp6632b_current_trigger():
    with expected_protocol(
        ik.hp.HP6632b,
        [
            "CURR:TRIG?",
            "CURR:TRIG {:e}".format(0.1)
        ] , [
            "1e-01"
        ]
    ) as psu:
        unit_eq(psu.current_trigger, 0.1 * pq.amp)
        psu.current_trigger = 0.1 * pq.amp

def test_hp6632b_init_output_trigger():
    with expected_protocol(
        ik.hp.HP6632b,
        [
            "INIT:NAME TRAN",
        ] , [
            ""
        ]
    ) as psu:
        psu.init_output_trigger()

def test_hp6632b_check_error_queue():
    with expected_protocol(
        ik.hp.HP6632b,
        [
            "SYST:ERR?",
            "SYST:ERR?",
        ] , [
            '-222,"Data out of range"',
            '+0,"No error"'
        ]
    ) as psu:
        err_queue = psu.check_error_queue()
        assert err_queue == [
                                psu.ErrorCodes.data_out_of_range
                            ], "got {}".format(err_queue)


## HP3456a TESTING ##                            

def test_hp3456a_trigger_mode():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
            "T4",
        ] , [
            ""
        ],
        sep = "\r"
    ) as dmm:
        dmm.trigger_mode = dmm.TriggerMode.hold

def test_hp3456a_number_of_digits():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
            "W6STG",
            "REG"
        ] , [
            "+06.00000E+0"
        ],
        sep = "\r"
    ) as dmm:
        dmm.number_of_digits = 6
        assert dmm.number_of_digits == 6
        
def test_hp3456a_auto_range():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
            "R1W",
        ] , [
            ""
        ],
        sep = "\r"
    ) as dmm:
        dmm.auto_range()
        
def test_hp3456a_number_of_readings():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
            "W10STN",
            "REN"
        ] , [
            "+10.00000E+0"
        ],
        sep = "\r"
    ) as dmm:
        dmm.number_of_readings = 10
        assert dmm.number_of_readings == 10
        
def test_hp3456a_nplc():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
            "W1STI",
            "REI"
        ] , [
            "+1.00000E+0"
        ],
        sep = "\r"
    ) as dmm:
        dmm.nplc = 1
        assert dmm.nplc == 1
        
def test_hp3456a_mode():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
            "S0F4",
        ] , [
            ""
        ],
        sep = "\r"
    ) as dmm:
        dmm.mode = dmm.Mode.resistance_2wire
        
def test_hp3456a_math_mode():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
            "M2",
        ] , [
            ""
        ],
        sep = "\r"
    ) as dmm:
        dmm.math_mode = dmm.MathMode.statistic
        
def test_hp3456a_trigger():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
            "T3",
        ] , [
            ""
        ],
        sep = "\r"
    ) as dmm:
        dmm.trigger()
        
def test_hp3456a_fetch():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
        ] , [
            "+000.1055E+0,+000.1043E+0,+000.1005E+0,+000.1014E+0"
        ],
        sep = "\r"
    ) as dmm:
        v = dmm.fetch(dmm.Mode.resistance_2wire)
        np.testing.assert_array_equal(v, [0.1055,0.1043,0.1005,0.1014] * pq.ohm)
        
def test_hp3456a_variance():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
            "REV",
        ] , [
            "+04.93111E-6"
        ],
        sep = "\r"
    ) as dmm:
        assert dmm.variance == +04.93111E-6
        
def test_hp3456a_count():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
            "REC",
        ] , [
            "+10.00000E+0"
        ],
        sep = "\r"
    ) as dmm:
        assert dmm.count == +10
        
def test_hp3456a_mean():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
            "REM",
        ] , [
            "+102.1000E-3"
        ],
        sep = "\r"
    ) as dmm:
        assert dmm.mean == +102.1000E-3
        
def test_hp3456a_delay():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
            "RED",
        ] , [
            "-000.0000E+0"
        ],
        sep = "\r"
    ) as dmm:
        assert dmm.delay == 0
        
def test_hp3456a_lower():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
            "REL",
        ] , [
            "+099.3000E-3"
        ],
        sep = "\r"
    ) as dmm:
        assert dmm.lower == +099.3000E-3
        
def test_hp3456a_upper():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
            "REU",
        ] , [
            "+105.5000E-3"
        ],
        sep = "\r"
    ) as dmm:
        assert dmm.upper == +105.5000E-3
        
def test_hp3456a_ryz():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
            "RER",
            "REY",
            "REZ"
        ] , [
            "+0600.000E+0",
            "+1.000000E+0",
            "+105.5000E-3"
        ],
        sep = "\r"
    ) as dmm:
        assert dmm.r == +0600.000E+0
        assert dmm.y == +1.000000E+0
        assert dmm.z == +105.5000E-3
        
def test_hp3456a_measure():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
            "S1F1W1STNT3",
            "S0F4W1STNT3",
            "S0F1W1STNT3"
        ] , [
            "+00.00000E-3",
            "+000.1010E+0",
            "+000.0002E-3"
        ],
        sep = "\r"
    ) as dmm:
        assert dmm.measure(dmm.Mode.ratio_dcv_dcv) == 0
        assert dmm.measure(dmm.Mode.resistance_2wire) == +000.1010E+0 * pq.ohm
        assert dmm.measure(dmm.Mode.dcv) == +000.0002E-3 * pq.volt

def test_hp3456a_input_range():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
            "R2W",
        ] , [
            ""
        ],
        sep = "\r"
    ) as dmm:
        dmm.input_range = 10 ** -1 * pq.volt
        
def test_hp3456a_relative():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
            "M0",
            "M3",
        ] , [
            "",
        ],
        sep = "\r"
    ) as dmm:
        dmm.relative = False
        dmm.relative = True

def test_hp3456a_auto_zero():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
            "Z0",
            "Z1",
        ] , [
            "",
        ],
        sep = "\r"
    ) as dmm:
        dmm.autozero = False
        dmm.autozero = True
        
def test_hp3456a_filter():
    with expected_protocol(
        ik.hp.HP3456a,
        [
            "HO0T4SO1",
            "FL0",
            "FL1",
        ] , [
            "",
        ],
        sep = "\r"
    ) as dmm:
        dmm.filter = False
        dmm.filter = True

