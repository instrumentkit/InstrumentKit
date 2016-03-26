#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing custom units used by various instruments.
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division

from quantities import Hz, milli, UnitQuantity
from quantities.unitquantity import IrreducibleUnit

# UNITS #######################################################################

# IRREDUCIBLE UNITS #


class UnitLogPower(IrreducibleUnit):
    """
    Base unit class for log-power units. The primary example of this
    is `dBm`.
    """
    _primary_order = 80  # Something large smaller than 99.

# SPECIFIC UNITS #

# Define basic unit of log-power, the dBm.

#: Decibel-milliwatts, a basic unit of logarithmic power.
dBm = UnitLogPower('decibel-milliwatt', symbol='dBm')

# The Phase Matrix signal generators communicate in units of millihertz (mHz)
# and centibel-milliwatts (cBm). We define those units here to make conversions
# easier later on.

# TODO: move custom units out to another module.

mHz = UnitQuantity(
    'millihertz',
    milli * Hz,
    symbol='mHz',
    doc="""
    `~quantities.UnitQuantity` representing millihertz, the native unit of the
    Phase Matrix FSW-0020.
    """
)

#: Centibel-milliwatts, the native log-power unit supported by the
#: Phase Matrix FSW-0020.
cBm = UnitLogPower('centibel-milliwatt', dBm / 10, symbol='cBm')
