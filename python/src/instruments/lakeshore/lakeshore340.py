#!/usr/bin/python
# Filename: lakeshore340.py

# Original author: Steven Casagrande (stevencasagrande@gmail.com)
# 2012

# This work is released under the Creative Commons Attribution-Sharealike 3.0 license.
# See http://creativecommons.org/licenses/by-sa/3.0/ or the included license/LICENSE.TXT file for more information.

# Attribution requirements can be found in license/ATTRIBUTION.TXT

from instruments.abstract_instruments import Instrument

class Lakeshore340(Instrument):
    def __init__(self, port, address,timeout_length):
        super(Lakeshore340, self).__init__(self,port,address,timeout_length)
        
    def temperature(self,sensor):
        '''
        
        '''
        if not isinstance(sensor,str):
            raise Exception('Sensor must be specified as a string.')
        return float(self.query('KRDG?' + sensor))
