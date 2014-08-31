#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# agilent34410a.py: Implementation of Agilent 34410A-specific functionality.
##
# © 2013-2014 Steven Casagrande (scasagrande@galvant.ca).
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

from flufl.enum import Enum

from instruments.generic_scpi import SCPIMultimeter

## CLASSES #####################################################################

class Agilent34410a(SCPIMultimeter):
    """
    The Agilent 34410a is a very popular 6.5 digit DMM. This class should also
    cover the Agilent 34401a, 34411a, as well as the backwards compatability
    mode in the newer Agilent/Keysight 34460a/34461a. You can find the full 
    specifications for these instruments on the `Keysight website`_.
    
    Example usage:
    
    >>> import instruments as ik
    >>> import quantities as pq
    >>> dmm = ik.agilent.Agilent34410a.open_gpib('/dev/ttyUSB0', 1)
    >>> print dmm.measure(dmm.Mode.resistance)
    
    .. _Keysight website: http://www.keysight.com/
    """

    def __init__(self, filelike):
        super(Agilent34410a, self).__init__(filelike)

    ## PROPERTIES ##
    
    @property
    def data_point_count(self):
        '''
        Gets the total number of readings that are located in reading memory 
        (RGD_STORE).
        
        :rtype: `int`
        '''
        return int(self.query('DATA:POIN?'))
    
    
    ## STATE MANAGEMENT METHODS ##

    def init(self):
        '''
        Switch device from "idle" state to "wait-for-trigger state".
        Measurements will begin when specified triggering conditions are met, 
        following the receipt of the INIT command.
        
        Note that this command will also clear the previous set of readings 
        from memory.
        '''
        self.sendcmd('INIT')
    
    def abort(self):
        '''
        Abort all measurements currently in progress.
        '''
        self.sendcmd('ABOR')
    
    ## MEMORY MANAGEMENT METHODS ##

    def clear_memory(self):
        '''
        Clears the non-volatile memory of the Agilent 34410a.
        '''
        self.sendcmd('DATA:DEL NVMEM')
    
    def r(self, count):
        '''
        Have the multimeter perform a specified number of measurements and then 
        transfer them using a binary transfer method. Data will be cleared from 
        instrument memory after transfer is complete.
        
        :param int count: Number of samples to take.
        
        :rtype: numpy.array
        '''
        if not isinstance(count, int):
            raise TypeError('Parameter "count" must be an integer')
        if count == 0:
            msg = 'R?'
        else:
            msg = 'R? ' + str(count)
        
        self.sendcmd('FORM:DATA REAL,32')
        self.sendcmd(msg)
        return self.binblockread(4)
        
    ## DATA READING METHODS ##
    
    def fetch(self):
        '''
        Transfer readings from instrument memory to the output buffer, and 
        thus to the computer.
        If currently taking a reading, the instrument will wait until it is 
        complete before executing this command.
        Readings are NOT erased from memory when using fetch. Use the R? 
        command to read and erase data.
        Note that the data is transfered as ASCII, and thus it is not 
        recommended to transfer a large number of
        data points using this method.
        
        :rtype: `list` of `float` elements
        '''
        return map(float, self.query( 'FETC?' ).split(',') )
    
    def read_data(self, sample_count):
        '''
        Transfer specified number of data points from reading memory 
        (RGD_STORE) to output buffer.
        First data point sent to output buffer is the oldest.
        Data is erased after being sent to output buffer.
        
        :param int sample_count: Number of data points to be transfered to 
            output buffer. If set to -1, all points in memory will be 
            transfered.
        
        :rtype: `list` of `float` elements
        '''
        if not isinstance(sampleCount,int):
            raise TypeError('Parameter "sampleCount" must be an integer.')
        
        if sampleCount == -1:
            sampleCount = self.data_point_count
        
        self.sendcmd('FORM:DATA ASC')
        return map(float, self.query('DATA:REM? '+str(sampleCount)).split(','))
    
    def read_data_NVMEM(self):
        '''
        Returns all readings in non-volatile memory (NVMEM).
        
        :rtype: `list` of `float` elements
        '''
        return map(float, self.query('DATA:DATA? NVMEM').split(','))
    
    # Read the Last Data Point
    def read_last_data(self):
        '''
        Retrieve the last measurement taken. This can be executed at any time, 
        including when the instrument is currently taking measurements.
        If there are no data points available, the value ``9.91000000E+37`` is 
        returned.
        
        :rtype: `float` or `int` (if an error occurs)
        '''
        data = self.query('DATA:LAST?')
        
        if data == '9.91000000E+37':
            return int(data)
        else:
            data = data[0:data.index(' ')] # Remove units
            return float(data)
    
    # Read: Set to "Wait-for-trigger" state, and immediately send result to output
    def read(self):
        '''
        Switch device from "idle" state to "wait-for-trigger" state. 
        Immediately after the trigger conditions are met, the data will be sent 
        to the output buffer of the instrument.
        
        This is similar to calling `~Agilent34410a.init` and then immediately 
        following `~Agilent34410a.fetch`.
        
        :rtype: `float`
        '''
        return float(self.query('READ?'))

