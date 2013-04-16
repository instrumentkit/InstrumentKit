#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# util_fns.py: Random utility functions.
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

## CLASSES #####################################################################

class ProxyList(object):
    def __init__(self, parent, proxy_cls, valid_set):
        self._parent = parent
        self._proxy_cls = proxy_cls
        self._valid_set = valid_set
    def __iter__(self):
        for idx in self._valid_set:
            yield self._proxy_cls(self._parent, idx)
    def __getitem__(self, idx):
        if idx not in self._valid_set:
            raise IndexError("Index out of range. Must be "
                                "in {}.".format(self._valid_set))
        return self._proxy_cls(self._parent, idx)

