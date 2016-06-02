#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides support for the Qubitekk MC1 Motor Controller.

MC1 Class originally contributed by Catherine Holloway.
"""

# IMPORTS #####################################################################
from __future__ import absolute_import
from instruments.abstract_instruments import Instrument
from enum import Enum
# CLASSES #####################################################################


class MC1(Instrument):
    """
    The MC1 is a controller for the qubitekk motor controller. Used with a
    linear actuator to perform a HOM dip.
    """
    def __init__(self, filelike, increment=1, upper_limit=300,
                 lower_limit=-300):
        super(MC1, self).__init__(filelike)
        self.terminator = "\r"
        self.increment = increment
        self.lower_limit = lower_limit
        self.upper_limit = upper_limit
        self._firmware = None
        self._controller = None


     # ENUMS #

    class MotorType(Enum):
        radio = "Radio"
        relay = "Relay"

    # PROPERTIES #


    @property
    def setting(self):
        """
        Get the current output setting
        :return: int, representing the currently active channel
        """
        response = self.query("OUTP?")
        return int(response)

    @setting.setter
    def setting(self, new_val):
        """
        Set the current output setting
        :param new_val: the output channel number, either 0 or 1
        :type new_val: either int or boolean
        """
        if new_val == 0:
            self.sendcmd(":OUTP 0")
        elif new_val == 1:
            self.sendcmd(":OUTP 1")
        else:
            raise ValueError("Setting not recognized")

    @property
    def position(self):
        """
        Return the internal motor state position
        :return: the internal position of the motor
        :rtype: int
        """
        response = self.query("POSI?")
        return int(response)

    @property
    def direction(self):
        """
        Return the internal direction variable, which is a function of how far
        the motor needs to go
        :return: the direction variable
        :rtype: int
        """
        response = self.query("DIRE?")
        return int(response)

    @property
    def firmware(self):
        """
        Gets the firmware version

        :rtype: `tuple`(Major:`int`, Minor:`int`, Patch`int`)
        """
        # the firmware is assumed not to change while the device is active
        # firmware is stored locally as it will be gotten often
        # pylint: disable=no-member
        if self._firmware is None:
            while self._firmware is None:
                self._firmware = self.query("FIRM?")
                value = self._firmware.split(".")
                if len(value) < 3:
                    for _ in range(3-len(value)):
                        value.append(0)
                value = tuple(map(int, value))
                self._firmware = value
        return self._firmware

    @property
    def controller(self):
        """
        Get the motor controller type
        :rtype: MC1.MotorType
        """
        if self._controller is None:
            response = self.query("MOTO?")
            self._controller = self.MotorType(response)
        return self._controller

    @property
    def move_timeout(self):
        """
        Return the motor's timeout value, which indicates the number of clock
        cycles before the motor can start moving again
        :return: the internal timeout of the motor
        :rtype: int
        """
        response = self.query("TAME?")
        return int(response)

    @property
    def range(self):
        """
        Create a range of values using limits and increment
        :rtype: range
        """
        return range(self.lower_limit, self.upper_limit, self.increment)

    # METHODS #

    def is_centering(self):
        """
        Query whether the motor is in its centering phase
        :return: 0 if not centering, 1 if centering
        :rtype: int
        """
        response = self.query("CENT?")
        return int(response)

    def center(self):
        """
        Commands the motor to go to the center of its travel range
        """
        self.sendcmd(":CENT")

    def reset(self):
        """
        Sends the stage to the limit of one of its travel ranges
        """
        self.sendcmd(":RESE")

    def move(self, new_val):
        """
        Move to a specified location
        :param new_val: the location
        :type new_val: int
        """
        if self.lower_limit <= new_val <= self.upper_limit:
            self.sendcmd(":MOVE "+str(int(new_val)))
        else:
            raise ValueError("Location out of range")