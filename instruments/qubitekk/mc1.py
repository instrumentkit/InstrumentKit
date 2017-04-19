#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides support for the Qubitekk MC1 Motor Controller.

MC1 Class originally contributed by Catherine Holloway.
"""

# IMPORTS #####################################################################

from __future__ import absolute_import, division

from builtins import range, map
from enum import Enum

import quantities as pq

from instruments.abstract_instruments import Instrument
from instruments.util_fns import (
    int_property, enum_property, unitful_property, assume_units
)

# CLASSES #####################################################################


class MC1(Instrument):
    """
    The MC1 is a controller for the qubitekk motor controller. Used with a
    linear actuator to perform a HOM dip.
    """
    def __init__(self, filelike):
        super(MC1, self).__init__(filelike)
        self.terminator = "\r"
        self._increment = 1*pq.ms
        self._lower_limit = -300*pq.ms
        self._upper_limit = 300*pq.ms
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

    @property
    def increment(self):
        """
        Gets/sets the stepping increment value of the motor controller

        :units: As specified, or assumed to be of units milliseconds
        :type: `~quantities.Quantity`
        """
        return self._increment

    @increment.setter
    def increment(self, newval):
        self._increment = assume_units(newval, pq.ms).rescale(pq.ms)

    @property
    def lower_limit(self):
        """
        Gets/sets the stepping lower limit value of the motor controller

        :units: As specified, or assumed to be of units milliseconds
        :type: `~quantities.Quantity`
        """
        return self._lower_limit

    @lower_limit.setter
    def lower_limit(self, newval):
        self._lower_limit = assume_units(newval, pq.ms).rescale(pq.ms)

    @property
    def upper_limit(self):
        """
        Gets/sets the stepping upper limit value of the motor controller

        :units: As specified, or assumed to be of units milliseconds
        :type: `~quantities.Quantity`
        """
        return self._upper_limit

    @upper_limit.setter
    def upper_limit(self, newval):
        self._upper_limit = assume_units(newval, pq.ms).rescale(pq.ms)

    direction = unitful_property(
        name="DIRE",
        doc="""
        Get the internal direction variable, which is a function of how far
        the motor needs to go.

        :type: `~quantities.Quantity`
        :units: milliseconds
        """,
        units=pq.ms,
        readonly=True
    )

    inertia = unitful_property(
        name="INER",
        doc="""
        Gets/Sets the amount of force required to overcome static inertia. Must
         be between 0 and 100 milliseconds.

        :type: `~quantities.Quantity`
        :units: milliseconds
        """,
        format_code='{:.0f}',
        units=pq.ms,
        valid_range=(0*pq.ms, 100*pq.ms),
        set_fmt=":{} {}"
    )

    @property
    def internal_position(self):
        """
        Get the internal motor state position, which is equivalent to the total
         number of milliseconds that voltage has been applied to the motor in
         the positive direction minus the number of milliseconds that voltage
         has been applied to the motor in the negative direction.

        :type: `~quantities.Quantity`
        :units: milliseconds
        """
        response = int(self.query("POSI?"))*self.step_size
        return response

    metric_position = unitful_property(
        name="METR",
        doc="""
        Get the estimated motor position, in millimeters.

        :type: `~quantities.Quantity`
        :units: millimeters
        """,
        units=pq.mm,
        readonly=True
    )

    setting = int_property(
        name="OUTP",
        doc="""
        Gets/sets the output port of the optical switch. 0 means input 1 is
        directed to output 1, and input 2 is directed to output 2. 1 means that
         input 1 is directed to output 2 and input 2 is directed to output 1.

        :type: `int`
        """,
        valid_set=range(2),
        set_fmt=":{} {}"
    )

    step_size = unitful_property(
        name="STEP",
        doc="""
        Gets/Sets the number of milliseconds per step. Must be between 1
        and 100 milliseconds.

        :type: `~quantities.Quantity`
        :units: milliseconds
        """,
        format_code='{:.0f}',
        units=pq.ms,
        valid_range=(1*pq.ms, 100*pq.ms),
        set_fmt=":{} {}"
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

    @property
    def move_timeout(self):
        """
        Get the motor's timeout value, which indicates the number of
        milliseconds before the motor can start moving again.

        :type: `~quantities.Quantity`
        :units: milliseconds
        """
        response = int(self.query("TIME?"))
        return response*self.step_size

    # METHODS #

    def is_centering(self):
        """
        Query whether the motor is in its centering phase

        :return: False if not centering, True if centering
        :rtype: `bool`
        """
        response = self.query("CENT?")
        return True if int(response) == 1 else False

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
        :type new_position: `~quantities.Quantity`
        """
        if self.lower_limit <= new_position <= self.upper_limit:
            new_position = assume_units(new_position, pq.ms).rescale(pq.ms)
            clock_cycles = new_position/self.step_size
            cmd = ":MOVE "+str(int(clock_cycles))
            self.sendcmd(cmd)
        else:
            raise ValueError("Location out of range")
