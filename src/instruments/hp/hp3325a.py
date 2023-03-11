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
import math
import typing
# IMPORTS #####################################################################

from enum import IntEnum

from instruments.abstract_instruments.function_generator import FunctionGenerator

# CLASSES #####################################################################


class HP3325a(FunctionGenerator):

    """The `HP3325a` is a 20Mhz Synthesizer / Function Generator.

    It supports sine-, square-, triangle-, ramp- waves across a wide range of frequencies. It also supports amplitude
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

    freq_scale = {"HZ": 1, "KH": 1E3, "MH": 1E6}
    ampl_scale = {"VO": 1, "MV": 1E-3, "VR": math.sqrt(2.0), "MR": 1E-3*math.sqrt(2.0)}

    @property
    def amplitude(self):
        am_resp = self.query("IAM")
        am_units = am_resp[-2:]
        am_num = am_resp[:-2].replace("AM", "").strip()
        return float(am_num * HP3325a.ampl_scale[am_units])

    @amplitude.setter
    def amplitude(self, new_amp):
        freq_units = "VO"
        freq_num = new_amp
        self.sendcmd(f"AM{freq_num}{freq_units}")

    @property
    def frequency(self):
        fr_resp = self.query("IFR")
        freq_units = fr_resp[-2:]
        freq_num = fr_resp[:-2].replace("FR", "").strip()
        return float(freq_num*HP3325a.freq_scale[freq_units])

    @frequency.setter
    def frequency(self, new_freq):
        # TODO - Do we need to scale by units?
        freq_units = "HZ"
        freq_num = new_freq
        self.sendcmd(f"FR{freq_num}{freq_units}")

    @property
    def function(self) -> Waveform:
        fu_resp = self.query("IFU")
        fu_resp = fu_resp.replace("FU", "")
        return HP3325a.Waveform(int(fu_resp))

    @function.setter
    def function(self, new_waveform: typing.Union[Waveform, FunctionGenerator.Function]):
        if type(new_waveform) is FunctionGenerator.Function:
            # Map to internal forms
            if new_waveform == FunctionGenerator.Function.arbitrary:
                # TODO - If this is HP3325B, it might work
                raise NotImplementedError("HP3325A does not support arbitrary source!")
            elif new_waveform == FunctionGenerator.Function.noise:
                raise NotImplementedError("HP3325A does not support arbitrary noise!")
            elif new_waveform == FunctionGenerator.Function.ramp:
                # TODO - Distinguish positive and negative ramp?
                new_waveform = HP3325a.Waveform.positive_ramp
            elif new_waveform == FunctionGenerator.Function.sinusoid:
                new_waveform = HP3325a.Waveform.sine
            elif new_waveform == FunctionGenerator.Function.square:
                new_waveform = HP3325a.Waveform.square
            elif new_waveform == FunctionGenerator.Function.triangle:
                new_waveform = HP3325a.Waveform.triangle
            else:
                raise NotImplementedError(f"HP3325 does not support function {new_waveform}")
        self.sendcmd(f"FU{int(new_waveform)}")

    @property
    def offset(self) -> float:
        of_resp = self.query("IOF")
        of_resp = of_resp.replace("OF", "")
        of_units = of_resp[-2:]
        # TODO - Use internal units system of instrumentkit
        return float(of_resp[:-2])*(1 if of_units == "VO" else 1000)

    @offset.setter
    def offset(self, new_offset):
        # TODO - Use internal units / better ranging
        self.sendcmd(f"OF{new_offset}VO")

    @property
    def phase(self) -> float:
        ph_resp = self.query("IPH")
        ph_resp = ph_resp.replace("PH", "").replace("DE","")
        # TODO - Use internal units system of instrumentkit
        return float(ph_resp)

    @phase.setter
    def phase(self, new_ph: float):
        self.sendcmd(f"PH{new_ph}DE")

    @property
    def high_voltage(self) -> bool:
        hv_resp = self.query("IHV")
        return int(hv_resp[-1]) == 1

    @high_voltage.setter
    def high_voltage(self, new_hv: bool):
        self.sendcmd(f"HV{1 if new_hv else 0}")

    @property
    def amplitude_modulation(self) -> bool:
        hv_resp = self.query("IMA")
        return int(hv_resp[-1]) == 1

    @amplitude_modulation.setter
    def amplitude_modulation(self, new_am: bool):
        self.sendcmd(f"MA{1 if new_am else 0}")

    @property
    def marker_frequency(self) -> bool:
        hv_resp = self.query("IMA")
        return int(hv_resp[-1]) == 1

    @marker_frequency.setter
    def marker_frequency(self, new_mf: bool):
        self.sendcmd(f"MA{1 if new_mf else 0}")

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
