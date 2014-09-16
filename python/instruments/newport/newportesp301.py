#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# newportesp301.py: Controller for the Newport ESP-301 motor controller.
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

## FEATURES ####################################################################

from __future__ import division

## IMPORTS #####################################################################

from time import time, sleep

import datetime

from flufl.enum import IntEnum

from contextlib import contextmanager

import quantities as pq

from instruments.abstract_instruments import Instrument
from instruments.newport.errors import NewportError
from instruments.util_fns import assume_units

## ENUMS #######################################################################

class NewportESP301HomeSearchMode(IntEnum):
    """
    Enum containing different search modes code
    """
    #: Search along specified axes for the +0 position.
    zero_position_count = 0
    #: Search for combined Home and Index signals.
    home_index_signals = 1
    #: Search only for the Home signal.
    home_signal_only = 2
    #: Search for the positive limit signal.
    pos_limit_signal = 3
    #: Search for the negative limit signal.
    neg_limit_signal = 4
    #: Search for the positive limit and Index signals.
    pos_index_signals = 5
    #: Search for the negative limit and Index signals.
    neg_index_signals = 6


class NewportESP301Units(IntEnum):
    """
    Enum containing what `units` return means. 
    """
    encoder_step = 0
    motor_step= 1
    millimeter= 2
    micrometer = 3
    inches = 4
    milli_inches = 5
    micro_inches = 6
    degree = 7
    gradian = 8
    radian = 9
    milliradian = 10
    microradian = 11

class NewportESP301MotorType(IntEnum):
    """
    Enum for different motor types. 
    """
    undefined = 0
    dc_servo = 1 
    stepper_motor = 2 
    commutated_stepper_motor = 3 
    commutated_brushless_servo = 4 

## CLASSES #####################################################################

class _AxisList(object):
    # TODO: make this a ProxyList.
    """
    Used to make expressions like ``NewportESP301.axis[idx]``
    work as expected.
    """
    def __init__(self, controller):
        self._controller = controller
        self._axisDict = dict()
    def __getitem__(self, idx):
        # FIXME: need to check MAX AXES, but the docs are not clear
        #        on how to do this. Once that's done, expose it as len.
        if idx < 0:
            raise IndexError("Negative axis indices are not allowed.")
        # Change one-based indices to zero-based for easier
        # Python programming.
        axis = self._axisDict.get(idx+1,NewportESP301Axis(self._controller, idx + 1))
        self._axisDict[idx+1] = axis
        return axis


class NewportESP301(Instrument):
    """
    Handles communication with the Newport ESP-301 multiple-axis motor
    controller using the protocol documented in the `user's guide`_.

    .. _user's guide: http://assets.newport.com/webDocuments-EN/images/14294.pdf
    """
             

    def __init__(self, filelike):
        super(NewportESP301, self).__init__(filelike)
        self._execute_immediately = True
        self._command_list = []
        self.terminator = "\r"

    ## PROPERTIES ##

    @property
    def axis(self):
        """
        Gets the axes of the motor controller as a sequence. For instance,
        to move along a given axis::

        >>> controller = NewportESP301.open_serial("COM3")
        >>> controller.axis[0].move(-0.001, absolute=False)

        Note that the axes are numbered starting from zero, so that
        Python idioms can be used more easily. This is not the same convention
        used in the Newport ESP-301 user's manual, and so care must
        be taken when converting examples.

        :type: :class:`NewportESP301Axis`
        """
        
        return _AxisList(self)

    ## LOW-LEVEL COMMAND METHODS ##

    def _newport_cmd(self, cmd, params=[], target=None, errcheck=True):
        """
        The Newport ESP-301 command set supports checking for errors,
        specifying different axes and allows for multiple parameters.
        As such, it is convienent to wrap calls to the low-level
        `~instruments.abstract_instruments.Instrument.sendcmd` method
        in a method that is aware of the eccenticities of the controller.

        This method sends a command, checks for errors on the device
        and turns them into exceptions as needed.

        :param bool errcheck: If `False`, suppresses the standard error
            checking. Note that since error-checking is unsupported
            during device programming, ``errcheck`` must be `False`
            during ``PGM`` mode.
        """
        query_resp = None
        if isinstance(target, NewportESP301Axis):
            target = axis._axis_id
            
        raw_cmd = "{target}{cmd}{params}".format(
            target=target if target is not None else "",
            cmd=cmd.upper(),
            params=",".join(map(str, params))
        )
        
        if self._execute_immediately: 
            query_resp = self._execute_cmd(raw_cmd,errcheck)
        else:
            self._command_list.append(raw_cmd)

        # This works because "return None" is equivalent to "return".
        return query_resp

    def _execute_cmd(self,raw_cmd,errcheck=True):
        """
        Takes a string command and executes it on Newport

        
        :param str raw_cmd: 
        :param bool errcheck: 

        
        :return: response of device
        :rtype: `str`
        
        """
        query_resp = None
        
        if "?" in raw_cmd:
            query_resp = self.query(raw_cmd)
        else:
            self.sendcmd(raw_cmd)
            
        if errcheck:
            err_resp = self.query('TB?')
            
            code, timestamp, msg = err_resp.split(",")
            code = int(code)
            if code != 0:
                raise NewportError(code)

        return query_resp

    ## SPECIFIC COMMANDS ##

    def _home(self, axis, search_mode,errcheck=True):
        """
        Private method for searching for home "OR", so that
        the methods in this class and the axis class can both
        point to the same thing.
        """
        self._newport_cmd("OR", target=axis, params=[search_mode],errcheck=errcheck)


    def search_for_home(self,axis, search_mode=NewportESP301HomeSearchMode.zero_position_count.value ,errcheck=True ):
        """
        Searches each axis sequentially
        for home using the method specified by ``search_mode``.

        :param NewportESP301HomeSearchMode search_mode: Method to detect when
            Home has been found.
        """
        self._home(axis=1, search_mode=search_mode,errcheck=errcheck)

    def reset(self):
        """
        Causes the device to perform a hardware reset. Note that
        this method is only effective if the watchdog timer is enabled
        by the physical jumpers on the ESP-301. Please see the `user's guide`_
        for more information.
        """
        self._newport_cmd("RS",errcheck=False)

    ## USER PROGRAMS ##

    @contextmanager
    def define_program(self, program_id):
        """
        Erases any existing programs with a given program ID
        and instructs the device to record the commands within this
        ``with`` block to be saved as a program with that ID.
        
        For instance:
        
        >>> controller = NewportESP301.open_serial("COM3")
        >>> with controller.define_program(15):
        ...     controller.axis[0].move(0.001, absolute=False)
        ...
        >>> controller.run_program(15)
        
        :param int program_id: An integer label for the new program.
            Must be in ``xrange(1, 101)``.
        """
        if program_id not in xrange(1, 101):
            raise ValueError("Invalid program ID. Must be an integer from 1 to 100 (inclusive).")
        self._newport_cmd("XX", target=program_id)
        try:
            self._newport_cmd("EP", target=program_id)
            yield
        finally:
            self._newport_cmd("QP")

    @contextmanager
    def execute_bulk_command(self,errcheck=True):
        """
        Context manager do execute multiple of commands in a single communication with device

        Example::

            with self.execute_bulk_command():
                execute commands as normal...
        """
        self._execute_immediately = False
        yield
        command_string = reduce(lambda x ,y : x + ' ; '+ y +' ; ',self._command_list)        
        self._bulk_query_resp = self._execute_cmd(command_string,errcheck)
        self._command_list = []
        self._execute_immediately = True

    def run_program(self, program_id):
        """
        Runs a previously defined user program with a given program ID.
        """
        if program_id not in xrange(1, 101):
            raise ValueError("Invalid program ID. Must be an integer from 1 to 100 (inclusive).")
        self._newport_cmd("EX", target=program_id)
    
        
class NewportESP301Axis(object):
    """
    Encapsulates communication concerning a single axis
    of an ESP-301 controller. This class should not be
    instantiated by the user directly, but is
    returned by `NewportESP301.axis`.
    """
    # quantities micro inch
    micro_inch = pq.UnitQuantity('micro-inch',pq.inch/1e6, symbol = 'uin')
    
    # Some more work might need to be done here to make
    # the encoder_step and motor_step functional
    # I really don't have a concrete idea how I'm 
    # going to do this until I have a physical device

    _unit_dict = {
                0    :  pq.count,
                1    :  pq.count,
                2    :  pq.mm,
                3    :  pq.um,
                4    :  pq.inch,
                5    :  pq.mil,
                6    :  micro_inch, #compound unit for micro-inch
                7    :  pq.deg,
                8    :  pq.grad,
                9    :  pq.rad,
                10   :  pq.mrad,
                11   :  pq.urad,
                } 


    def __init__(self, controller, axis_id):
        if not isinstance(controller, NewportESP301):
            raise TypeError("Axis must be controlled by a Newport ESP-301 motor controller.")

        # TODO: check axis_id
        
        self._controller = controller
        self._axis_id = axis_id

        self._units = self.units
        
    ## CONTEXT MANAGERS ##
    
    @contextmanager
    def _units_of(self, units):
        """
        Sets the units for the corresponding axis to a those given by an integer
        label (see `NewportESP301Units`), ensuring that the units are properly
        reset at the completion of the context manager.
        """
        old_units = self._get_units()
        self._set_units(units)
        yield
        self._set_units(old_units)
        
    ## PRIVATE METHODS ##
    
    def _get_units(self):
        """
        Returns the integer label for the current units set for this axis.
        
        .. seealso::
            NewportESP301Units
        """
        return NewportESP301Units(
            self._controller._newport_cmd("SN?", target=self.axis_id)
        )
        
    def _set_units(self, new_units):
        return self._controller._newport_cmd(
            "SN", target=self.axis_id,
            params=[int(new_units)]
        )
        
    ## PROPERTIES ##
    
    @property
    def axis_id(self):
        """
        Get axis number of Newport Controller

        :type: `int`
        """
        return self._axis_id
    
    @property
    def is_motion_done(self):
        """
        `True` if and only if all motion commands have
        completed. This method can be used to wait for
        a motion command to complete before sending the next
        command.

        :type: `bool`
        """
        return bool(int(self._controller._newport_cmd("MD?", target=self.axis_id)))
        
    @property
    def acceleration(self):
        """
        Get acceleration

        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of current newport unit
        :param accel: Sets acceleration
        :type accel: `~quantities.Quantity` or `float`
        
        """
        
        return assume_units(float(self._controller._newport_cmd("AC?", target=self.axis_id)),
                self._units/(pq.s**2))    
    @acceleration.setter
    def acceleration(self,accel):
        accel = float(assume_units(accel,self._units/(pq.s**2)).rescale(
                self._units/(pq.s**2)).magnitude)
        return self._controller._newport_cmd("AC",target=self.axis_id,params=[accel])
   
    @property
    def deceleration(self):
        """
        Gets deceleration

        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of current newport :math:`\\frac{unit}{s^2}`
        :param decel: Sets deceleration 
        :type decel: `~quantities.Quantity` or float
        """
        return assume_units(float(self._controller._newport_cmd("AG?", target=self.axis_id)),
                self._units/(pq.s**2))
    @deceleration.setter
    def deceleration(self,decel):
        decel = float(assume_units(decel,self._units/(pq.s**2)).rescale(
                self._units/(pq.s**2)).magnitude)
        return self._controller._newport_cmd("AG",target=self.axis_id,params=[decel])
    
    @property
    def estop_deceleration(self):
        """
        Gets estop_deceleration

        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of current newport :math:`\\frac{unit}{s^2}`
        :param decel: Sets deceleration 
        :type decel: `~quantities.Quantity` or float
        """
        return assume_units(float(self._controller._newport_cmd("AE?", target=self.axis_id)),
                self._units/(pq.s**2))
    @estop_deceleration.setter
    def estop_deceleration(self,decel):
        decel = float(assume_units(decel,self._units/(pq.s**2)).rescale(
                self._units/(pq.s**2)).magnitude)
        return self._controller._newport_cmd("AE",target=self.axis_id,params=[decel])
   
    @property
    def jerk(self):
        """
        Gets and sets the jerk rate for the controller

        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of current newport unit
        :param accel: Sets acceleration
        :type accel: `~quantities.Quantity` or `float`
        
        """
        
        return assume_units(float(self._controller._newport_cmd("JK?", target=self.axis_id)),
                self._units/(pq.s**3))    
    @jerk.setter
    def jerk(self,jerk):
        jerk = float(assume_units(jerk,self._units/(pq.s**3)).rescale(
                self._units/(pq.s**3)).magnitude)
        return self._controller._newport_cmd("JK",target=self.axis_id,params=[jerk])

    @property
    def velocity(self):
        """
        Gets velocity

        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of current newport :math:`\\frac{unit}{s}`
        :param velocity: Sets velocity
        :type velocity: `~quantities.Quantity` or `float`
        """
        return assume_units(float(self._controller._newport_cmd("VA?", target=self.axis_id)),
                self._units/(pq.s))
    @velocity.setter
    def velocity(self,velocity):
        velocity = float(assume_units(velocity,self._units/(pq.s)).rescale(
                self._units/(pq.s)).magnitude)
        return self._controller._newport_cmd("VA",target=self.axis_id,params=[velocity])

    @property
    def max_velocity(self):
        """
        Get the maximum velocity

        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of current newport :math:`\\frac{unit}{s}`
        :param velocity: Sets the maximum velocity
        :type velocity: `~quantities.Quantity` or `float`
        """
        return assume_units(float(self._controller._newport_cmd("VU?", target=self.axis_id)),
                self._units/pq.s)
    @max_velocity.setter
    def max_velocity(self,velocity):
        velocity = float(assume_units(velocity,self._units/(pq.s)).rescale(
                self._units/(pq.s)).magnitude)
        return self._controller._newport_cmd("VU", target=self.axis_id,params=[velocity])
    
    @property
    def max_base_velocity(self):
        """
        Get the maximum base velocity for stepper motors

        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of current newport :math:`\\frac{unit}{s}`
        :param velocity: Sets the maximum velocity
        :type velocity: `~quantities.Quantity` or `float`
        """
        return assume_units(float(self._controller._newport_cmd("VB?", target=self.axis_id)),
                self._units/pq.s)
    @max_base_velocity.setter
    def max_base_velocity(self,velocity):
        velocity = float(assume_units(velocity,self._units/(pq.s)).rescale(
                self._units/(pq.s)).magnitude)
        return self._controller._newport_cmd("VB", target=self.axis_id,params=[velocity])
    
    @property
    def jog_high_velocity(self):
        """
        Gets and sets jog high velocity

        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of current newport :math:`\\frac{unit}{s}`
        :param jog_high_velocity: Sets velocity
        :type jog_high_velocity: `~quantities.Quantity` or `float`
        """
        return assume_units(float(self._controller._newport_cmd("JH?", target=self.axis_id)),
                self._units/(pq.s))
    @jog_high_velocity.setter
    def jog_high_velocity(self,jog_high_velocity):
        jog_high_velocity = float(assume_units(jog_high_velocity,self._units/(pq.s)).rescale(
                self._units/(pq.s)).magnitude)
        return self._controller._newport_cmd("JH",target=self.axis_id,params=[jog_high_velocity])

    @property
    def jog_low_velocity(self):
        """
        Gets and sets jog low velocity

        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of current newport :math:`\\frac{unit}{s}`
        :param jog_low_velocity: Sets velocity
        :type jog_low_velocity: `~quantities.Quantity` or `float`
        """
        return assume_units(float(self._controller._newport_cmd("JW?", target=self.axis_id)),
                self._units/(pq.s))
    @jog_low_velocity.setter
    def jog_low_velocity(self,jog_low_velocity):
        jog_low_velocity = float(assume_units(jog_low_velocity,self._units/(pq.s)).rescale(
                self._units/(pq.s)).magnitude)
        return self._controller._newport_cmd("JW",target=self.axis_id,params=[jog_low_velocity])

    @property
    def homing_velocity(self):
        """
        Gets and sets the homing velocity

        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of current newport :math:`\\frac{unit}{s}`
        :param homing_velocity: Sets velocity
        :type homing_velocity: `~quantities.Quantity` or `float`
        """
        return assume_units(float(self._controller._newport_cmd("OH?", target=self.axis_id)),
                self._units/(pq.s))
    @homing_velocity.setter
    def homing_velocity(self,homing_velocity):
        homing_velocity = float(assume_units(homing_velocity,self._units/(pq.s)).rescale(
                self._units/(pq.s)).magnitude)
        return self._controller._newport_cmd("OH",target=self.axis_id,params=[homing_velocity])

    @property
    def max_acceleration(self):
        """
        Get max acceleration

        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of current newport :math:`\\frac{unit}{s^2}`

        :param accel: Sets the maximum acceleration
        :type accel: `~quantities.Quantity` or `float`
        """
        return assume_units(float(self._controller._newport_cmd("AU?", target=self.axis_id)),
                self._units/(pq.s**2))
    @max_acceleration.setter
    def max_acceleration(self,accel):
        accel = float(assume_units(accel,self._units/(pq.s**2)).rescale(
                self._units/(pq.s**2)).magnitude)
        return self._controller._newport_cmd("AU",target=self.axis_id,params=[accel])

    # Max deacceleration is always the same as accelleration 
    @property
    def max_deceleration(self):
        """
        Get max deceleration

        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of current newport :math:`\\frac{unit}{s^2}`
        :param decel: Sets maximum deceleration
        :type: `~quantities.Quantity` or `float`
        """
        return self.max_acceleration
    @max_deceleration.setter
    def max_deacceleration(self,decel):        
        decel = float(assume_units(decel,self._units/(pq.s**2)).rescale(
                self._units/(pq.s**2)).magnitude)
        return self.max_acceleration(decel)
    
    @property
    def position(self):
        """
        Gets real position on axis in units

        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of current newport unit
        :type: `~quantities.Quantity` or `float`
        """
        return assume_units(float(self._controller._newport_cmd("TP?", target=self.axis_id)),
                self._units)
    @property
    def desired_position(self):
        """
        Gets desired position on axis in units

        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of current newport unit
        :type: `~quantities.Quantity` or `float`
        """
        return assume_units(float(self._controller._newport_cmd("DP?", target=self.axis_id)),
                self._units)
    @property
    def desired_velocity(self):
        """
        Gets desired velocity on axis in unit/s

        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of current newport unit/s
        :type: `~quantities.Quantity` or `float`
        """
        return assume_units(float(self._controller._newport_cmd("DP?", target=self.axis_id)),
                self._units/pq.s)
    
    @property
    def home(self):
        """
        Get home position

        :units: As specified (if a `~quantities.Quantity`) or assumed to be
            of current newport unit
        :param home: Sets home position of axis
        :type home: `~quantities.Quantity` or `float`
        """
        return assume_units(float(self._controller._newport_cmd("DH?", target=self.axis_id)),
                self._units)
    #default should be 0 as that sets current position as home
    @home.setter
    def home(self, home=0):
        home = float(assume_units(home,self._units).rescale(
                self._units).magnitude)
        return self._controller._newport_cmd("DH", target=self.axis_id, params=[home])
    
    @property
    def units(self):
        """
        Get the units that all commands are in reference to. 

        :param unit: Set the reference unit for axis

        :type unit: `~quantities.Quantity` with units corresponding to 
            units of axis connected  or int which corresponds to Newport 
            unit number 
        :rtype: `~quantities.Quantity`

        """
        self._units = self.get_pq_unit(self._get_units())
        return self._units
        
    @units.setter
    def units(self,unit):
        if isinstance(unit, int):
            self._units = self.get_pq_unit(NewportESP301Units(int(unit)))
        elif isinstance(unit,pq.Quantity):
            self._units = unit
            unit = self.get_unit_num(unit)

        return self._set_units(unit)

    @property
    def encoder_resolution(self):
        """
        Get the resolution of the encode. The minimum number of units per step. 
        Encoder functionality must be enabled

        :units: The number of units per encoder step
        :param resolution: Sets the encoder resolution of axis
        :type resolution: `~quantities.Quantity` or `float`
        """

        return assume_units(float(self._controller._newport_cmd("SU?",target=self.axis_id)),
                self._units)
    @encoder_resolution.setter
    def encoder_resolution(self, resolution):
        
        resolution = float(assume_units(resolution,self._units).rescale(
                self._units).magnitude)
        return self._controller._newport_cmd("SU",target=self.axis_id,params=[resolution])

    @property
    def full_step_resolution(self):
        """
        Get the resolution of the encode. The minimum number of units per step. 
        Encoder functionality must be enabled

        :units: The number of units per encoder step
        :param full_step_resolution: Sets the encoder resolution of axis
        :type full_step_resolution: `~quantities.Quantity` or `float`
        """

        return assume_units(float(self._controller._newport_cmd("FR?",target=self.axis_id)),
                self._units)
    @full_step_resolution.setter
    def full_step_resolution(self, full_step_resolution):
        
        full_step_resolution = float(assume_units(full_step_resolution,self._units).rescale(
                self._units).magnitude)
        return self._controller._newport_cmd("FR",target=self.axis_id,params=[full_step_resolution])
    
    @property
    def left_limit(self):
        """
        Get the left travel limit

        :units: The limit in units
        :param limit: Set the travel limit
        :type: `~quantities.Quantity` or `float`
        """
        return assume_units(float(self._controller._newport_cmd("SL?",target=self.axis_id)),
                self._units)
    @left_limit.setter
    def left_limit(self, limit):
        limit = float(assume_units(limit,self._units).rescale(
                self._units).magnitude)
        return self._controller._newport_cmd("SL",target=self.axis_id,params=[limit])    

    @property
    def right_limit(self):
        """
        Get the right travel limit

        :units: units
        :param limit: Set the travel limit
        :type: `~quantities.Quantity` or `float`
        """
        return assume_units(float(self._controller._newport_cmd("SR?",target=self.axis_id)),
                self._units)
    @right_limit.setter
    def right_limit(self, limit):
        limit = float(assume_units(limit,self._units).rescale(
            self._units).magnitude)
        return self._controller._newport_cmd("SR",target=self.axis_id,params=[limit])
    
    @property
    def error_threshold(self):
        """
        Get and set the error threshold 

        :units: units
        :param error_threshold: Set the travel limit
        :type: `~quantities.Quantity` or `float`
        """
        return assume_units(float(self._controller._newport_cmd("FE?",target=self.axis_id)),
                self._units)
    @error_threshold.setter
    def error_threshold(self, error_threshold):
        error_threshold = float(assume_units(error_threshold,self._units).rescale(
            self._units).magnitude)
        return self._controller._newport_cmd("FE",target=self.axis_id,params=[error_threshold])

    @property
    def current(self):
        """
        Get and set the current

        :units: A
        :param current: Set the current
        :type: `~quantities.Quantity` or `float`
        """
        return assume_units(float(self._controller._newport_cmd("QI?",target=self.axis_id)),
                pq.A)
    @current.setter
    def current(self, current):
        current = float(assume_units(current,pq.A).rescale(
            pq.A).magnitude)
        return self._controller._newport_cmd("QI",target=self.axis_id,params=[current])

    @property
    def voltage(self):
        """
        Get and set the current

        :units: A
        :param voltage: Set the voltage
        :type: `~quantities.Quantity` or `float`
        """
        return assume_units(float(self._controller._newport_cmd("QV?",target=self.axis_id)),
                self.V)
    @voltage.setter
    def voltage(self, voltage):
        voltage = float(assume_units(voltage,pq.V).rescale(
            pq.V).magnitude)
        return self._controller._newport_cmd("QV",target=self.axis_id,params=[voltage])
   
    @property    
    def motor_type(self):
        """
        Get and set the motor type 
        * 0 = undefined
        * 1 = DC Servo 
        * 2 = Stepper motor
        * 3 = commutated stepper motor
        * 4 = commutated brushless servo motor

        :param int motor_type: Type of motor
        """
        return NewportESP301MotorType( int(self._controller._newport_cmd("QM?",target=self._axis_id)) )
    @motor_type.setter
    def motor_type(self, motor_type):
        self._controller._newport_cmd("QM",target=self._axis_id,params=[int(motor_type)])

    @property    
    def feedback_configuration(self):
        """
        Get and set Feedback configuration        

        :param int feedback_configuration: 
        """
        return int(self._controller._newport_cmd("ZB?",target=self._axis_id)[:-2],16)
    @feedback_configuration.setter
    def feedback_configuration(self, feedback_configuration):
        self._controller._newport_cmd("ZB",target=self._axis_id,params=[int(feedback_configuration)])

    @property    
    def position_display_resolution(self):
        """
        Get and set the position display resolution

        :param int position_display_resolution: 
        """
        return int(self._controller._newport_cmd("FP?",target=self._axis_id))
    @position_display_resolution.setter
    def position_display_resolution(self, position_display_resolution):
        self._controller._newport_cmd("FP",target=self._axis_id,params=[int(position_display_resolution)])    
    
    @property    
    def trajectory(self):
        """
        Get and set the trajectory

        :param int trajectory: 
        """
        return int(self._controller._newport_cmd("TJ?",target=self._axis_id))
    @trajectory.setter
    def trajectory(self, trajectory):
        self._controller._newport_cmd("TJ",target=self._axis_id,params=[int(trajectory)])

    @property    
    def microstep_factor(self):
        """
        Get and set the microstep_factor

        :param int microstep_factor: 
        """
        return int(self._controller._newport_cmd("QS?",target=self._axis_id))
    @microstep_factor.setter
    def microstep_factor(self, microstep_factor):

        factor = int(microstep_factor)
        if factor >= 1 and factor <= 250 :
            self._controller._newport_cmd("QS",target=self._axis_id,params=[factor])
        else:
            raise ValueError("Microstep factor must be between 1 and 250")

    @property    
    def hardware_limit_configuration(self):
        """
        Get and set the hardware_limit_configuration

        :param int hardware_limit_configuration: 
        """
        return int(self._controller._newport_cmd("ZH?",target=self._axis_id)[:-2])
    @hardware_limit_configuration.setter
    def hardware_limit_configuration(self, hardware_limit_configuration):
        self._controller._newport_cmd("ZH",target=self._axis_id,params=[int(hardware_limit_configuration)])

    @property    
    def acceleration_feed_forward(self):
        """
        Get and set the acceleration_feed_forward

        :param int acceleration_feed_forward: 
        """
        return float(self._controller._newport_cmd("AF?",target=self._axis_id))
    @acceleration_feed_forward.setter
    def acceleration_feed_forward(self, acceleration_feed_forward):
        self._controller._newport_cmd("AF",target=self._axis_id,params=[float(acceleration_feed_forward)])

    @property    
    def proportional_gain(self):
        """
        Get and set the proportional_gain

        :param float proportional_gain: 
        """
        return float(self._controller._newport_cmd("KP?",target=self._axis_id)[:-1])
    @proportional_gain.setter
    def proportional_gain(self, proportional_gain):
        self._controller._newport_cmd("KP",target=self._axis_id,params=[float(proportional_gain)])

    @property    
    def derivative_gain(self):
        """
        Get and set the derivative_gain

        :param float derivative_gain: 
        """
        return float(self._controller._newport_cmd("KD?",target=self._axis_id))
    @derivative_gain.setter
    def derivative_gain(self, derivative_gain):
        self._controller._newport_cmd("KD",target=self._axis_id,params=[float(derivative_gain)])

    @property    
    def integral_gain(self):
        """
        Get and set the integral_gain

        :param float integral_gain: 
        """
        return float(self._controller._newport_cmd("KI?",target=self._axis_id))
    @integral_gain.setter
    def integral_gain(self, integral_gain):
        self._controller._newport_cmd("KI",target=self._axis_id,params=[float(integral_gain)])

    @property    
    def integral_saturation_gain(self):
        """
        Get and set the integral_saturation_gain

        :param float integral_saturation_gain: 
        """
        return float(self._controller._newport_cmd("KS?",target=self._axis_id))
    @integral_saturation_gain.setter
    def integral_saturation_gain(self,integral_saturation_gain):
        self._controller._newport_cmd("KS",target=self._axis_id,params=[float(integral_saturation_gain)])

    @property
    def encoder_position(self):
        with self._units_of(NewportESP301Units.encoder_step):
            return self.position
        

    ## MOVEMENT METHODS ##
    def search_for_home(self,
            search_mode=NewportESP301HomeSearchMode.zero_position_count.value
        ):
        """
        Searches this axis only
        for home using the method specified by ``search_mode``.

        :param NewportESP301HomeSearchMode search_mode: Method to detect when
            Home has been found.
        """
        self._controller._home(axis=self.axis_id, search_mode=search_mode)

    def move(self, position, absolute=True,wait=False,block=False):
        """
        :param position: Position to set move to along this axis.
        :type position: `float` or :class:`~quantities.Quantity`
        :param bool absolute: If `True`, the position ``pos`` is
            interpreted as relative to the zero-point of the encoder.
            If `False`, ``pos`` is interpreted
            as relative to the current position of this axis.
        :param bool wait: If True, will tell axis to not execute other
            commands until movement is finished
        :param bool block: If True, will block code until movement is finished
        """
        position = float(assume_units(position,self._units).rescale(
            self._units).magnitude)
        # TODO: handle unit conversions here.
        if absolute:
            self._controller._newport_cmd("PA", params=[position], target=self.axis_id)
        else:
            self._controller._newport_cmd("PR", params=[position], target=self.axis_id)
        
        if wait:
            self.wait_for_position(position)
            if block:
                sleep(0.003)
                mot = self.is_motion_done
                while not mot:                    
                    mot = self.is_motion_done


    def move_to_hardware_limit(self):
        """
        move to hardware travel limit
        """
        self._controller._newport_cmd("MT", target=self.axis_id)

    def move_indefinitely(self):
        """
        Move until told to stop
        """
        self._controller._newport_cmd("MV", target=self.axis_id)

    def abort_motion(self):
        """
        Abort motion
        """
        self._controller._newport_cmd("AB", target=self.axis_id)
        
    def wait_for_stop(self):
        """ 
        Waits for axis motion to stop before next command is executed
        """
        self._controller._newport_cmd("WS",target=self.axis_id)

    def stop_motion(self):
        """
        Stop all motion on axis. With programmed deceleration rate
        """
        try:
            self._controller._newport_cmd("ST",target=self.axis_id)
        except NewportError, e:
            print e

    def wait_for_position(self,position):
        """
        Wait for axis to reach position before executing next command

        :param position: Position to wait for on axis

        :type position: float or :class:`~quantities.Quantity`
        """
        position = float(assume_units(position,self._units).rescale(
            self._units).magnitude)
        self._controller._newport_cmd("WP",target=self.axis_id,params=[position])
    
    def wait_for_motion(self, poll_interval=0.01, max_wait=None):
        """
        Blocks until all movement along this axis is complete, as reported
        by `~NewportESP301Axis.is_motion_done`.

        :param float poll_interval: How long (in seconds) to sleep between
            checking if the motion is complete.
        :param float max_wait: Maximum amount of time to wait before
            raising a `IOError`. If `None`, this method will wait
            indefinitely.
        """
        # FIXME: make sure that the controller is not in
        #        programming mode, or else this might not work.
        #        In programming mode, the "WS" command should be
        #        sent instead, and the two parameters to this method should
        #        be ignored.
        poll_interval = float(assume_units(position,pq.s).rescale(
            pq.s).magnitude)
        max_wait = float(assume_units(position,pq.s).rescale(
            pq.s).magnitude)
        tic = time()
        while True:
            if self.is_motion_done:
                return
            else:
                if max_wait is None or (time() - tic) < max_wait:
                    sleep(poll_interval)
                else:
                    raise IOError("Timed out waiting for motion to finish.")
                    
    def enable(self):
        """
        Turns motor axis on.
        """
        self._controller._newport_cmd("MO",target=self._axis_id)

    def disable(self):
        """
        Turns motor axis off.
        """
        self._controller._newport_cmd("MF",target=self._axis_id)
        
    def setup_axis(self,**kwargs):
        """
        Setup a non-newport DC servo motor stage. Necessary parameters are. 

        * 'motor_type' = type of motor see 'QM' in Newport documentation
        * 'current' = motor maximum current (A)
        * 'voltage' = motor voltage (V)
        * 'units' = set units (see NewportESP301Units)(U)
        * 'resolution' = value of encoder step in terms of (U)
        * 'max_velocity' = maximum velocity (U/s)
        * 'max_working_velocity' =  maximum working velocity (U/s)
        * 'homing_velocity' = homing speed (U/s)
        * 'jog_high_velocity' = jog high speed (U/s)
        * 'jog_low_velocity' = jog low speed (U/s)
        * 'max_acceleration' = maximum acceleration (U/s^2)
        * 'acceleration' = acceleration (U/s^2)
        * 'deceleration' = set deceleration (U/s^2)
        * 'error_threshold' = set error threshold (U)
        * 'proportional_gain' = PID proportional gain (optional)
        * 'derivative_gain' = PID derivative gain (optional)
        * 'interal_gain' = PID internal gain (optional)
        * 'integral_saturation_gain' = PID integral saturation (optional)
        * 'trajectory' = trajectory mode (optional)
        * 'position_display_resolution' (U per step)
        * 'feedback_configuration'
        * 'full_step_resolution'  = (U per step)
        * 'home' = (U)
        * 'acceleration_feed_forward' = bewtween 0 to 2e9
        * 'reduce_motor_torque' =  (time(ms),percentage)
        """
        
            # set motor to DC servo
        if 'motor_type' in kwargs:
            self.motor_type = kwargs['motor_type']
        #set feedback configuration
        if 'feedback_configuration' in kwargs:
            self.feedback_configuration = kwargs['feedback_configuration']
        #set full step resolution
        if 'full_step_resolution' in kwargs:
            self.full_step_resolution = kwargs['full_step_resolution']
        #set full step resolution
        if 'position_display_resolution' in kwargs:
            self.position_display_resolution = kwargs['position_display_resolution']
        #set current              
        if 'current' in kwargs:
            self.current= kwargs['current']
        #set voltage
        if 'voltage' in kwargs:
            self.voltage =  kwargs['voltage']
        # set units 
        if 'units' in kwargs:
            units = int(kwargs['units'])
            self.units = units 
        #set resolution 
        if 'encoder_resolution' in kwargs:
            self.encoder_resolution = kwargs['encoder_resolution'] 
        #set max acceleration 
        if 'max_acceleration' in kwargs:
            self.max_acceleration= kwargs['max_acceleration']

        # set maximum velocity 
        if 'max_velocity' in kwargs:
            self.max_velocity = kwargs['max_velocity']       

        #max base velocity for stepper motors
        if 'max_base_velocity' in kwargs: 
            self.max_base_velocity = kwargs['max_base_velocity']     
        
        
        #set homing speed 
        if 'homing_velocity' in kwargs:
            self.homing_velocity = kwargs['homing_velocity']
        #set jog high speed
        if 'jog_high_velocity' in kwargs:
            self.jog_high_velocity = kwargs['jog_high_velocity']
        #set jog low speed 
        if 'jog_low_velocity' in kwargs:
            self.jog_low_velocity = kwargs['jog_low_velocity']       
        
        #set acceleration 
        if 'acceleration' in kwargs:
            self.acceleration = kwargs['acceleration']
        #velocity
        if 'velocity' in kwargs:
            self.velocity = kwargs['velocity']
        #set deceleration
        if 'deceleration' in kwargs:
            self.deceleration = kwargs['deceleration']
        if 'estop_deceleration' in kwargs:
            self.estop_deceleration = kwargs['estop_deceleration']
        if 'jerk' in kwargs:
            self.jerk = kwargs['jerk']
        #set error threshold
        if 'error_threshold' in kwargs:
            self.error_threshold = kwargs['error_threshold']
        if 'proportional_gain' in kwargs:
            self.proportional_gain = kwargs['proportional_gain']
        if 'derivative_gain' in kwargs:
            self.derivative_gain = kwargs['derivative_gain']
        if 'integral_gain' in kwargs:
            self.integral_gain = kwargs['integral_gain']
        if 'integral_saturation_gain' in kwargs:
            self.integral_saturation_gain = ['integral_saturation_gain']
        if 'home' in kwargs:
            self.home = kwargs['home']
        if 'microstep_factor' in kwargs:
            self.microstep_factor = kwargs['microstep_factor']
        if 'acceleration_feed_forward' in kwargs:
            self.acceleration_feed_forward = kwargs['acceleration_feed_forward']
        if 'trajectory' in kwargs:
            self.trajectory = kwargs['trajectory']
        if 'hardware_limit_configuration' in kwargs:
            self.hardware_limit_configuration = kwargs['hardware_limit_configuration']            
        if 'reduce_motor_torque_time' in kwargs and 'reduce_motor_torque_percentage' in kwargs:
            time = kwargs['reduce_motor_torque_time']
            time= int(assume_units(time,pq.ms).rescale(
            pq.ms).magnitude)
            if not (time >=0 and time <=60000):
                raise ValueError("Time must be between 0 and 60000 ms")
            percentage = kwargs['reduce_motor_torque_percentage']
            percentage = int(assume_units(percentage,pq.percent).rescale(
                pq.percent).magnitude)
            if not (percentage >=0 and percentage <=100):
                raise ValueError("Time must be between 0 and 60000 ms")
            self._controller._newport_cmd("QR",target=self._axis_id,params=[time,percentage])

        #update motor configuration
        self._controller._newport_cmd("UF",target=self._axis_id)
        self._controller._newport_cmd("QD",target=self._axis_id)
        #save configuration
        self._controller._newport_cmd("SM")
        return self.read_setup()

    

    def read_setup(self):
        """
        Returns dictionary containing: 
            'units'
            'motor_type'
            'feedback_configuration'
            'full_step_resolution'
            'position_display_resolution'
            'current'
            'max_velocity'
            'encoder_resolution'
            'acceleration'
            'deceleration'
            'velocity'
            'max_acceleration'
            'homing_velocity'
            'jog_high_velocity'
            'jog_low_velocity'
            'estop_deceleration'
            'jerk'        
            'proportional_gain'
            'derivative_gain'
            'integral_gain'
            'integral_saturation_gain'
            'home'
            'microstep_factor'
            'acceleration_feed_forward'
            'trajectory'
            'hardware_limit_configuration'

        :rtype: dict of `quantities.Quantity`, float and int
        """
        
        config = {}        
        config['units'] = self.units
        config['motor_type'] = self.motor_type
        config['feedback_configuration'] = self.feedback_configuration
        config['full_step_resolution'] = self.full_step_resolution
        config['position_display_resolution'] = self.position_display_resolution
        config['current'] = self.current
        config['max_velocity'] = self.max_velocity
        config['encoder_resolution'] = self.encoder_resolution
        config['acceleration'] = self.acceleration
        config['deceleration'] = self.deceleration
        config['velocity'] = self.velocity
        config['max_acceleration'] = self.max_acceleration            
        config['homing_velocity'] = self.homing_velocity
        config['jog_high_velocity'] = self.jog_high_velocity
        config['jog_low_velocity'] = self.jog_low_velocity
        config['estop_deceleration'] = self.estop_deceleration
        config['jerk'] = self.jerk
        #config['error_threshold'] = self.error_threshold
        config['proportional_gain'] = self.proportional_gain
        config['derivative_gain'] = self.derivative_gain
        config['integral_gain'] = self.integral_gain
        config['integral_saturation_gain'] = self.integral_saturation_gain
        config['home'] = self.home
        config['microstep_factor'] = self.microstep_factor
        config['acceleration_feed_forward'] = self.acceleration_feed_forward
        config['trajectory'] = self.trajectory
        config['hardware_limit_configuration'] = self.hardware_limit_configuration
        return config

    def get_status(self):
        """
        Returns Dictionary containing values:
            'units'
            'position'
            'desired_position'
            'desired_velocity'
            'is_motion_done'

        :rtype: dict
        """
        status = {}
        status['units'] = self.units 
        status['position'] = self.position 
        status['desired_position'] = self.desired_position
        status['desired_velocity'] = self.desired_velocity
        status['is_motion_done'] = self.is_motion_done

        return status
        
    # FIXME: make these two methods private.
        
    def get_pq_unit(self, num):
        """
        Gets the units for the specified axis.

        :units: The units for the attached axis 
        :type num: int
        """
        return NewportESP301Axis._unit_dict[num]

    def get_unit_num(self, quantity):
        """
        Gets the integer label used by the Newport ESP 301 corresponding to a
        given `~quantities.Quantity`.

        :param quantities.Quantity quantity: Units to return a label for.
        
        :return int:
        """
        for num, quant in self._unit_dict.iteritems():
            if quant == quantity:
                return num
                
        raise KeyError("{0} is not a valid unit for Newport Axis".format(quantity))

