#!/usr/bin/python
# Filename: tektds224.py

# Original author: Steven Casagrande (stevencasagrande@gmail.com)
# 2012

# This work is released under the Creative Commons Attribution-Sharealike 3.0 license.
# See http://creativecommons.org/licenses/by-sa/3.0/ or the included license/LICENSE.TXT file for more information.

# Attribution requirements can be found in license/ATTRIBUTION.TXT

from instrument.instrument import Instrument
from numpy import *
import struct

class Tektds224(Instrument):
	def __init__(self, port, address,timeout_length):
		Instrument.__init__(self,port,address,timeout_length)
	
	# Coupling	
	def coupling(self, channel, setting):
		'''
		Set input coupling of specified channel.
		
		channel: Input channel which will have the input coupling changed.
		channel = {1|2|3|4|CH1|CH2|CH3|CH4},integer/string
		'''
		if type(channel) == type(str()):
			channel = channel.lower()
			if channel in ['1','2','3','4']:
				channel = int(channel)
			elif channel in ['ch1','ch2','ch3','ch4']:
				channel = ['ch1','ch2','ch3','ch4'].index(channel) + 1
			else:
				raise Exception('Only "CH1", "CH2", "CH3", and "CH4" are valid channels to have the input coupling changed.')
		elif type(channel) == type(int()) and channel not in [1,2,3,4]:
			raise Exception('Channel must be 1, 2, 3, or 4 when specified as an integer.')
		else:
			raise Exception('Channel must be specified as an integer or string when changing the coupling.')
		
		if( setting.upper() in ['AC','DC','GND'] ):
			self.write( 'CH' + str(channel) + ':COUPL ' + setting.upper() )
		else:
			raise Exception('Error: Only AC, DC, and GND are valid coupling settings.')
	
	# Read Waveform		
	def readWaveform(self, channel, format):
		'''
		Read waveform from the oscilloscope.
		This function is all inclusive. After reading the data from the oscilloscope, it unpacks the data and scales it accordingly.
		Supports both ASCII and binary waveform transfer. For 2500 data points, with a width of 2 bytes, transfer takes approx 2 seconds for binary, and 7 seconds for ASCII.
		
		Function returns a list [x,y], where both x and y are numpy arrays.
		
		channel: Channel which will have its waveform transfered.
		channel = {CH1|CH2|CH3|CH4},string
		
		format: Data transfer format. Either ASCII or binary.
		format = {ASCII,BINARY},string
		'''
		validChannel = ['CH1', 'CH2', 'CH3', 'CH4', 'REFA', 'REFB', 'REFC', 'REFD', 'MATH']
		if( channel.upper() not in validChannel ):
			print 'Error: Only the following channels are supported: "CH1", "CH2", "CH3", "CH4", "REFA", "REFB", "REFC", "REFD", "MATH".'
			return 0
		
		validFormat = ['ASCII','BINARY']
		if( format.upper() not in validFormat ):
			print 'Error: Only "ASCII" and "BINARY" are valid data formats'
			return 0
		
		self.write( 'DAT:SOU ' + channel.upper() ) # Set the acquisition channel
		
		if( format.upper() == 'ASCII' ):
			self.write( 'DAT:ENC ASCI' ) # Set the data encoding format to ASCII
			raw = self.query( 'CURVE?' )
			raw = raw.split(",") # Break up comma delimited string
			raw = map(float,raw) # Convert each list element to int
			raw = array(raw) # Convert into numpy array
		elif( format.upper() == 'BINARY' ):
			self.write( 'DAT:ENC RIB' ) # Set encoding to signed, big-endian
			self.write( 'CURVE?' )
			raw = self.binblockread(2) # Read in the binary block, data width of 2 bytes

			self.ser.read(2) # Read in the two ending \n\r characters
		
		yoffs = self.query( 'WFMP:' + channel.upper() + ':YOF?' ) # Retrieve Y offset
		ymult = self.query( 'WFMP:' + channel.upper() + ':YMU?' ) # Retrieve Y multiplier
		yzero = self.query( 'WFMP:' + channel.upper() + ':YZE?' ) # Retrieve Y zero
		
		y = ( (raw - float(yoffs) ) * float(ymult) ) + float(yzero)
		
		xzero = self.query( 'WFMP:XZE?' ) # Retrieve X zero
		xincr = self.query( 'WFMP:XIN?' ) # Retrieve X incr
		ptcnt = self.query( 'WFMP:' + channel.upper() + ':NR_P?' ) # Retrieve number of data points
		
		x = arange( float(ptcnt) ) * float(xincr) + float(xzero)
		
		return [x,y]
		
