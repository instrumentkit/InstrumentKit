#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# newportesp301.py: Controller for the Newport ESP-301 motor controller.
##
# © 2013 Steven Casagrande (scasagrande@galvant.ca).
#
# This file is a part of the GPIBUSB adapter project.
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

import quantities as pq

from instruments.abstract_instruments import Instrument

## CLASSES #####################################################################

class NewportError(IOError):
    def __init__(self, msg, timestamp=None, errcode=None):
        super(NewportError, self).__init__(msg)
        self._timestamp = timestamp
        if errcode is not None:
            # Break the error code into an axis number
            # and the rest of the code.
            self._errcode = errcode % 100
            self._axis = errcode // 100
            if self._axis == 0: self._axis = None
        else:
            self._errcode = None
            self._axis = None

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def errcode(self):
        return self._errcode

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
    controller using the protocol documented in the `user's guide`_

    .. _user's guide: http://assets.newport.com/webDocuments-EN/images/14294.pdf
    """
                 
    # No __init__ needed.

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
        """
        
        return _AxisList(self)

    ## LOW-LEVEL COMMAND METHODS ##

    def _newport_cmd(self, cmd, *params, axis=None, errcheck=True):
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
        if isinstance(axis, NewportESP301Axis):
            axis = axis._axis_id
            
        raw_cmd = "{axis}{cmd}{params}".format(
            axis=axis if axis is not None else "",
            cmd=cmd.upper(),
            params=",".join(map(str, params))
        )
        
        if "?" in cmd:
            query_resp = self.query(raw_cmd)
        else:
            self.sendcmd(raw_cmd)
            
        if errcheck:
            err_resp = self.query('TB?')
            code, timestamp, msg = err_resp.split(",")
            if code != 0:
                raise NewportError(
                    "Newport controller reports error with message {}.".format(msg),
                    timestamp, code
                )

        # This works because "return None" is equivalent to "return".
        return query_resp

    ## SPECIFIC COMMANDS ##

    def reset(self):
        self._newport_cmd("RS")

    
        
class NewportESP301Axis(object):
    """
    Encapsulates communication concerning a single axis
    of an ESP-301 controller.
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
    def acceleration(self):
        return self._controller._newport_cmd("AC?", axis=self)

    @property
    def deacceleration(self):
        return self._controller._newport_cmd("AG?", axis=self)

    @property
    def velocity(self):
        return self._controller._newport_cmd("VA?", axis=self)

    @property
    def max_velocity(self):
        return self._controller._newport_cmd("VU?", axis=self)
    

    ## MOVEMENT METHODS ##

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
        self.controller._newport_cmd("PA", pos, axis=self)
