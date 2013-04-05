#!/usr/bin/python
# Filename: yokogawa7651.py

# Original author: Steven Casagrande (stevencasagrande@gmail.com)
# 2012

# This work is released under the Creative Commons Attribution-Sharealike 3.0 license.
# See http://creativecommons.org/licenses/by-sa/3.0/ or the included license/LICENSE.TXT file for more information.

# Attribution requirements can be found in license/ATTRIBUTION.TXT

from instruments.abstract_instruments import Instrument

class Yokogawa7651(Instrument):
    def __init__(self, port, address,timeout_length):
        super(Yokogawa7651, self).__init__(self,port,address,timeout_length)
        self.outputtng = 0
        
    def trigger(self):
        '''
        Triggering function for the Yokogawa 7651.
        
        After changing any parameters of the instrument (for example, output voltage), the device needs to be triggered before it will update.
        '''
        self.write('E;')
    
    # Set Voltage Range
    def setVoltageRange(self,voltage):
        '''
        Function changes the voltage range of the power supply. 
        A float representing the desired voltage will have the range adjusted accordingly, or a string specifying the range will also work.
        
        Device can output a max of 30V.
        
        voltage: Desired voltage (float) or directly specified voltage range (string)
        voltage = {<0...+30.0>|10MV|100MV|1V|10V|30V},float/string
        '''
        if ( type(voltage) == type(float()) ) or ( type(voltage) == type(int()) ):
            if voltage < 10e-3:
                yokoRange = 2
            elif ( voltage >= 10e-3 ) and ( voltage < 100e-3 ):
                yokoRange = 3
            elif ( voltage >= 100e-3 ) and ( voltage < 1 ):
                yokoRange = 4
            elif ( voltage >= 1 ) and ( voltage < 10 ):
                yokoRange = 5
            elif ( voltage >= 10 ) and ( voltage <= 30 ):
                yokoRange = 6
            else:
                raise Exception('Highest voltage range is 30V.')
        elif type(voltage) == type(str()):
            voltage = voltage.lower()
            valid = ['10mv','100mv','1v','10v','30v']
            if voltage not in valid:
                raise Exception('Allowed voltage range values are 10mv, 100mv, 1v, 10v and 30v.')
            else:
                yokoRange = valid.index(voltage) + 2    
                
        self.write( 'R%i;' % (yokoRange) )
        self.trigger()
    
    # Set Current Range
    def setCurrentRange(self,current):
        '''
        Function changes the current range of the power supply. 
        A float representing the desired current will have the range adjusted accordingly, or a string specifying the range will also work.
        
        Device has a output max of 100mA.
        
        current: Desired current (float) or directly specified current range (string)
        voltage = {<0...+0.1>|1MA|10MA|100MA},float/string
        '''
        if ( type(current) == type(float()) ) or ( type(current) == type(int()) ):
            if current < 1e-3:
                yokoRange = 4
            elif ( current >= 1e-3 ) and ( current < 10e-3 ):
                yokoRange = 5
            elif ( voltage >= 10e-3 ) and ( voltage < 100e-3 ):
                yokoRange = 6
            else:
                raise Exception('Highest current range is 100mA.')
        elif type(current) == type(str()):
            current = current.lower()
            valid = ['1ma','10ma','100ma']
            if current not in valid:
                raise Exception('Allowed current range values are 1mA, 10mA and 100mA.')
            else:
                yokoRange = valid.index(current) + 4    
                
        self.write( 'R%i;' % (yokoRange) )
        self.trigger()
    
    # Set Function    
    def setFunction(self,func):
        '''
        Set the output of the Yokogawa 7651 to either constant voltage or constant current mode.
        
        func: Desired constant (voltage or current) mode.
        func = {VOLTAGE|CURRENT},string
        '''
        if type(func) != type(str()):
            raise Exception('Parameter "func" must be a string.')
            
        func = func.lower()
        
        if func == 'voltage':
            setting = 1
        elif func == 'current':
            setting = 5
        else:
            raise Exception('Only allowed values are "voltage" and "current".')
        
        self.write( 'F%i;' % (setting) )
        self.trigger()
    
    # Set output Voltage    
    def setVoltage(self,voltage):
        '''
        Set the output voltage of the power supply.
        
        voltage: Desired constant output voltage
        voltage = <0...+30.0>,float
        '''
        
        if ( type(voltage) == type(float()) or type(voltage) == type(int()) ):
            self.setVoltageRange(voltage)
            self.write( 'S%f;' % (voltage) )
            self.trigger()
        else:
            raise Exception('Please specify voltage as a integer for float.')
    
    # Output    
    def output(self,setting):
        '''
        Enable or disable the output of the Yokogawa 7651.
        
        setting: Specify the state of the power supply output.
        setting = {0|1|OFF|ON},integer/string
        '''
        if type(setting) == type(str()):
            setting = setting.lower()
        
            if setting in ['off','on']:
                setting = ['off','on'].index(setting)
            if setting in ['0','1']:
                setting = int(setting)
                
        if setting not in [0,1]:
            raise Exception('Valid parameters are "on", "off", 1 and 0.')
        
        if setting == 1: # If we want to turn the output on
            if self.outputting == 0: # and we are NOT currently outputting
                self.write('O1;')
                self.trigger()
                self.outputting = 1
        else: # If we want to turn the output off
            if self.outputting == 1: # and we are curently outputting
                self.write('O0;')
                self.trigger()
                self.outputting = 0
                
        
        
        
                
                
                
                
                
                
