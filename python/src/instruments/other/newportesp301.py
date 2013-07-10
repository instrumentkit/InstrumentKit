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

from datetime import datetime

from flufl.enum import IntEnum

from contextlib import contextmanager

import quantities as pq

from instruments.abstract_instruments import Instrument

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
    encoder_step= 0
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


## CLASSES #####################################################################

class NewportError(IOError):
    """
    Raised in response to an error with a Newport-brand instrument.
    """
    #Dict Containing all possible errors.Uses strings for keys in order to handle axis
    #Outside self definition so not rebuilt for everytime
    messageDict={
    '0' : "NO ERROR DETECTED" ,
    '1' : "PCI COMMUNICATION TIME-OUT",
    '2' : "Reserved for future use" ,
    '3' : "Reserved for future use" ,
    '4' : "EMERGENCY SOP ACTIVATED",
    '5' : "Reserved for future use" ,
    '6' : "COMMAND DOES NOT EXIST" ,
    '7' : "PARAMETER OUT OF RANGE",
    '8' : "CABLE INTERLOCK ERROR",
    '9' : "AXIS NUMBER OUT OF RANGE",
    '10' : "Reserved for future use" ,
    '11' : "Reserved for future use" ,
    '12' : "Reserved for future use" ,
    '13' : "GROUP NUMBER MISSING" ,
    '14' : "GROUP NUMBER OUT OF RANGE" ,
    '15' : "GROUP NUMBER NOT ASSIGNED" ,
    '16' : "GROUP NUMBER ALREADY ASSIGNED" ,
    '17' : "GROUP AXIS OUT OF RANGE" ,
    '18' : "GROUP AXIS ALREADY ASSIGNED" ,
    '19' : "GROUP AXIS DUPLICATED",
    '20' : "DATA ACQUISITION IS BUSY" ,
    '21' : "DATA ACQUISITION SETUP ERROR",
    '22' : "DATA ACQUISITION NOT ENABLED",
    '23' : "SERVO CYCLE (400 µS) TICK FAILURE",
    '24' : "Reserved for future use" ,
    '25' : "DOWNLOAD IN PROGRESS",  
    '26' : "STORED PROGRAM NOT STARTEDL",
    '27' : "COMMAND NOT ALLOWEDL",
    '28' : "STORED PROGRAM FLASH AREA FULL",
    '29' : "GROUP PARAMETER MISSING" ,
    '30' : "GROUP PARAMETER OUT OF RANGE",
    '31' : "GROUP MAXIMUM VELOCITY EXCEEDED",
    '32' : "GROUP MAXIMUM ACCELERATION EXCEEDED",
    '33' : "GROUP MAXIMUM DECELERATION EXCEEDED",
    '34' : " GROUP MOVE NOT ALLOWED DURING MOTION",
    '35' : "PROGRAM NOT FOUND",
    '36' : "Reserved for future use" ,
    '37' : "AXIS NUMBER MISSING" , 
    '38' : "COMMAND PARAMETER MISSING",
    '39' : "PROGRAM LABEL NOT FOUND",
    '40' : "LAST COMMAND CANNOT BE REPEATED",
    '41' : "MAX NUMBER OF LABELS PER PROGRAM EXCEEDED",
    'x00' : "MOTOR TYPE NOT DEFINED",
    'x01' : "PARAMETER OUT OF RANGE",
    'x02' : "AMPLIFIER FAULT DETECTED",
    'x03' : "FOLLOWING ERROR THRESHOLD EXCEEDED",
    'x04' : "POSITIVE HARDWARE LIMIT DETECTED",
    'x05' : "NEGATIVE HARDWARE LIMIT DETECTED",
    'x06' : "POSITIVE SOFTWARE LIMIT DETECTED",
    'x07' : "NEGATIVE SOFTWARE LIMIT DETECTED",
    'x08' : "MOTOR / STAGE NOT CONNECTED" ,
    'x09' : "FEEDBACK SIGNAL FAULT DETECTED",
    'x10' : "MAXIMUM VELOCITY EXCEEDED",
    'x11' : "MAXIMUM ACCELERATION EXCEEDED" ,
    'x12' : "Reserved for future use",
    'x13' : "MOTOR NOT ENABLED",
    'x14' : "Reserved for future use" ,
    'x15' : "MAXIMUM JERK EXCEEDED",
    'x16' : "MAXIMUM DAC OFFSET EXCEEDED",
    'x17' : "ESP CRITICAL SETTINGS ARE PROTECTED" ,
    'x18' : "ESP STAGE DEVICE ERROR",
    'x19' : "ESP STAGE DATA INVALID",
    'x20' : "HOMING ABORTED",
    'x21' : "MOTOR CURRENT NOT DEFINED",
    'x22' : "UNIDRIVE COMMUNICATIONS ERROR",
    'x23' : "UNIDRIVE NOT DETECTED",
    'x24' : "SPEED OUT OF RANGE",
    'x25' : "INVALID TRAJECTORY MASTER AXIS",
    'x26' : "PARAMETER CHARGE NOT ALLOWED",
    'x27' : "INVALID TRAJECTORY MODE FOR HOMING",
    'x28' : "INVALID ENCODER STEP RATIO",
    'x29' : "DIGITAL I/O INTERLOCK DETECTED",
    'x30' : "COMMAND NOT ALLOWED DURING HOMING",
    'x31' : "COMMAND NOT ALLOWED DUE TO GROUP" ,
    'x32' : "INVALID TRAJECTORY MODE FOR MOVING"
    }
    def __init__(self, errcode=None):

        
        self._timestamp = datetime.now()
        if errcode is not None:
            # Break the error code into an axis number
            # and the rest of the code.
            self._errcode = errcode % 100
            self._axis = errcode // 100 
            if self._axis == 0: 
                self._axis = None
                error_message = self.getMessage(str(errcode))
                error = "Newport Error: {0}. Error Message: {1}".format(str(errcode),error_message)
                super(NewportError, self).__init__(error)
            else:                
                error_message = self.getMessage('x{0}'.format(self._errcode))
                error = "Newport Error: {0}. Axis: {1}. Error Message: {2}".format(str(self._errcode),self._axis,error_message)
                super(NewportError, self).__init__(error)

        else:
            self._errcode = None
            self._axis = None
            super(NewportError, self).__init__("")


    @property
    def timestamp(self):
        """
        Geturns the timestamp reported by the device as the time
        at which this error occured.

        :type: `datetime`
        """
        return self._timestamp

    @property
    def errcode(self):
        """
        Gets the error code reported by the device.
        
        :type: `int`
        """
        return self._errcode

    @property
    def axis(self):
        """
        Gets the axis with which this error is concerned, or
        `None` if the error was not associated with any particlar
        axis.

        :type: `int`
        """
        return self._axis

    def getMessage(self,code):
        return NewportError.messageDict.get(code,"Error code not recognised")


class _AxisList(object):
    """
    Used to make expressions like ``NewportESP301.axis[idx]``
    work as expected.
    """
    def __init__(self, controller):
        self._controller = controller
    def __getitem__(self, idx):
        # FIXME: need to check MAX AXES, but the docs are not clear
        #        on how to do this. Once that's done, expose it as len.
        if idx < 0:
            raise IndexError("Negative axis indices are not allowed.")
        # Change one-based indices to zero-based for easier
        # Python programming.
        return NewportESP301Axis(self._controller, idx + 1)

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

    def reset(self,errcheck=True):
        """
        Causes the device to perform a hardware reset. Note that
        this method is only effective if the watchdog timer is enabled
        by the physical jumpers on the ESP-301. Please see the `user's guide`_
        for more information.
        """
        self._newport_cmd("RS",errcheck=errcheck)

    ## USER PROGRAMS ##

    @contextmanager
    def define_program(self, program_id):
        """
        Erases any existing programs with a given program ID
        and instructs the device to record the commands within this
        ``with`` block to be saved as a program with that ID.

        For instance::

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

        Example 
        --------
        .. code-block:: python
           with self.execute_bulk_command():
                ... execute commands as normal
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

    def __init__(self, controller, axis_id):
        if not isinstance(controller, NewportESP301):
            raise TypeError("Axis must be controlled by a Newport ESP-301 motor controller.")

        # TODO: check axis_id
        
        self._controller = controller
        self._axis_id = axis_id

    ## PROPERTIES ##
    # TODO: handle units, implement setters.
    @property
    def axis_id(self):
        """
        Get axis number of Newport Controller

        :type: `int`
        """
        return axis_id
    
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

        
        :type:`float` 
        :return: acceleration in units/s^2
        """
        return float(self._controller._newport_cmd("AC?", target=self.axis_id))    
    @acceleration.setter
    def acceleration(self,accel):
        """
        Sets acceleration in units/s^2
        
        :param float accel: acceleration in units/s^2

        """
        return self._controller._newport_cmd("AC",target=self.axis_id,params=[accel])
   
    @property
    def deceleration(self):
        """
        Gets deceleration

        :return: deceleration in units/s^2
        :type: `float`
        """
        return float(self._controller._newport_cmd("AG?", target=self.axis_id))
    @deceleration.setter
    def deceleration(self,decel):
        """
        Sets deceleration

        :param float decel: deceleration in units/s^2
        """
        return self._controller._newport_cmd("AG",target=self.axis_id,params=[deaccel])
    
    @property
    def velocity(self):
        """
        Gets velocity

        :return: velocity in units/s
        :type: `float`
        """
        return float(self._controller._newport_cmd("VA?", target=self.axis_id))
    @velocity.setter
    def velocity(self,velocity):
        """
        Sets velocity

        :param float velocity: velocity in units/s
        """
        return self._controller._newport_cmd("VA",target=self.axis_id,params=[velocity])

    @property
    def max_velocity(self):
        """
        Get the maximum velocity

        :return: velocity in units/s
        :type: `float`
        """
        return float(self._controller._newport_cmd("VU?", target=self.axis_id))
    @max_velocity.setter
    def max_velocity(self,velocity):
         """
        Sets max velocity

        :param float velocity: velocity in units/s
        """
        return self._controller._newport_cmd("VU", target=self.axis_id,params=[velocity])
    
    @property
    def max_acceleration(self):
        """
        Get max acceleration

        :type:`float` 
        :return: acceleration in units/s^2
        """
        return float(self._controller._newport_cmd("AU?", target=self.axis_id))
    @max_acceleration.setter
    def max_acceleration(self,accel):
         """
        Sets max acceleration

        :param float accel: acceleration in units/s^2
        """
        return self._controller._newport_cmd("AU",target=self.axis_id,params=[accel])

    # Max deacceleration is always the same as accelleration 
    @property
    def max_deceleration(self):
        """
        Get max deceleration

        :return: deceleration in units/s^2
        :type: `float`
        """
        return float(self.max_acceleration)
    @max_deceleration.setter
    def max_deacceleration(self,decel):
         """
        Sets max deceleration

        :param float decel: deceleration in units/s^2
        """
        return self.max_acceleration(deaccel)
    
    @property
    def position(self):
        """
        Gets real position on axis in units

        :return: position in units
        :type: `float`
        """
        return float(self._controller._newport_cmd("TP?", target=self.axis_id))
    
    @property
    def home(self):
        """
        Get home position

        :return: position in units
        :type: `float`
        """
        return float(self._controller._newport_cmd("DH?",target=self.axis_id))   
    #default should be 0 as that sets current position as home
    @home.setter
    def home(self,home=0):
         """
        Sets home position. Default position is current position which means 0

        :param float home: position in units
        """
        return self._controller._newport_cmd("DH",target=self.axis_id,params=[v])
    
    @property
    def units(self):
        """
        Get the units that all commands are in reference to. 


        :type: `int` 
        :return:=====  ============     
                Int      Unit      
                =====  ============ 
                1      encoder step  
                2      motor step
                3      millimeter
                4      micrometer
                5      inches
                6      milli-inches
                7      micro-inches
                8      degree
                9      radian
                10     milliradian
                11     microradian
                =====  ===========  
        """
        return int(self._controller._newport_cmd("SN?",target=self.axis_id))
    @units.setter
    def units(self,unit):
         """
        Set the units for all actions to be in reference to.            

        :param unit int:=====  ============     
                        Int      Unit      
                        =====  ============ 
                        1      encoder step  
                        2      motor step
                        3      millimeter
                        4      micrometer
                        5      inches
                        6      milli-inches
                        7      micro-inches
                        8      degree
                        9      radian
                        10     milliradian
                        11     microradian
                        =====  ===========  
        """
        return self._controller._newport_cmd("SN",target=self.axis_id,params=[int(value)])

    @property
    def encoder_resolution(self):
        """
        Get the resolution of the encode. Minimum units per step. 
        Encoder functionality must be enabled

        :return: units/step
        :type: `float`
        """
        return float(self._controller._newport_cmd("SU?",target=self.axis_id)) 
    @encoder_resolution.setter
    def encoder_resolution(self, resolution):
         """
        Sets encoder resolution. Resolution must be enabled

        :param float resolution: Sets units/step
        """
        return self._controller._newport_cmd("SU",target=self.axis_id,params=[value])
    
    @property
    def left_limit(self):
        """
        Get the left travel limit

        :return: units
        :type: `float`
        """
        return float(self._controller._newport_cmd("SL?",target=self.axis_id))
    @left_limit.setter
    def left_limit(self, limit):
         """
        Sets left travel limit

        :param float limit: Sets left limit in units
        """
        return self._controller._newport_cmd("SL",target=self.axis_id,params=[value])    

    @property
    def right_limit(self):
        """
        Get the right travel limit

        :return: units
        :type: `float`
        """
        return float(self._controller._newport_cmd("SR?",target=self.axis_id))
    @right_limit.setter
    def right_limit(self, value):
          """
        Sets right travel limit

        :param float limit: Sets right limit in units
        """
        return self._controller._newport_cmd("SR",target=self.axis_id,params=[value])
    
    @property
    def gear_ratio(self):
        """
        This command gets the master-slave reduction ratio for a slave axis. The 
        trajectory of the slave is the desired trajectory or actual position of the master 
        scaled by reduction ratio.

        :type: `float`
        """
        return self._controller._newport_cmd("GR?",target=self.axis_id)
    @gear_ratio.setter
    def gear_ratio(self, ratio):
         """
        This command sets the master-slave reduction ratio for a slave axis. The 
        trajectory of the slave is the desired trajectory or actual position of the master 
        scaled by reduction ratio.

        :param float ratio: Gearing ratio
        """
        return self._controller._newport_cmd("GR",target=self.axis_id,params=[value])



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
        self._home(axis=self.axis_id, search_mode=search_mode)

    def move(self, pos, absolute=True):
        """
        :param pos: Position to set move to along this axis.
        :type pos: `float` or `~quantities.Quantity`
        :param bool absolute: If `True`, the position ``pos`` is
            interpreted as relative to the zero-point of the encoder.
            If `False`, ``pos`` is interpreted
            as relative to the current position of this axis.
        """
        
        # TODO: handle unit conversions here.
        self._controller._newport_cmd("PA", params=[pos], target=self.axis_id)

    def wait_for_stop(self):
        """ 
        Waits for axis motion to stop before next command is executed
        """
        self._controller._newport_cmd("WS",target=self.axis_id)

    def stop_motion(self):
        """
        Stop all motion on axis. With programmed deceleration rate
        """
        self._controller._newport_cmd("ST",target=self.axis_id)

    def wait_for_position(self,position):
        """
        Wait for axis to reach position before executing next command
        """
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
        tic = time()
        while True:
            if self.is_motion_done:
                return
            else:
                if max_wait is None or (time() - tic) < max_wait:
                    sleep(poll_interval)
                else:
                    raise IOError("Timed out waiting for motion to finish.")



