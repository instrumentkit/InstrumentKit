#!/usr/bin/python
# Filename: keithley195.py

# Original author: Steven Casagrande (stevencasagrande@gmail.com)
# 2012

# This work is released under the Creative Commons Attribution-Sharealike 3.0 license.
# See http://creativecommons.org/licenses/by-sa/3.0/ or the included license/LICENSE.TXT file for more information.

# Attribution requirements can be found in license/ATTRIBUTION.TXT

from instrument.instrument import Instrument

class Keithley195(Instrument):
	def __init__(self, port, address,timeout_length):
		Instrument.__init__(self,port,address,timeout_length)
		self.write('YX') # Removes the termination CRLF characters from the instrument
		
	def read(self):
		self.write('+read')
		return self.readline()
	
	def trigger(self):
		self.write('X')
	
	def setFunction(self,func):
		
		if not isinstance(func,str):
			raise Exception('Meaurement mode must be a string.')
		func = func.lower()
		
		valid = ['volt:dc','volt:ac','res','curr:dc','curr:ac']
		valid2 = ['voltage:dc','voltage:ac','resistance','current:dc','current:ac']
		
		if func in valid2:
			func = valid2.index(func)
		elif func in valid:
			func = valid.index(func)
		else:
			raise Exception('Valid measurement modes are: ' + str(valid2))
		
		self.write('F' + func + 'X') # Write and trigger instrument
		
	def setVoltageDCRange(self,voltage):
		if isinstance(voltage,str):
			voltage = voltage.lower()
			if voltage == 'auto':
				voltage = 0
			else:
				raise Exception('Only valid string for voltage range is "auto".')
		elif isinstance(voltage,float) or isinstance(voltage,int):
			valid = [20e-3,20e-3,2,20,200,1000]
			if voltage in valid:
				voltage = valid.index(voltage) + 1
			else:
				raise Exception('Valid voltage ranges are: ' + str(valid))
		else:
			raise Exception('Instrument voltage range must be specified as a float, integer, or string.')
			
		self.write('R' + voltage + 'X')
	
	def setVoltageACRange(self,voltage):
		if isinstance(voltage,str):
			voltage = voltage.lower()
			if voltage == 'auto':
				voltage = 0
			else:
				raise Exception('Only valid string for voltage range is "auto".')
		elif isinstance(voltage,float) or isinstance(voltage,int):
			valid = [200e-3,200e-3,2,20,200,700]
			if voltage in valid:
				voltage = valid.index(voltage) + 1
			else:
				raise Exception('Valid voltage ranges are: ' + str(valid))
		else:
			raise Exception('Instrument voltage range must be specified as a float, integer, or string.')
			
		self.write('R' + voltage + 'X')
			
	def setCurrentRange(self,current)
		if isinstance(current,str):
			current = current.lower()
			if current == 'auto':
				current = 0
			else:
				raise Exception('Only valid string for current range is "auto".')
		elif isinstance(current,float) or isinstance(current,int):
			valid = [20e-6,200e-6,2e-3,20e-3,200e-3,2]
			if current in valid:
				current = valid.index(current) + 1
			else:
				raise Exception('Valid current ranges are: ' + str(valid))
		else:
			raise Exception('Instrument current range must be specified as a float, integer, or string.')
			
		self.write('R' + current + 'X')
			
	def setResistanceRange(self,res)
		if isinstance(res,str):
			res = res.lower()
			if res == 'auto':
				res = 0
			else:
				raise Exception('Only valid string for resistance range is "auto".')
		elif isinstance(res,float) or isinstance(res,int):
			valid = [20,200,2000,20e3,200e3,2e6,20e6]
			if res in valid:
				res = valid.index(res) + 1
			else:
				raise Exception('Valid resistance ranges are: ' + str(valid))
		else:
			raise Exception('Instrument resistance range must be specified as a float, integer, or string.')
			
		self.write('R' + res + 'X')
			
	def autoRange(self)
		self.write('R0X')		
			
	def 		
			
			
			
			
			
			
			
			
			
