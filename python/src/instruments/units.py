#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# units.py: Custom units used by various instruments.
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

## IMPORTS #####################################################################

from quantities import Hz, milli, GHz, UnitQuantity, Quantity
from quantities.unitquantity import IrreducibleUnit

## UNITS #######################################################################

## IRREDUCIBLE UNITS ##

class UnitLogPower(IrreducibleUnit):
    _primary_order = 80 # Something large smaller than 99.

## SPECIFIC UNITS ##

# Define basic unit of log-power, the dBm.

#: Decibel-milliwatts, a basic unit of logarithmic power.
dBm = UnitLogPower('decibel-milliwatt', symbol='dBm')

# The Phase Matrix signal generators communicate in units of millihertz (mHz)
# and centibel-milliwatts (cBm). We define those units here to make conversions
# easier later on.

# TODO: move custom units out to another module.

mHz = UnitQuantity('millihertz', milli * Hz, symbol='mHz', doc="""
`~quantities.UnitQuantity` representing millihertz, the native unit of the
Phase Matrix FSW-0020.
""")

#: Centibel-milliwatts, the native log-power unit supported by the
#: Phase Matrix FSW-0020.
cBm = UnitLogPower('centibel-milliwatt', dBm / 10, symbol='cBm')

