#!/usr/bin/env python
"""
Driver for the Pfeiffer TPG36x vacumm gauge controller.
"""

# IMPORTS #####################################################################

from enum import Enum, IntEnum

from instruments.abstract_instruments import Instrument
from instruments.units import ureg as u
from instruments.util_fns import ProxyList

# CLASSES #####################################################################


class TPG36x(Instrument):
    """
    The Pfeiffer TPG361/2 is a vacuum gauge controller with one/two channels.

    By default, the two channel version is intialized. If you have the one channel
    version (TPG361), set the `number_channels` property to 1.

    Example usage:

        TODO:

    """

    def __init__(self, filelike):
        super().__init__(filelike)

        self._number_channels = 2

        self._defined_cmd = {
            "ETX": 3,
            "ENQ": 5,
            "ACK": 6,
            "NAK": 21,
        }

        self.terminator = "\r\n"

    class Language(Enum):
        """Enum to get/set the language of the device."""

        ENGLISH = 0
        GERMAN = 1
        FRENCH = 2

    class PressureUnit(Enum):
        """Enum for the pressure units (example)."""
        MBAR = 0
        TORR = 1
        PASCAL = 2

    class Channel:
        """
        Class representing a sensor attached to the TPG 362.

        .. warning:: This class should NOT be manually created by the user. It is
            designed to be initialized by the `TPG36x` class.
        """

        def __init__(self, parent, chan):
            if not isinstance(parent, TPG36x):
                raise TypeError("Don't do that.")
            self._chan = chan
            self._parent = parent

        @property
        def pressure(self):
            """
            The pressure measured by the channel, returned as a pint.Quantity
            with the correct units attached (based on instrument settings).
            """
            # Exemple de réponse brute : "0,+1.7377E+00"
            raw_str = self._parent.query(f"PR{self._chan + 1}")

            # On sépare le code d'état et la valeur
            status_str, val_str = raw_str.split(',')

            # Convertit la partie pression en float
            val = float(val_str)  # => +1.7377E+00 -> 1.7377

            # Récupère l'unité courante configurée
            current_unit_enum_name = self._parent.pressure_unit  # "MBAR", "TORR", etc.

            # On fait un "map" vers pint
            if current_unit_enum_name == "MBAR":
                return val * u.mbar
            elif current_unit_enum_name == "TORR":
                return val * u.torr
            elif current_unit_enum_name == "PASCAL":
                return val * u.pascal
            else:
                # fallback
                return val * u.dimensionless

    @property
    def channel(self):
        """
        Gets a specific channel object.

        Note that the channel number is pythonic, i.e., the first channel is 0.

        :rtype: `TPG36x.Channel`
        """
        return ProxyList(self, self.Channel, range(self._number_channels))

    @property
    def language(self):
        """
        Get the language of the TPG36x.

        :rtype: `TPG36x.Language`
        """
        val = int(self.query("LNG"))
        return self.Language(val).name

    @language.setter
    def language(self, value):
        """
        Set the language of the TPG36x.

        :param value: The language to set.
        :type value: `TPG36x.Language`
        """
        self.sendcmd(f"LNG,{value.value}")


    @property
    def pressure_unit(self):
        """
        Get or set the unit of the TPG36x (global to the instrument).

        :rtype: str (the name of the enum, e.g. "MBAR", "TORR", "PASCAL", etc.)
        """
        val = self.query("UNI")
        val = int(val)
        return self.PressureUnit(val).name
        #the doc may be send just 0, 1, 2, ... so we need to convert it in int

    @pressure_unit.setter
    def pressure_unit(self, new_unit):
        """
        Set the unit of the TPG36x.

        :param new_unit: The unit to set, e.g. TPG36x.PressureUnit.MBAR
                         ou simplement la string "MBAR".
        """
        # Like that the code can accept enum or a string
        if isinstance(new_unit, str):
            # We suppose "MBAR", "TORR", "PASCAL"
            new_unit = self.PressureUnit[new_unit.upper()]
        cmd_val = new_unit.value
        self.sendcmd(f"UNI,{cmd_val}")


    @property
    def name(self):
        """
        Get the name from the TPG36x.

        :rtype: str
        """
        return self.query("AYT").split(",")[0]

    @property
    def number_channels(self):
        """
        The number of channels on the TPG36x.

        :rtype: int
        """
        return self._number_channels

    @number_channels.setter
    def number_channels(self, value):
        if value not in (1, 2):
            raise ValueError("The TPG36x only supports 1 or 2 channels.")
        self._number_channels = value

    @property
    def pressure(self):
        """
        The pressure measured by the first channel.

        To select the channel, get a channel first and then call the pressure
        method on it.

        :rtype: `pint.Quantity`
        """
        return self.channel[0].pressure

    def query(self, cmd):
        """
        Query the TPG36x with the enquire command.

        :return: The response from the TPG36x.
        """
        self.sendcmd(cmd)
        self.write(chr(self._defined_cmd["ENQ"]))
        return self.read()

    def _ack_expected(self, msg=""):
        return [chr(self._defined_cmd["ACK"])]