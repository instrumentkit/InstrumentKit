#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# __init__.py: "Native SPI" driver for Phase Matrix signal
#     generators.
##
# Authors: Christopher Granade (cgranade@cgranade.com) and
#     Troy Borneman.
##

## FEATURES ####################################################################

from __future__ import division

## IMPORTS #####################################################################

from instruments.abstract_instruments import Instrument
from instruments.util_fns import assume_units
from quantities import Hz, milli, GHz, UnitQuantity, Quantity
from quantities.unitquantity import IrreducibleUnit
 
## UNITS #######################################################################
# The Phase Matrix signal generators communicate in units of millihertz (mHz)
# and centibel-milliwatts (cBm). We define those units here to make conversions
# easier later on.

# TODO: move custom units out to another module.
mHz = UnitQuantity('millihertz', milli * Hz, symbol='mHz', doc="""
`~quantities.UnitQuantity` representing millihertz, the native unit of the
Phase Matrix FSW-0020.
""")

class UnitLogPower(IrreducibleUnit):
    _primary_order = 80 # Something large smaller than 99.

#: Decibel-milliwatts, a basic unit of logarithmic power.
dBm = UnitLogPower('decibel-milliwatt', symbol='dBm')
#: Centibel-milliwatts, the native log-power unit supported by the
#: Phase Matrix FSW-0020.
cBm = UnitLogPower('centibel-milliwatt', dBm / 10, symbol='cBm')

## CLASSES #####################################################################

class PhaseMatrixFSW0020(Instrument):
    """
    Communicates with a Phase Matrix FSW-0020 signal generator via the
    "Native SPI" protocol, supported on all FSW firmware versions.
    """
        
    def reset(self):
        r"""
        Causes the connected signal generator to perform a hardware reset.
        Note that no commands will be accepted by the generator for at least
        :math:`5 \mu\text{s}`.
        """
        self.sendcmd('0E.')
    
    @property
    def freq(self):
        """
        Gets/sets the output frequency of the signal generator.
        If units are not specified, the frequency is assumed
        to be in gigahertz (GHz).
        
        :type: `~quantities.Quantity` or `float`
        :units: frequency, assumed to be GHz
        """
        return (int(self.query('04.'), 16) * mHz).rescale(GHz)
        
    @freq.setter
    def freq(self, newval):
        # Rescale the input to millihertz as demanded by the signal
        # generator, then convert to an integer.
        newval = int(assume_units(newval, GHz).rescale(mHz).magnitude)

        # Write the integer to the serial port in ASCII-encoded
        # uppercase-hexadecimal format, with padding to 12 nybbles.
        self.sendcmd('0C{:012X}.'.format(newval))
        
        # No return data, so no readline needed.

    @property
    def power(self):
        """
        Gets/sets the output power of the signal generator.
        If units are not specified, the power is assumed to be in
        decibel-milliwatts (dBm).
        
        :type: `~quantities.Quantity` or `float`
        :units: log-power, assumed to be dBm
        """
        return (int(self.query('0D.'), 16) * cBm).rescale(dBm)

    @power.setter
    def power(self, newval):
        # TODO: convert UnitPower Quantity instances to UnitLogPower.
        #       That is, convert [W] to [dBm].

        # The Phase Matrix unit speaks in units of centibel-milliwats,
        # so convert and take the integer part.
        newval = int(assume_units(newval, dBm).rescale(cBm).magnitude)

        # Command code 0x03, parameter length 2 bytes (4 nybbles)
        self.sendcmd('03{:04X}.'.format(newval))

    @property
    def blanking(self):
        """
        :type: `bool`
        """
        # TODO
        pass

    @blanking.setter
    def blanking(self, newval):
        self.sendcmd('05{:02X}.'.format(1 if newval else 0))

    @property
    def ref_output(self):
        """
        :type: `bool`
        """
        # TODO
        pass

    @ref_output.setter
    def ref_output(self, newval):
        self.sendcmd('08{:02X}.'.format(1 if newval else 0))


    @property
    def rf_output(self):
        """
        :type: `bool`
        """
        # TODO
        pass

    @rf_output.setter
    def rf_output(self, newval):
        self.sendcmd('0F{:02X}.'.format(1 if newval else 0))


    @property
    def pulse_modulation(self):
        """
        :type: `bool`
        """
        # TODO
        pass

    @pulse_modulation.setter
    def pulse_modulation(self, newval):
        self.sendcmd('09{:02X}.'.format(1 if newval else 0))

    @property
    def am_modulation(self):
        """
        :type: `bool`
        """
        # TODO
        pass

    @am_modulation.setter
    def am_modulation(self, newval):
        self.sendcmd('0A{:02X}.'.format(1 if newval else 0))
    
