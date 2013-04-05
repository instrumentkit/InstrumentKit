#!/usr/bin/python
# Filename: oxforditc503.py

# Original author: Steven Casagrande (stevencasagrande@gmail.com)
# 2012

# This work is released under the Creative Commons Attribution-Sharealike 3.0 license.
# See http://creativecommons.org/licenses/by-sa/3.0/ or the included license/LICENSE.TXT file for more information.

# Attribution requirements can be found in license/ATTRIBUTION.TXT

from instrument.instrument import Instrument

class OxfordITC503(Instrument):
    def __init__(self, port, address,timeout_length):
        super(OxfordITC503, self).__init__(self,port,address,timeout_length)
        self.write('C3') # Enable remote commands
        
    def write(self, msg):
        Instrument.write(self, '+eoi:0') # Disable EOI
        Instrument.write(self, '+eos:13') # Set EOS char to CR (ASCII 13)
        Instrument.write(self, msg)
        Instrument.write(self, '+eoi:1') # Enable EOI
    
    # Read Temperature    
    def readTemp(self,probeNum):
        '''
        Read temperature of an attached probe to the Oxford ITC503.
        
        Returns a float containing the temperature of the specified probe in Kelvin.
        
        probeNum: Attached probe number that will be used for reading the temperature.
        probeNum = {1|2|3},integer
        '''
        if( probeNum not in [1,2,3] ):
            raise Exception('Only 1,2,3 are valid probe numbers for Oxford ITC 503')
        
        temp = self.query('R' + probeNum)
        temp = temp[1:len(temp)] # Remove the first character ('R')
        temp = float(temp) # Convert to float
        
        return temp
