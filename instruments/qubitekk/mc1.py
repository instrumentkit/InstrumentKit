#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides support for the Qubitekk MC1 Motor Controller.

MC1 Class originally contributed by Catherine Holloway.
"""

# IMPORTS #####################################################################
from __future__ import absolute_import
from builtins import range
from enum import Enum

from instruments.abstract_instruments import Instrument
# CLASSES #####################################################################
from instruments.util_fns import int_property, enum_property


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
        """
        Enum for the motor types for the MC1
        """
        radio = "Radio"
        relay = "Relay"

    # PROPERTIES #

    setting = int_property(
        name="OUTP",
        doc="""
        Gets/sets the output setting of the optical switch.

        :type: `int`
        """,
        valid_set=range(2),
        set_fmt=":{} {}"
    )

    position = int_property(
        name="POSI",
        doc="""
        Get the internal motor state position.

        :type: `int`
        """,
        readonly=True
    )

    direction = int_property(
        name="DIRE",
        doc="""
        Get the internal direction variable, which is a function of how far
        the motor needs to go.

        :type: `int`
        """,
        readonly=True
    )

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

    controller = enum_property(
        'MOTO',
        MotorType,
        doc="""
        Get the motor controller type.
        """,
        readonly=True
    )

    move_timeout = int_property(
        name="TIME",
        doc="""
        Get the motor's timeout value, which indicates the number of clock
        cycles before the motor can start moving again.

        :type: `int`
        """,
        readonly=True
    )

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

    def move(self, new_position):
        """
        Move to a specified location. Position is unitless and is defined as
        the number of motor steps. It varies between motors.
        :param new_position: the location
        :type new_position: int
        """
        if self.lower_limit <= new_position <= self.upper_limit:
            cmd = ":MOVE "+str(int(new_position))
            self.sendcmd(cmd)
        else:
            raise ValueError("Location out of range")
