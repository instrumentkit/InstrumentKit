#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Topmode Class contributed by Catherine Holloway
#

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division
from builtins import range

import quantities as pq
from flufl.enum import IntEnum

from instruments.toptica.toptica_utils import convert_toptica_boolean as ctbool
from instruments.toptica.toptica_utils import convert_toptica_datetime as ctdate

from instruments.abstract_instruments import Instrument
from instruments.util_fns import ProxyList

# CLASSES #####################################################################


class TopMode(Instrument):

    """
    The TopMode is a diode laser with active stabilization, produced by Toptica.
    The spec sheet is available here:

    http://www.toptica.com/fileadmin/user_upload/products/Diode_Lasers/Industrial_OEM/Single_Frequency/TopMode/toptica_BR_TopMode.pdf
    """
    class CharmStatus(IntEnum):
        un_initialized = 0
        in_progress = 1
        success = 2
        failure = 3

    class Laser(object):

        """
        Class representing a laser on the Toptica Topmode.

        .. warning:: This class should NOT be manually created by the user. It
        is designed to be initialized by the `Topmode` class.
        """

        def __init__(self, parent, idx):
            self.parent = parent
            self.name = "laser{}".format(idx + 1)

        @property
        def serial_number(self):
            return self.parent.reference(self.name + ":serial-number")

        @property
        def model(self):
            return self.parent.reference(self.name + ":model")

        @property
        def wavelength(self):
            return float(self.parent.reference(self.name + ":wavelength")) * pq.nm

        @property
        def production_date(self):
            return self.parent.reference(self.name + ":production-date")

        @property
        def enable(self):
            return ctbool(self.parent.reference(self.name + ":emission"))

        @enable.setter
        def enable(self, newval):
            if not isinstance(newval, bool):
                raise TypeError(
                    "Laser emmission must be a boolean, got: {}".format(newval))
            return self.parent.set(self.name + ":enable-emission", newval)

        @property
        def on_time(self):
            return float(self.parent.reference(self.name + ":ontime")) * pq.s

        @property
        def charm_status(self):
            response = int(self.parent.reference(self.name + ":health"))
            return (response >> 7) % 2 == 1

        @property
        def temperature_control_status(self):
            response = int(self.parent.reference(self.name + ":health"))
            return (response >> 5) % 2 == 1

        @property
        def current_control_status(self):
            response = int(self.parent.reference(self.name + ":health"))
            return (response >> 6) % 2 == 1

        @property
        def tec_status(self):
            return ctbool(self.parent.reference(self.name + ":tec:ready"))

        @property
        def intensity(self):
            """
            This parameter is unitless
            """
            return float(self.parent.reference(self.name + ":intensity"))

        @property
        def mode_hop(self):
            """
            Checks whether the laser has mode-hopped
            """
            return ctbool(self.parent.reference(self.name + ":charm:reg:mh-occured"))

        @property
        def lock_start(self):
            """
            Returns the date and time of the start of mode-locking
            """
            return ctdate(self.parent.reference(self.name + ":charm:reg:started"))

        @property
        def first_mode_hop_time(self):
            """
            Returns the date and time of the first mode hop
            """
            return ctdate(self.parent.reference(self.name + ":charm:reg:first-mh"))

        @property
        def latest_mode_hop_time(self):
            """
            Returns the date and time of the latest mode hop
            """
            return ctdate(self.parent.reference(self.name + ":charm:reg:latest-mh"))

        @property
        def correction_status(self):
            return TopMode.CharmStatus[int(self.parent.reference(self.name + ":charm:correction-status"))]

        def correction(self):
            """
            run the correction
            """
            if self.correction_status == TopMode.CharmStatus.un_initialized:
                self.parent.execute(
                    self.name + ":charm:start-correction-initial")
            else:
                self.parent.execute(self.name + ":charm:start-correction")

    def __init__(self, filelike):
        super(TopMode, self).__init__(filelike)
        self.prompt = ">"
        self.terminator = "\n"

    def _ack_expected(self, msg=""):
        return msg

    # TOPMODE CONTROL LANGUAGE #

    def execute(self, command):
        self.sendcmd("(exec '" + command + ")")

    def set(self, param, value):
        if isinstance(value, str):
            self.sendcmd("(param-set! '{} \"{}\")".format(param, value))
        elif isinstance(value, tuple) or isinstance(value, list):
            self.sendcmd(
                "(param-set! '{} '({}))".format(param, " ".join(value)))
        elif isinstance(value, bool):
            value = "t" if value else "f"
            self.sendcmd("(param-set! '{} #{})".format(param, value))

    def reference(self, param):
        return self.query("(param-ref '{})".format(param))

    def display(self, param):
        return self.query("(param-disp '{})".format(param))

    # PROPERTIES #

    @property
    def laser(self):
        return ProxyList(self, self.Laser, range(2))

    @property
    def enable(self):
        """
        is the laser lasing?
        :return:
        """
        return ctbool(self.reference("emission"))

    @enable.setter
    def enable(self, newval):
        if not isinstance(newval, bool):
            raise TypeError("Emission status must be a boolean, "
                            "got: {}".format(type(newval)))
        self.set("enable-emission", newval)

    @property
    def locked(self):
        """
        Is the key switch unlocked?
        :return:
        """
        return ctbool(self.reference("front-key-locked"))

    @property
    def interlock(self):
        """
        Is the interlock switch open?
        :return:
        """
        return ctbool(self.reference("interlock-open"))

    @property
    def fpga_status(self):
        """
        returns false on FPGA failure
        :return:
        """
        response = int(self.reference("system-health"))
        return False if response % 2 else True

    @property
    def temperature_status(self):
        """
        returns false if there is a temperature controller board failure
        :return:
        """
        response = int(self.reference("system-health"))
        return False if (response >> 1) % 2 else True

    @property
    def current_status(self):
        """
        returns false if there is a current controller board failure
        :return:
        """
        response = int(self.reference("system-health"))
        return False if (response >> 2) % 2 else True

    def reboot(self):
        """
        Reboots the system (note, this will end the serial connection)
        """
        self.execute("reboot-system")
