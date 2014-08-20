#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# lcc25.py: class for the Thorlabs LCC25 Liquid Crystal Controller
##
# © 2014 Steven Casagrande (scasagrande@galvant.ca).
#
# This file is a part of the InstrumentKit project.
# Licensed under the AGPL version 3.
##
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
##
# LCC25 Class contributed by Catherine Holloway
#
## IMPORTS #####################################################################

import quantities as pq
from flufl.enum import IntEnum

from instruments.abstract_instruments import Instrument
from instruments.util_fns import assume_units

## CLASSES #####################################################################

class LCC25(Instrument):
    """
    The LCC25 is a controller for the thorlabs liquid crystal modules.
    it can set two voltages and then oscillate between them at a specific 
    repetition rate.
    
    The user manual can be found here:
    http://www.thorlabs.com/thorcat/18800/LCC25-Manual.pdf
    """
    def __init__(self, filelike):
        super(LCC25, self).__init__(filelike)
        self.terminator = "\r"
        self.end_terminator = ">"
        
    ## ENUMS ##
    
    class Mode(IntEnum):
        modulate = 0
        voltage1 = 1
        voltage2 = 2
    
    ## PROPERTIES ##

    def name(self):
        """
        gets the name and version number of the device
        """
        response = self.check_command("*idn?")
        if response is "CMD_NOT_DEFINED":
            self.name()          
        else:
            return response

    @property
    def frequency(self):
        """
        Gets/sets the frequency at which the LCC oscillates between the 
        two voltages.
        
        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of units Hertz.
        :type: `~quantities.Quantity`
        """
        response = self.check_command("freq?")
        if not response is "CMD_NOT_DEFINED":
            return float(response)*pq.Hz
    @frequency.setter
    def frequency(self, newval):
        newval = assume_units(newval, pq.Hz).rescale(pq.Hz).magnitude
        if newval < 5:
            raise ValueError("Frequency is too low.")
        if newval >150:
            raise ValueError("Frequency is too high")
        self.sendcmd("freq={}".format(newval))

    @property
    def mode(self):
        """
        Gets/sets the output mode of the LCC25
        
        :type: `LCC25.Mode`
        """
        response = self.check_command("mode?")
        if not response is "CMD_NOT_DEFINED":
            return LCC25.Mode[int(response)]
    @mode.setter
    def mode(self, newval):
        if (newval.enum is not LCC25.Mode):
            raise TypeError("Mode setting must be a `LCC25.Mode` value, "
                "got {} instead.".format(type(newval)))
        response = self.query("mode={}".format(newval.value))

    @property
    def enable(self):
        """
        Gets/sets the output enable status.
        
        If output enable is on (`True`), there is a voltage on the output.
        
        :type: `bool`
        """
        response = self.check_command("enable?")
        if not response is "CMD_NOT_DEFINED":
            return True if int(response) is 1 else False
    @enable.setter
    def enable(self, newval):
        if not isinstance(newval, bool):
            raise TypeError("LLC25 enable property must be specified with a "
                            "boolean.")
        self.sendcmd("enable={}".format(int(newval)))
    
    @property
    def extern(self):
        """
        Gets/sets the use of the external TTL modulation.
        
        Value is `True` for external TTL modulation and `False` for internal
        modulation.
        
        :type: `bool`
        """
        response = self.check_command("extern?")
        if not response is "CMD_NOT_DEFINED":
            return True if int(response) is 1 else False
    @extern.setter
    def extern(self, newval):
        if not isinstance(newval, bool):
            raise TypeError("LLC25 extern property must be specified with a "
                            "boolean.")
        self.sendcmd("extern={}".format(int(newval)))

    @property
    def remote(self):
        """
        Gets/sets front panel lockout status for remote instrument operation.
        
        Value is `False` for normal operation and `True` to lock out the front
        panel buttons.
        
        :type: `bool`
        """
        response = self.check_command("remote?")
        if not response is "CMD_NOT_DEFINED":
            return True if int(response) is 1 else False
    @remote.setter
    def remote(self, newval):
        if not isinstance(newval, bool):
            raise TypeError("LLC25 remote property must be specified with a "
                            "boolean.")
        self.sendcmd("remote={}".format(int(newval)))

    @property
    def voltage1(self):
        """
        Gets/sets the voltage value for output 1.
        
        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of units Volts.
        :type: `~quantities.Quantity`
        """
        response = self.check_command("volt1?")
        if not response is "CMD_NOT_DEFINED":
            return float(response)*pq.V
    @voltage1.setter
    def voltage1(self, newval):
        newval = assume_units(newval, pq.V).rescale(pq.V).magnitude
        if newval < 0:
            raise ValueError("Voltage is too low.")
        if newval > 25:
            raise ValueError("Voltage is too high")
        self.sendcmd("volt1={}".format(newval))

    @property
    def voltage2(self):
        """
        Gets/sets the voltage value for output 2.
        
        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of units Volts.
        :type: `~quantities.Quantity`
        """
        response = self.check_command("volt2?")
        if not response is "CMD_NOT_DEFINED":
            return float(response)*pq.V
    @voltage1.setter
    def voltage2(self, newval):
        newval = assume_units(newval, pq.V).rescale(pq.V).magnitude
        if newval < 0:
            raise ValueError("Voltage is too low.")
        if newval > 25:
            raise ValueError("Voltage is too high")
        self.sendcmd("volt2={}".format(newval))

    @property
    def min_voltage(self):
        """
        Gets/sets the minimum voltage value for the test mode.
        
        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of units Volts.
        :type: `~quantities.Quantity`
        """
        response = self.check_command("min?")
        if not response is "CMD_NOT_DEFINED":
            return float(response)*pq.V
    @min_voltage.setter
    def min_voltage(self, newval):
        newval = assume_units(newval, pq.V).rescale(pq.V).magnitude
        if newval < 0:
            raise ValueError("Voltage is too low.")
        if newval > 25:
            raise ValueError("Voltage is too high")
        self.sendcmd("min={}".format(newval))

    @property
    def max_voltage(self):
        """
        Gets/sets the maximum voltage value for the test mode. If the maximum 
        voltage is less than the minimum voltage, nothing happens.
        
        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of units Volts.
        :type: `~quantities.Quantity`
        
        """
        response = self.check_command("max?")
        if not response is "CMD_NOT_DEFINED":
            return float(response)*pq.V
    @max_voltage.setter
    def max_voltage(self, newval):
        newval = assume_units(newval, pq.V).rescale(pq.V).magnitude
        if newval < 0:
            raise ValueError("Voltage is too low.")
        if newval > 25:
            raise ValueError("Voltage is too high")
        self.sendcmd("max={}".format(newval))

    @property
    def dwell(self):
        """
        Gets/sets the dwell time for voltages for the test mode.
        
        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of units milliseconds.
        :type: `~quantities.Quantity`
        """
        response = self.check_command("dwell?")
        if not response is "CMD_NOT_DEFINED":
            return float(response)*pq.ms
    @dwell.setter
    def dwell(self, newval):
        newval = int(assume_units(newval, pq.ms).rescale(pq.ms).magnitude)
        if newval < 0:
            raise ValueError("Dwell time must be positive")
        self.sendcmd("dwell={}".format(newval))

    @property
    def increment(self):
        """
        Gets/sets the voltage increment for voltages for the test mode.
        
        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of units Volts.
        :type: `~quantities.Quantity`
        """
        response = self.check_command("increment?")
        if not response is "CMD_NOT_DEFINED":
            return float(response)*pq.V
    @increment.setter
    def increment(self, newval):
        newval = assume_units(newval, pq.V).rescale(pq.V).magnitude
        if newval < 0:
            raise ValueError("Increment voltage must be positive")
        self.sendcmd("increment={}".format(newval))

    ## METHODS ##
    
    def check_command(self,command):
        """
        Checks for the \"Command error CMD_NOT_DEFINED\" error, which can 
        sometimes occur if there were incorrect terminators on the previous 
        command. If the command is successful, it returns the value, if not, 
        it returns CMD_NOT_DEFINED
        
        check_command will also clear out the query string
        """
        response = self.query(command)
        response = self.read()
        cmd_find = response.find("CMD_NOT_DEFINED")
        if cmd_find ==-1:
            error_find = response.find("CMD_ARG_INVALID")
            if error_find ==-1:
                output_str = response.replace(command,"")
                output_str = output_str.replace(self.terminator,"")
                output_str = output_str.replace(self.end_terminator,"")
            else:
                output_str = "CMD_ARG_INVALID"
        else:
            output_str = "CMD_NOT_DEFINED"
        return output_str
    
    def default(self):
        """
        Restores instrument to factory settings.
        
        Returns 1 if successful, 0 otherwise
        
        :rtype: `int`
        """
        response = self.check_command("default")
        if not response is "CMD_NOT_DEFINED":
            return 1
        else:
            return 0

    def save(self):
        """
        Stores the parameters in static memory
        
        Returns 1 if successful, zero otherwise.
        
        :rtype: `int`
        """
        response = self.check_command("save")
        if not response is "CMD_NOT_DEFINED":
            return 1
        else:
            return 0

    def set_settings(self, slot):
        """
        Saves the current settings to memory
        
        Returns 1 if successful, zero otherwise.
        
        :param slot: Memory slot to use, valid range `[1,4]`
        :type slot: `int`
        
        :rtype: `int`
        """
        if slot < 0:
            raise ValueError("Slot number is less than 0")
        if slot > 4:
            raise ValueError("Slot number is greater than 4")
        response = self.check_command("set={}".format(slot))
        if response != "CMD_NOT_DEFINED" and response != "CMD_ARG_INVALID":
            return 1
        else:
            return 0

    def get_settings(self,slot):
        """
        Gets the current settings to memory
        
        Returns 1 if successful, zero otherwise.
        
        :param slot: Memory slot to use, valid range `[1,4]`
        :type slot: `int`
        
        :rtype: `int`
        """
        if slot < 0:
            raise ValueError("Slot number is less than 0")
        if slot > 4:
            raise ValueError("Slot number is greater than 4")
        response = self.check_command("get={}".format(slot))
        if response != "CMD_NOT_DEFINED" and response != "CMD_ARG_INVALID":
            return 1
        else:
            return 0

    def test_mode(self):
        """
        Puts the LCC in test mode - meaning it will increment the output 
        voltage from the minimum value to the maximum value, in increments, 
        waiting for the dwell time
        
        Returns 1 if successful, zero otherwise.
        
        :rtype: `int`
        """
        response = self.check_command("test")
        if not response is "CMD_NOT_DEFINED":
            return 1
        else:
            return 0
