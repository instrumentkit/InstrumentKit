#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# util_fns.py: Random utility functions.
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

import quantities as pq
from flufl.enum import Enum, IntEnum

## FUNCTIONS ###################################################################

def assume_units(value, units):
    """
    If units are not provided for ``value`` (that is, if it is a raw
    `float`), then returns a `~quantities.Quantity` with magnitude
    given by ``value`` and units given by ``units``.
    """
    if not isinstance(value, pq.Quantity):
        value = pq.Quantity(value, units)
    return value

def bool_property(name, inst_true, inst_false, doc=None):
    """
    Called inside of SCPI classes to instantiate boolean properties 
    of the device cleanly.
    Example:
    my_property = bool_property("BEST:PROPERTY", "ON", "OFF")
    """
    def getter(self):
        return self.query(name + "?").strip() == inst_true
    def setter(self, newval):
        self.sendcmd("{} {}".format(name, inst_true if newval else inst_false))
        
    return property(fget=getter, fset=setter, doc=doc)
    
def enum_property(name, enum, doc=None, input_decoration=None, output_decoration=None):
    """
    Called inside of SCPI classes to instantiate Enum properties 
    of the device cleanly.
    The decorations can be functions which modify the incoming and outgoing 
    values for dumb instruments that do stuff like include superfluous quotes
    that you might not want in your enum.
    Example:
    my_property = bool_property("BEST:PROPERTY", enum_class)
    """
    def in_decor_fcn(val):
        return val if input_decoration is None else input_decoration(val)
    def out_decor_fcn(val):
        return val if output_decoration is None else output_decoration(val)
    def getter(self):
        return enum[in_decor_fcn(self.query("{}?".format(name)))]
    def setter(self, newval):
        self.sendcmd("{} {}".format(name, out_decor_fcn(enum[newval].value)))
    
    return property(fget=getter, fset=setter, doc=doc)

def unitless_property(name, format_code='{:e}', doc=None):
    """
    Called inside of SCPI classes to instantiate properties with unitless 
    numeric values.
    """
    def getter(self):
        raw = self.query("{}?".format(name))
        return float(raw)
    def setter(self, newval):
        strval = format_code.format(newval)
        self.sendcmd("{} {}".format(name, strval))

    return property(fget=getter, fset=setter, doc=doc)

def unitful_property(name, units, format_code='{:e}', doc=None):
    """
    Called inside of SCPI classes to instantiate properties with unitful numeric
    values.
    """
    def getter(self):
        raw = self.query("{}?".format(name))
        return float(raw) * unit
    def setter(self, newval):
        # Rescale to the correct unit before printing. This will also catch bad units.
        strval = format_code.format(assume_units(newval, units).rescale(units).item())
        self.sendcmd("{} {}".format(name, strval))

    return property(fget=getter, fset=setter, doc=doc)

def string_property(name, bookmark_symbol='"', doc=None):
    """
    Called inside of SCPI classes to instantiate properties with a string value.
    """
    bookmark_length = len(bookmark_symbol)
    def getter(self):
        raw = self.query("{}?".format(name))
        return raw[bookmark_length:-bookmark_length]
    def setter(self, newval):
        self.sendcmd("{} {}{}{}".format(name, bookmark_symbol, newval, bookmark_symbol))

    return property(fget=getter, fset=setter, doc=doc)

## CLASSES #####################################################################

class ProxyList(object):
    def __init__(self, parent, proxy_cls, valid_set):
        self._parent = parent
        self._proxy_cls = proxy_cls
        self._valid_set = valid_set
        
        # FIXME: This only checks the next level up the chain!
        self._isenum = (Enum in valid_set.__bases__) or (IntEnum in valid_set.__bases__)
    def __iter__(self):
        for idx in self._valid_set:
            yield self._proxy_cls(self._parent, idx)
    def __getitem__(self, idx):
        # If we have an enum, try to normalize by using getitem. This will
        # allow for things like 'x' to be used instead of enum.x.
        if self._isenum:
            try:
                idx = self._valid_set[idx]
            except ValueError:
                pass
            
        if idx not in self._valid_set:
            raise IndexError("Index out of range. Must be "
                                "in {}.".format(self._valid_set))
        return self._proxy_cls(self._parent, idx)
    def __len__(self):
        return len(self._valid_set)
