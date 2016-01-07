#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# agilent33220a.py: Driver for the Agilent 33220a function generator.
##
# © 2013 Steven Casagrande (scasagrande@galvant.ca).
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

## FEATURES ####################################################################

from __future__ import division

## IMPORTS #####################################################################

from flufl.enum import Enum
from flufl.enum._enum import EnumValue

import quantities as pq

from instruments.generic_scpi import SCPIFunctionGenerator
from instruments.util_fns import (
    enum_property, int_property, bool_property, unitful_property, assume_units
)


## CLASSES #####################################################################

class Agilent33220a(SCPIFunctionGenerator):

    def __init__(self, filelike):
        super(Agilent33220a, self).__init__(filelike)
        
    ## ENUMS ##
    
    class Function(Enum):
        sinusoid = "SIN"
        square = "SQU"
        ramp = "RAMP"
        pulse = "PULS"
        noise = "NOIS"
        dc = "DC"
        user = "USER"
        
    class LoadResistance(Enum):
        minimum = "MIN"
        maximum = "MAX"
        high_impedance = "INF"
        
    class OutputPolarity(Enum):
        normal = "NORM"
        inverted = "INV"
        
    ## PROPERTIES ##
    
    function = enum_property(
        name="FUNC",
        enum=Function,
        doc="""
        Gets/sets the output function of the function generator
        
        :type: `Agilent33220a.Function`
        """,
        set_fmt="{}:{}"
    )
    
    duty_cycle = int_property(
        name="FUNC:SQU:DCYC",
        doc="""
        Gets/sets the duty cycle of a square wave.
        
        Duty cycle represents the amount of time that the square wave is at a 
        high level.
        
        :type: `int`
        """,
        valid_set=xrange(101)
    )
    
    ramp_symmetry = int_property(
        name="FUNC:RAMP:SYMM",
        doc="""
        Gets/sets the ramp symmetry for ramp waves.
        
        Symmetry represents the amount of time per cycle that the ramp wave is 
        rising (unless polarity is inverted).
        
        :type: `int`
        """,
        valid_set=xrange(101)
    )
    
    output = bool_property(
        name="OUTP",
        inst_true="ON",
        inst_false="OFF",
        doc="""
        Gets/sets the output enable status of the front panel output connector.
        
        The value `True` corresponds to the output being on, while `False` is
        the output being off.
        
        :type: `bool`
        """
    )
    
    output_sync = bool_property(
        name="OUTP:SYNC",
        inst_true="ON",
        inst_false="OFF",
        doc="""
        Gets/sets the enabled status of the front panel sync connector.
        
        :type: `bool`
        """ 
    )
    
    output_polarity = enum_property(
        name="OUTP:POL",
        enum=OutputPolarity,
        doc="""
        Gets/sets the polarity of the waveform relative to the offset voltage.
        
        :type: `~Agilent33220a.OutputPolarity`
        """
    )
    
    @property
    def load_resistance(self):
        """
        Gets/sets the desired output termination load (ie, the impedance of the 
        load attached to the front panel output connector).
        
        The instrument has a fixed series output impedance of 50ohms. This 
        function allows the instrument to compensate of the voltage divider 
        and accurately report the voltage across the attached load.
        
        :units: As specified (if a `~quantities.quantity.Quantity`) or assumed
            to be of units :math:`\\Omega` (ohm).
        :type: `~quantities.quantity.Quantity` or `Agilent33220a.LoadResistance`
        """
        value = self.query("OUTP:LOAD?")
        try:
            return int(value) * pq.ohm
        except:
            return self.LoadResistance[value.strip()]
    @load_resistance.setter
    def load_resistance(self, newval):
        if (not isinstance(newval, EnumValue)) or (newval.enum is not 
                                                        self.LoadResistance):
            newval = newval.value
        elif isinstance(newval, int):
            if (newval < 0) or (newval > 10000):
                raise ValueError("Load resistance must be between 0 and 10,000")
            newval = assume_units(newval, pq.ohm).rescale(pq.ohm).magnitude
        else:
            raise TypeError("Not a valid load resistance type.")
        self.sendcmd("OUTP:LOAD {}".format(newval))

