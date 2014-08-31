#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# __init__.py: Tests for generic SCPI instruments.
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

import instruments as ik
from instruments.tests import expected_protocol, make_name_test, unit_eq

import cStringIO as StringIO
import quantities as pq
import numpy as np

## TESTS ######################################################################

test_scpi_multimeter_name = make_name_test(ik.generic_scpi.SCPIMultimeter)
    
def test_scpi_multimeter_mode():
    with expected_protocol(
        ik.generic_scpi.SCPIMultimeter,
        [
            "CONF?",
            "CONF:CURR:AC"
        ] , [
            "FRES +1.000000E+01,+3.000000E-06"
        ]
    ) as dmm:
        assert dmm.mode == dmm.Mode.fourpt_resistance
        dmm.mode = dmm.Mode.current_ac

def test_scpi_multimeter_trigger_mode():
    with expected_protocol(
        ik.generic_scpi.SCPIMultimeter,
        [
            "TRIG:SOUR?",
            "TRIG:SOUR EXT"
        ] , [
            "BUS"
        ]
    ) as dmm:
        assert dmm.trigger_mode == dmm.TriggerMode.bus
        dmm.trigger_mode = dmm.TriggerMode.external

def test_scpi_multimeter_input_range():
    with expected_protocol(
        ik.generic_scpi.SCPIMultimeter,
        [
            "CONF?", #1
            "CONF?", #2
            "CONF?", #3.1
            "CONF:FRES MIN", #3.2
            "CONF?", #4.1
            "CONF:CURR:DC 1.0" #4.2
        ] , [
            "CURR:AC +1.000000E+01,+3.000000E-06",  #1
            "CURR:AC AUTO,+3.000000E-06",           #2
            "FRES +1.000000E+01,+3.000000E-06",     #3
            "CURR:DC +1.000000E+01,+3.000000E-06"   #4
        ]
    ) as dmm:
        assert dmm.input_range == 1e1 * pq.amp
        assert dmm.input_range == dmm.InputRange.automatic
        dmm.input_range = dmm.InputRange.minimum
        dmm.input_range = 1 * pq.amp
        
def test_scpi_multimeter_resolution():
    with expected_protocol(
        ik.generic_scpi.SCPIMultimeter,
        [
            "CONF?", #1
            "CONF?", #2
            "CONF?", #3.1
            "CONF:FRES +1.000000E+01,MIN", #3.2
            "CONF?", #4.1
            "CONF:CURR:DC +1.000000E+01,3e-06" #4.2
        ] , [
            "VOLT +1.000000E+01,+3.000000E-06",     #1
            "VOLT +1.000000E+01,MAX",           #2
            "FRES +1.000000E+01,+3.000000E-06",     #3
            "CURR:DC +1.000000E+01,+3.000000E-06"   #4
        ]
    ) as dmm:
        assert dmm.resolution == 3e-06
        assert dmm.resolution == dmm.Resolution.maximum
        dmm.resolution = dmm.Resolution.minimum
        dmm.resolution = 3e-06

