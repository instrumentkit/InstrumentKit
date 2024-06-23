#!/usr/bin/env python
#
# hp3325a.py: Driver for the HP3235a/b Synthesizer/Function Generator.
#
# © 2023 Scott Phillips (polygonguru@gmail.com).
#
# This file is a part of the InstrumentKit project.
# Licensed under the AGPL version 3.
#
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
#
"""
Driver for the HP3325a Synthesizer/Function Generator

Originally contributed and copyright held by Scott Phillips (polygonguru@gmail.com)

An unrestricted license has been provided to the maintainers of the Instrument
Kit project.
"""

# IMPORTS #####################################################################
import math
from enum import Enum, IntEnum

from instruments import Instrument
from instruments.abstract_instruments import FunctionGenerator
from instruments.units import ureg as u
from instruments.util_fns import enum_property, unitful_property, bool_property


# CLASSES #####################################################################

def amplitude_parse(am_resp: str) -> float:
    am_units = am_resp[-2:]
    am_num = am_resp[:-2].replace("AM", "").strip()
    return float(am_num * HP3325a.ampl_scale[am_units])


def frequency_parse(fr_resp: str) -> float:
    freq_units = fr_resp[-2:]
    freq_num = fr_resp[:-2].replace("FR", "").strip()
    return float(freq_num * HP3325a.freq_scale[freq_units])


def offset_parse(of_resp: str) -> float:
    of_resp = of_resp.replace("OF", "")
    of_units = of_resp[-2:]
    return float(of_resp[:-2]) * (1 if of_units == "VO" else 1000)


class HP3325a(FunctionGenerator):
    """The `HP3325a` is a 20Mhz Synthesizer / Function Generator.

    It supports sine-, square-, triangle-, ramp-waves across a wide range of frequencies. It also supports amplitude
    and phase modulation, as well as DC-offset.

    `HP3325a` is a HPIB / pre-448.2 instrument.
    """

    def __init__(self, filelike):
        """
        Initialise the instrument, and set the required eos, eoi needed for
        communication.
        """
        super().__init__(filelike)
        self._channel_count = 1
        self.terminator = "\r\n"

    class Waveform(IntEnum):
        """
        Enum with the supported math modes
        """
        dc_only = 0
        sine = 1
        square = 2
        triangle = 3
        positive_ramp = 4
        negative_ramp = 5

    class FrequencyScale(Enum):
        """
        Enum with the supported frequency scales
        """
        hertz = 1
        kilohertz = 1e3
        megahertz = 1e6

    class AmplitudeScale(Enum):
        """
        Enum with the supported amplitude scales
        """
        Volts = 1
        Millivolts = 1e-3
        Volts_RMS = math.sqrt(2.0)
        Millivolts_RMS = 1e-3 * math.sqrt(2.0)

    freq_scale = {"HZ": 1, "KH": 1e3, "MH": 1e6}
    ampl_scale = {
        "VO": 1,
        "MV": 1e-3,
        "VR": math.sqrt(2.0),
        "MR": 1e-3 * math.sqrt(2.0),
    }

    # PROPERTIES ##

    function = enum_property(
        command="IFU",
        enum=Waveform,
        set_cmd="FU",
        doc="""
        Gets/sets the output function of the function generator
        
        type: `HP3325a.Waveform`
        """,
        input_decoration=int,
        set_fmt="{}{}",
    )

    amplitude = unitful_property(
        command="IAM",
        units=u.volts,
        set_cmd="AM",
        format_code="{}",
        doc="""
        Gets/sets the amplitude of the output waveform
        
        :type: `float`
        """,
        input_decoration=amplitude_parse,
        set_fmt="{}{}VO",
    )

    frequency = unitful_property(
        command="IFR",
        units=u.hertz,
        set_cmd="FR",
        format_code="{}",
        doc="""
        Gets/sets the frequency of the output waveform
        
        :type: `float`
        """,
        input_decoration=frequency_parse,
        set_fmt="{}{}HZ",
    )

    offset = unitful_property(
        command="IOF",
        units=u.volts,
        set_cmd="OF",
        format_code="{}",
        doc="""
        Gets/sets the offset of the output waveform
        
        :type: `float`
        """,
        input_decoration=offset_parse,
        set_fmt="{}{}VO",
    )

    phase = unitful_property(
        command="IPH",
        units=u.degrees,
        set_cmd="PH",
        format_code="{}",
        doc="""
        Gets/sets the phase of the output waveform
        
        :type: `float`
        """,
        input_decoration=lambda x: float(x.replace("PH", "").replace("DE", "").strip()),
        set_fmt="{}{}DE",
    )

    high_voltage = bool_property(
        command="IHV",
        set_cmd="HV",
        inst_true="HV1",
        inst_false="HV0",
        doc="""
        Gets/sets the high voltage mode of the output waveform
        
        :type: `bool`
        """,
        set_fmt="{}{}",
    )

    amplitude_modulation = bool_property(
        command="IMA",
        set_cmd="MA",
        inst_true="1",
        inst_false="0",
        doc="""
        Gets/sets the amplitude modulation mode of the output waveform
        
        :type: `bool`
        """,
        set_fmt="{}{}",
    )

    marker_frequency = bool_property(
        command="IMA",
        set_cmd="MA",
        inst_true="1",
        inst_false="0",
        doc="""
        Gets/sets the marker frequency mode of the output waveform
        
        :type: `bool`
        """,
        set_fmt="{}{}",
    )

    def query(self, cmd, size=-1):
        """
        Query the instrument with the given command and return the response
        """
        # strip the question mark because HP3325A is too old for that
        cmd = cmd.replace("?", "")
        return Instrument.query(self, cmd, size)

    def amplitude_calibration(self):
        self.sendcmd("AC")

    def assign_zero_phase(self):
        self.sendcmd("AP")

    # TODO - Support CALM which only works on 3325B
    # TODO - Support DCLR which only works on 3325B
    # TODO - Support DISP which only works on 3325B
    # TODO - Support DRCL,DSTO which only works on 3325B
    # TODO - Support DSP which only works on 3325B
    # TODO - Support ECHO which only works on 3325B
    # TODO - Support ENH which only works on 3325B
    # TODO - Support ESTB which only works on 3325B
    # TODO - Support EXTR which only works on 3325B
    # TODO - Support HEAD which only works on 3325B
    # TODO - Support *IDN? which only works on 3325B
    # TODO - Support LCL which only works on 3325B

    def query_error(self) -> int:
        # TODO - Support ERR? on HP3325B which is more specific
        err_resp = self.query("IER")
        return int(err_resp.replace("e", "").replace("r", "").strip())


# UNITS #######################################################################

UNITS = {
    None: 1,
}
