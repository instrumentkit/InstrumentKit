#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# lcc25.py: class for the Thorlabs LCC25 Liquid Crystal Controller
##
# © 2013 Steven Casagrande (scasagrande@galvant.ca).
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
## IMPORTS #####################################################################
from instruments.abstract_instruments import Instrument
import quantities as pq
from flufl.enum import IntEnum

class LCC25mode(IntEnum):
    modulate = 0
    voltage1 = 1
    voltage2 = 2

class LCC25(Instrument):
    """
    The LCC25 is a controller for the thorlabs liquid crystal modules.
    it can set two voltages and then oscillate between them at a specific repetition rate
    The user manual can be found here:
    http://www.thorlabs.com/thorcat/18800/LCC25-Manual.pdf
    """
    def __init__(self, filelike):
        super(LCC25, self).__init__(filelike)
        self.terminator = "\r"
        self.end_terminator = ">"

    def check_command(self,command):
        """
        Checks for the \"Command error CMD_NOT_DEFINED\" error, which can sometimes occur if there were
        incorrect terminators on the previous command. If the command is successful, it returns the value,
        if not, it returns CMD_NOT_DEFINED
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


    def name(self):
        """
        gets the name and version number of the device
        """
        response = self.check_command("*idn?")
        if response is "CMD_NOT_DEFINED":
            self.name()          
        else:
            return response

    ### LCC SETTINGS ###

    @property
    def frequency(self):
        """
        The frequency at which the LCC oscillates between the two voltages
        """
        response = self.check_command("freq?")
        if not response is "CMD_NOT_DEFINED":
            return float(response)*pq.Hz
    @frequency.setter
    def frequency(self, newval):
        if newval < 5:
            raise ValueError("Frequency is too low.")
        if newval >150:
            raise ValueError("Frequency is too high")
        self.sendcmd("freq={}".format(newval))

    @property
    def mode(self):
        """
        The output mode of the LCC
        mode 0 modulates between voltage 1 and voltage 2
        mode 1 sets the output to voltage 1
        mode 2 sets the output to voltage 2
        """
        response = self.check_command("mode?")
        if not response is "CMD_NOT_DEFINED":
            return int(response)
    @mode.setter
    def mode(self, newval):
        if newval != 0 and newval != 1 and newval !=2:
            raise ValueError("Not a valid output mode")
        response = self.query("mode={}".format(newval))
        #print(response)

    @property
    def enable(self):
        """
        If output enable is on, there is a voltage on the output
        """
        response = self.check_command("enable?")
        if not response is "CMD_NOT_DEFINED":
            return float(response)
    @enable.setter
    def enable(self, newval):
        if newval != 0 and newval != 1:
            raise ValueError("Not a valid value for output enable")
        self.sendcmd("enable={}".format(newval))
    
    @property
    def extern(self):
        """
        0 for internal modulation, 1 for external TTL modulation
        """
        response = self.check_command("extern?")
        if not response is "CMD_NOT_DEFINED":
            return float(response)
    @extern.setter
    def extern(self, newval):
        if newval != 0 and newval != 1:
            raise ValueError("Not a valid value for external modulation enable")
        self.sendcmd("extern={}".format(newval))

    @property
    def remote(self):
        """
        0 for normal operation, 1 to lock out buttons
        """
        response = self.check_command("remote?")
        if not response is "CMD_NOT_DEFINED":
            return float(response)
    @remote.setter
    def remote(self, newval):
        if newval != 0 and newval != 1:
            raise ValueError("Not a valid value for remote operation enable")
        self.sendcmd("remote={}".format(newval))

    @property
    def voltage1(self):
        """
        The voltage value for output 1
        """
        response = self.check_command("volt1?")
        if not response is "CMD_NOT_DEFINED":
            return float(response)*pq.V
    @voltage1.setter
    def voltage1(self, newval):
        if newval < 0:
            raise ValueError("Voltage is too low.")
        if newval >25:
            raise ValueError("Voltage is too high")
        self.sendcmd("volt1={}".format(newval))

    @property
    def voltage2(self):
        """
        The voltage value for output 2
        """
        response = self.check_command("volt2?")
        if not response is "CMD_NOT_DEFINED":
            return float(response)*pq.V
    @voltage1.setter
    def voltage2(self, newval):
        if newval < 0:
            raise ValueError("Voltage is too low.")
        if newval >25:
            raise ValueError("Voltage is too high")
        self.sendcmd("volt2={}".format(newval))


    @property
    def min_voltage(self):
        """
        The minimum voltage value for the test mode
        """
        response = self.check_command("min?")
        if not response is "CMD_NOT_DEFINED":
            return float(response)*pq.V
    @min_voltage.setter
    def min_voltage(self, newval):
        if newval < 0:
            raise ValueError("Voltage is too low.")
        if newval >25:
            raise ValueError("Voltage is too high")
        self.sendcmd("min={}".format(newval))

    
    @property
    def max_voltage(self):
        """
        The maximum voltage value for the test mode
        if the maximum voltage is greater than the minimum voltage, nothing happens
        """
        response = self.check_command("max?")
        if not response is "CMD_NOT_DEFINED":
            return float(response)*pq.V
    
    @max_voltage.setter
    def max_voltage(self, newval):
        if newval < 0:
            raise ValueError("Voltage is too low.")
        if newval >25:
            raise ValueError("Voltage is too high")
        self.sendcmd("max={}".format(newval))

    @property
    def dwell(self):
        """
        The dwell time for voltages for the test mode
        """
        response = self.check_command("dwell?")
        if not response is "CMD_NOT_DEFINED":
            return float(response)*pq.ms
    
    @dwell.setter
    def dwell(self, newval):
        if newval < 0:
            raise ValueError("Dwell time must be positive")
        self.sendcmd("dwell={}".format(newval))

    @property
    def increment(self):
        """
        The voltage increment for voltages for the test mode
        """
        response = self.check_command("increment?")
        if not response is "CMD_NOT_DEFINED":
            return float(response)*pq.V
    
    @increment.setter
    def increment(self, newval):
        if newval < 0:
            raise ValueError("Increment voltage must be positive")
        self.sendcmd("increment={}".format(newval))


    ### LCC Methods ###
    def default(self):
        """
        restores factory settings
        returns 1 if successful
        """
        response = self.check_command("default")
        if not response is "CMD_NOT_DEFINED":
            return 1
        else:
            return 0

    def save(self):
        """
        stores the parameters in static memory
        returns 1 if successful
        """
        response = self.check_command("save")
        if not response is "CMD_NOT_DEFINED":
            return 1
        else:
            return 0

    def set_settings(self,slot):
        """
        saves the current settings to memory
        returns 1 if successful
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
        gets the current settings from memory
        returns 1 if successful
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
        Puts the LCC in test mode - meaning it will increment the output voltage from the minimum value to the maximum value, in increments, waiting for the dwell time
        returns 1 if successful
        """
        response = self.check_command("test")
        if not response is "CMD_NOT_DEFINED":
            return 1
        else:
            return 0
