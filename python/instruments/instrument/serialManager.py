#!/usr/bin/python
# Filename: serialManager.py

# Original author: Steven Casagrande (stevencasagrande@gmail.com)
# 2012

# This work is released under the Creative Commons Attribution-Sharealike 3.0 license.
# See http://creativecommons.org/licenses/by-sa/3.0/ or the included license/LICENSE.TXT file for more information.

# Attribution requirements can be found in license/ATTRIBUTION.TXT

#
# This module handles creating the serial objects for the instrument classes.
# This is needed for Windows because only 1 serial object can have an open connection to
# a serial port at a time. This is not needed on Linux, as multiple pyserial connections
# can be open at the same time to the same serial port.
#

import serial

serialObjDict = {}

def newSerialConnection(port):
	if not isinstance(port,str):
		raise Exception('Serial port must be specified as a string.')
	
	if port not in serialObjDict:
		serialObjDict[port] = serial.Serial(port,460800,timeout=30)
	
	return serialObjDict[port]
