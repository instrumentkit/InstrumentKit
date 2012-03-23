#!/usr/bin/python
# Filename: lakeshore475.py

# Original author: Steven Casagrande (stevencasagrande@gmail.com)
# 2012

# This work is released under the Creative Commons Attribution-Sharealike 3.0 license.
# See http://creativecommons.org/licenses/by-sa/3.0/ or the included license/LICENSE.TXT file for more information.

# Attribution requirements can be found in license/ATTRIBUTION.TXT

from instrument.instrument import Instrument

class Lakeshore475(Instrument):
	def __init__(self, port, address,timeout_length):
		Instrument.__init__(self,port,address,timeout_length)

	# Read Field
	def readField(self):
		'''
		Read field from connected probe.
		
		Returns a float. Units are currently selected units on the device. 
		'''
		return float( self.query( 'RDGFIELD?' ) )

	# Chnage Measurement Mode
	def changeMeasurementMode(self,mode,resolution,filterType,peakMode,peakDisp):
		'''
		Change the measurement mode of the Gaussmeter.
		
		mode: The desired measurement mode type
		mode = {DC|RMS|PEAK},string
		
		resolution: Digit resolution of the measured field.
		resolution = {3|4|5},integer
		
		filterType: Specify the signal filter used by the instrument. Available types include wide band, narrow band, and low pass.
		filterType = {WIDE|NARROW|LOW PASS},string
		
		peakMode: Peak measurement mode to be used.
		peakMode = {PERIODIC|PULSE},string
		
		peakDisp: Peak display mode to be used.
		peakDisp = {POSITIVE|NEGATIVE|BOTH},string
		'''
		if type(mode) != type(str()):
			raise Exception('Parameter "mode" must be a string.')
		if type(resolution) != type(int()):
			raise Exception('Parameter "resolution" must be an integer.')
		if type(filterType) != type(str()):
			raise Exception('Parameter "filterType" must be a string.')
		if type(peakMode) != type(str()):
			raise Exception('Parameter "peakMode" must be a string.')
		if type(peakDisp) != type(str()):
			raise Exception('Parameter "peakDisp" must be a string.')
		
		mode = mode.upper()
		filterType = filterType.upper()
		peakMode = peakMode.upper()
		peakDisp = peakDisp.upper()

		# Parse the measurement mode
		valid = ['DC','RMS','PEAK']
		if mode not in valid:
			raise Exception('Only "DC", "RMS", and "PEAK" are valid measurement modes.')
		else:
			mode = valid.index(mode) + 1

		# Parse the resolution
		if resolution in [3,4,5]:
			resolution = resolution - 2
		else:
			raise Exception('Only 3,4,5 are valid resolutions (must be type int).')
		
		# Parse the filter type
		valid = ['WIDE','NARROW','LOW PASS']
		if filterType not in valid:
			raise Exception('Only "WIDE", "NARROW", and "LOW PASS" are valid filter types.')
		else:
			filterType = valid.index(filterType) + 1
		
		# Parse the peak measurement mode
		valid = ['PERIODIC','PULSE']
		if peakMode not in valid:
			raise Exception('Only "PERIODIC" and "PULSE" peak measurement modes are supported.')
		else:
			peakMode = valid.index(peakMode) + 1
			
		# Parse the peak display mode
		valid = ['POSITIVE','NEGATIVE','BOTH']
		if peakDisp not in valid:
			raise Exception('Only "POSITIVE","NEGATIVE", and "BOTH" are supported for display of peak reading.')
		else:
			peakDisp = valid.index(peakDisp) + 1
			
		self.write( 'RDGMODE %s,%s,%s,%s,%s' % (mode,resolution,filterType,peakMode,peakDisp) )
	
	# Query Field Units	
	def queryFieldUnits(self):
		'''
		Function returns the units (as a string) the Gaussmeter is currently set to.
		'''
		unit = int(self.query('UNIT?'))
		return ['Gauss','Tesla','Oersted','Amp/meter'][unit-1]
		
	def setFieldUnits(self,unit):
		'''
		Set the field units of the Gaussmeter.
		
		unit: Desired field unit
		unit = {Gauss|Tesla|Oersted|Amp/meter},string
		'''
		if type(unit) != type(str()):
			raise Exception('Parameter "unit" must be a string.')
		
		unit = unit.lower()
		valid1 = ['gauss','tesla','oersted','amp/meter']
		valid2 = ['g','t','o','a']
		if unit in valid1:
			unit = str( valid1.index(unit) + 1 )
		elif unit in valid2:
			unit = str( valid2.index(unit) + 1 )
		else:
			raise Exception('Only "gauss", "tesla", "oersted", and "amp/meter" are supported units.')
			
		self.write( 'UNIT ' + unit )
	
	# Set Temperature Units		
	def setTempUnits(self,unit):
		'''
		Set the temperature units of the Gaussmeter.
		
		unit: Desired temperature units
		unit = {Celsius,Kelvin},string
		'''
		if type(unit) != type(str()):
			raise Exception('Parameter "unit" must be a string.')
		
		unit = unit.lower()
		valid = ['c','k','celsius','kelvin']
		if unit not in valid:
			raise Exception('Only "c" and "k" are valid temperature units.')
		else:
			unit = valid.index(unit) + 1
			if unit >= 3:
				unit = unit - 2
			
		self.write( 'TUNIT ' + str(unit) )
	
	# Query Temperature Units	
	def queryTempUnits(self):
		'''
		Query the temperature units of the Gaussmeter
		
		Returns the temperature units as a string.
		'''
		unit = int( self.query('TUNIT?') )
		valid = ['Celsius','Kelvin']
		return valid[unit-1]
	
	
	
	
	
	
	
	
	
		
