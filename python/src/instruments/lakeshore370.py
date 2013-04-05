#!/usr/bin/python
# Filename: lakeshore370.py

# Original author: Steven Casagrande (stevencasagrande@gmail.com)
# 2012

# This work is released under the Creative Commons Attribution-Sharealike 3.0 license.
# See http://creativecommons.org/licenses/by-sa/3.0/ or the included license/LICENSE.TXT file for more information.

# Attribution requirements can be found in license/ATTRIBUTION.TXT

from instrument.instrument import Instrument

class Lakeshore370(Instrument):
    def __init__(self, port, address,timeout_length):
        super(Lakeshore370, self).__init__(self,port,address,timeout_length)
        self.write('IEEE 3,0') # Disable termination characters and enable EOI
    
    def resistance(self,channel):
        if not isinstance(channel,int):
            raise Exception('Channel number must be specified as an integer.')
        
        if (channel < 1) or (channel > 16):
            raise Exception('Channel must be 1-16 (inclusive).')
        
        return float( self.query( 'RDGR? ' + str(channel) ) )
            
            
            
            
            
            
            
        
        
        
        
        
        
        
