#!/usr/bin/python
# Filename: instrument.py

# Original author: Steven Casagrande (stevencasagrande@gmail.com)
# 2012

# This work is released under the Creative Commons Attribution-Sharealike 3.0 license.
# See http://creativecommons.org/licenses/by-sa/3.0/ or the included license/LICENSE.TXT file for more information.

# Attribution requirements can be found in license/ATTRIBUTION.TXT

import serial
import time
from numpy import *
import struct

class Instrument:
	def __init__(self, port, address,timeout_length):
		self.port = port
		self.address = address
		self.timeout = timeout_length
		self.ser = serial.Serial(port,460800,timeout=self.timeout)
		#self.ser.open()
		
	def write(self, msg):
		#print msg
		self.ser.write("+a:" + str(self.address) + "\r")
		time.sleep(0.02)
		self.ser.write(msg + "\r")
		time.sleep(0.02)
	
	def query(self, msg):
		self.write(msg)
		#result = self.ser.readline(self,size=None,eol='\r')
		result = bytearray()
		c = 0
		while c != '\r':
			c = self.ser.read(1)
			result += c
		return bytes(result)
	
	def identify(self):
		return self.query('*IDN?')
		
	def reset(self):
		self.write('*RST')
	
	def clear(self):
		self.write('*CLS')
	
	def selfTest(self):
		return self.query('*TST?')
	
	def trigger(self):
		self.write('*TRG')
		
	def change_timeout(self,timeout_length):
		self.timeout = timeout_length
		self.ser.timeout = self.timeout
		
	def binblockread(self,dataWidth):
		if( dataWidth not in [1,2]):
			print 'Error: Data width must be 1 or 2.'
			return 0
		symbol = self.ser.read(1) # This needs to be a # symbol for valid binary block
		if( symbol != '#' ): # Check to make sure block is valid
			print 'Error: Not a valid binary block start. Binary blocks require the first character to be #.'
			return 0
		else:
			digits = int( self.ser.read(1) ) # Read in the num of digits for next part
			num_of_bytes = int( self.ser.read(digits) ) # Read in the num of bytes to be read
			temp = self.ser.read(num_of_bytes) # Read in the data bytes
		
			raw = zeros(num_of_bytes/dataWidth) # Create zero array
			for i in range(0,num_of_bytes/dataWidth):
				raw[i] = struct.unpack(">h", temp[i*dataWidth:i*dataWidth+dataWidth])[0] # Parse binary string into ints
			del temp
		
			return raw
