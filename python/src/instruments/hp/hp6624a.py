#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# hp6624a.py: Python class for the HP 6624a power supply
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

import quantities as pq

from instruments.abstract_instruments import Instrument
from instruments.util_fns import assume_units, ProxyList

## CLASSES #####################################################################

class _HP6624aChannel(object):
    '''
    Class representing a power output channel on the HP6624a.
    
    .. warning:: This class should NOT be manually created by the user. It is 
        designed to be initialized by the `HP6624a` class.
    '''
    
    def __init__(self, hp, idx):
        self._hp = hp
        self._idx = idx + 1
        
    ## PROPERTIES ##
        
    @property
    def voltage(self):
        '''
        Gets/sets the voltage of the specified channel.
        
        Note there is no bounds checking on the value specified.
        
        :units: As specified, or assumed to be :math:`\\text{V}` otherwise.
        :type: `float` or `~quantities.Quantity`
        '''
        return pq.Quantity(float(self._hp.query(
                        'VSET? {}'.format(self._idx)).strip()[:-1]), pq.volt)
    @voltage.setter
    def voltage(self, newval):
        self._hp.sendcmd('VSET {},{}'.format(
            self._idx,
            assume_units(newval, pq.volt).rescale(pq.volt).magnitude,
            ))
            
    @property
    def current(self):
        '''
        Gets/sets the current of the specified channel.
        
        Note there is no bounds checking on the value specified.
        
        :units: As specified, or assumed to be :math:`\\text{A}` otherwise.
        :type: `float` or `~quantities.Quantity`
        '''
        return pq.Quantity(float(self._hp.query(
                        'ISET? {}'.format(self._idx)).strip()[:-1]), pq.amp)
    @current.setter
    def current(self, newval):
        self._hp.sendcmd('ISET {},{}'.format(
            self._idx,
            assume_units(newval, pq.amp).rescale(pq.amp).magnitude
            ))
        
    @property
    def overvoltage(self):
        '''
        Gets/sets the overvoltage protection setting for the specified channel.
        
        Note there is no bounds checking on the value specified.
        
        :units: As specified, or assumed to be :math:`\\text{V}` otherwise.
        :type: `float` or `~quantities.Quantity`
        '''    
        return pq.Quantity(float(self._hp.query(
                        'OVSET? {}'.format(self._idx)).strip()[:-1]), pq.volt)
    @overvoltage.setter
    def overvoltage(self, newval):
        self._hp.sendcmd('OVSET {},{}'.format(
            self._idx,
            assume_units(newval, pq.volt).rescale(pq.volt).magnitude
            ))
        
    @property
    def overcurrent(self):
        '''
        Gets/sets the overcurrent protection setting for the specified channel.
        
        This is a toggle setting. It is either on or off.
        
        :type: `bool`
        '''
        return (True if self._hp.query('OVP? {}'.format(self._idx)).strip()[:-1]
                is '1' else False)
    @overcurrent.setter
    def overcurrent(self, newval):
        if (newval is True) or (newval is 1):
            newval = 1
        else:
            newval = 0
        self._hp.sendcmd('OVP {},{}'.format(self._idx, newval))
    
    @property
    def output(self):
        '''
        Gets/sets the outputting status of the specified channel.
        
        This is a toggle setting. True will turn on the channel output 
        while False will turn it off.
        
        :type: `bool` 
        '''
        return (True if self._hp.query('OUT? {}'.format(self._idx)).strip()[:-1]
                is '1' else False)
    @output.setter
    def output(self, newval):
        if (newval is True) or (newval is 1):
            newval = 1
        else:
            newval = 0
        self._hp.sendcmd('OUT {},{}'.format(self._idx, newval))
    
    
    ## METHODS ##
    
    def reset(self):
        '''
        Reset overvoltage and overcurrent errors to resume operation.
        '''
        self._hp.sendcmd('OVRST {}'.format(self._idx))
        self._hp.sendcmd('OCRST {}'.format(self._idx))

    
class HP6624a(Instrument):  
    '''
    The HP6624a is a multi-output power supply. 
    
    This class can also be used for HP662xa, where x=1,2,3,4,7. Note that some 
    models have less channels then the HP6624 and it is up to the user to take 
    this into account.
    
    Example usage:
    
    >>> import instruments as ik
    >>> psu = ik.hp.HP6624a.open_gpibusb('/dev/ttyUSB0', 1)
    >>> psu.channel[0].voltage = 10 # Sets channel 1 voltage to 10V.
    '''  
    
    ## PROPERTIES ##
    
    @property
    def channel(self):
        '''
        Gets a specific channel object. The desired channel is specified like 
        one would access a list.
        
        :rtype: `_HP6624aChannel`
        
        .. seealso::
            `HP6624a` for example using this property.
        '''
        return ProxyList(self, _HP6624aChannel, xrange(4))
    
    ## METHODS ##
        
    def clear(self):
        '''
        Taken from the manual:
        
        Return the power supply to its power-on state and all parameters are
        returned to their initial power-on values except the following:
        
        #) The store/recall registers are not cleared.
        #) The power supply remains addressed to listen.
        #) The PON bit in the serial poll register is cleared.
        '''
        self.sendcmd('CLR')
        
        
        
        
        
        
        
        
        
        
