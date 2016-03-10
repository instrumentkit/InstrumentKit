#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides common error handling for Newport devices.
"""

# IMPORTS ####################################################################

from __future__ import absolute_import
from __future__ import division

import datetime

# CLASSES ####################################################################


class NewportError(IOError):
    """
    Raised in response to an error with a Newport-brand instrument.
    """
    start_time = datetime.datetime.now()

    # Dict Containing all possible errors.
    # Uses strings for keys in order to handle axis
    messageDict = {
        '0': "NO ERROR DETECTED",
        '1': "PCI COMMUNICATION TIME-OUT",
        '2': "Reserved for future use",
        '3': "Reserved for future use",
        '4': "EMERGENCY SOP ACTIVATED",
        '5': "Reserved for future use",
        '6': "COMMAND DOES NOT EXIST",
        '7': "PARAMETER OUT OF RANGE",
        '8': "CABLE INTERLOCK ERROR",
        '9': "AXIS NUMBER OUT OF RANGE",
        '10': "Reserved for future use",
        '11': "Reserved for future use",
        '12': "Reserved for future use",
        '13': "GROUP NUMBER MISSING",
        '14': "GROUP NUMBER OUT OF RANGE",
        '15': "GROUP NUMBER NOT ASSIGNED",
        '16': "GROUP NUMBER ALREADY ASSIGNED",
        '17': "GROUP AXIS OUT OF RANGE",
        '18': "GROUP AXIS ALREADY ASSIGNED",
        '19': "GROUP AXIS DUPLICATED",
        '20': "DATA ACQUISITION IS BUSY",
        '21': "DATA ACQUISITION SETUP ERROR",
        '22': "DATA ACQUISITION NOT ENABLED",
        '23': "SERVO CYCLE (400 µS) TICK FAILURE",
        '24': "Reserved for future use",
        '25': "DOWNLOAD IN PROGRESS",
        '26': "STORED PROGRAM NOT STARTEDL",
        '27': "COMMAND NOT ALLOWEDL",
        '28': "STORED PROGRAM FLASH AREA FULL",
        '29': "GROUP PARAMETER MISSING",
        '30': "GROUP PARAMETER OUT OF RANGE",
        '31': "GROUP MAXIMUM VELOCITY EXCEEDED",
        '32': "GROUP MAXIMUM ACCELERATION EXCEEDED",
        '33': "GROUP MAXIMUM DECELERATION EXCEEDED",
        '34': " GROUP MOVE NOT ALLOWED DURING MOTION",
        '35': "PROGRAM NOT FOUND",
        '36': "Reserved for future use",
        '37': "AXIS NUMBER MISSING",
        '38': "COMMAND PARAMETER MISSING",
        '39': "PROGRAM LABEL NOT FOUND",
        '40': "LAST COMMAND CANNOT BE REPEATED",
        '41': "MAX NUMBER OF LABELS PER PROGRAM EXCEEDED",
        'x00': "MOTOR TYPE NOT DEFINED",
        'x01': "PARAMETER OUT OF RANGE",
        'x02': "AMPLIFIER FAULT DETECTED",
        'x03': "FOLLOWING ERROR THRESHOLD EXCEEDED",
        'x04': "POSITIVE HARDWARE LIMIT DETECTED",
        'x05': "NEGATIVE HARDWARE LIMIT DETECTED",
        'x06': "POSITIVE SOFTWARE LIMIT DETECTED",
        'x07': "NEGATIVE SOFTWARE LIMIT DETECTED",
        'x08': "MOTOR / STAGE NOT CONNECTED",
        'x09': "FEEDBACK SIGNAL FAULT DETECTED",
        'x10': "MAXIMUM VELOCITY EXCEEDED",
        'x11': "MAXIMUM ACCELERATION EXCEEDED",
        'x12': "Reserved for future use",
        'x13': "MOTOR NOT ENABLED",
        'x14': "Reserved for future use",
        'x15': "MAXIMUM JERK EXCEEDED",
        'x16': "MAXIMUM DAC OFFSET EXCEEDED",
        'x17': "ESP CRITICAL SETTINGS ARE PROTECTED",
        'x18': "ESP STAGE DEVICE ERROR",
        'x19': "ESP STAGE DATA INVALID",
        'x20': "HOMING ABORTED",
        'x21': "MOTOR CURRENT NOT DEFINED",
        'x22': "UNIDRIVE COMMUNICATIONS ERROR",
        'x23': "UNIDRIVE NOT DETECTED",
        'x24': "SPEED OUT OF RANGE",
        'x25': "INVALID TRAJECTORY MASTER AXIS",
        'x26': "PARAMETER CHARGE NOT ALLOWED",
        'x27': "INVALID TRAJECTORY MODE FOR HOMING",
        'x28': "INVALID ENCODER STEP RATIO",
        'x29': "DIGITAL I/O INTERLOCK DETECTED",
        'x30': "COMMAND NOT ALLOWED DURING HOMING",
        'x31': "COMMAND NOT ALLOWED DUE TO GROUP",
        'x32': "INVALID TRAJECTORY MODE FOR MOVING"
    }

    def __init__(self, errcode=None, timestamp=None):

        if timestamp is None:
            self._timestamp = datetime.datetime.now() - NewportError.start_time
        else:
            self._timestamp = datetime.timedelta(
                seconds=(timestamp * 400E-6))

        if errcode is not None:
            # Break the error code into an axis number
            # and the rest of the code.
            self._errcode = int(errcode) % 100
            self._axis = errcode // 100
            if self._axis == 0:
                self._axis = None
                error_message = self.get_message(str(errcode))
                error = "Newport Error: {0}. Error Message: {1}. " \
                        "At time : {2}".format(str(errcode),
                                               error_message,
                                               self._timestamp)
                super(NewportError, self).__init__(error)
            else:
                error_message = self.get_message('x{0}'.format(self._errcode))
                error = "Newport Error: {0}. Axis: {1}. " \
                        "Error Message: {2}. " \
                        "At time : {3}".format(str(self._errcode),
                                               self._axis,
                                               error_message,
                                               self._timestamp)
                super(NewportError, self).__init__(error)

        else:
            self._errcode = None
            self._axis = None
            super(NewportError, self).__init__("")

    # PRIVATE METHODS ##

    @staticmethod
    def get_message(code):
        """
        Returns the error string for a given error code

        :param str code: Error code as returned by instrument
        :return: Full error code string
        :rtype: `str`
        """
        return NewportError.messageDict.get(code, "Error code not recognised")

    # PROPERTIES ##

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
