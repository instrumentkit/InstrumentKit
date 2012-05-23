#!/usr/bin/python
# Filename: keithley6220.py

# Original author: Steven Casagrande (stevencasagrande@gmail.com)
# 2012

# This work is released under the Creative Commons Attribution-Sharealike 3.0 license.
# See http://creativecommons.org/licenses/by-sa/3.0/ or the included license/LICENSE.TXT file for more information.

# Attribution requirements can be found in license/ATTRIBUTION.TXT

from instrument.instrument import Instrument

class Keithley6220(Instrument):
    def __init__(self, port, address,timeout_length):
        Instrument.__init__(self,port,address,timeout_length)
    
    def output(self,current):
    	
    	if not isinstance(current,float):
    		raise Exception('Current must be specified as a float.')
    		
    	if (current < -105e-3) or (current > 105e3):
    		raise Exception('Current must be betwen -105e-3 and 105e+3')
    		
    	self.write( 'SOUR:CURR ' + str(current) )
    	
    def disable(self):
    	self.write('SOUR:CLE:IMM') # Set output to zero and then turn the output off
