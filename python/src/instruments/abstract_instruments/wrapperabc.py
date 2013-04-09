#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# wrapperabc.py: Python ABC for file-like wrappers
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
##

## FEATURES ####################################################################

from __future__ import division

## IMPORTS #####################################################################

import abc

class WrapperABC(object):
    __metaclass__ = abc.ABCMeta
    
    ## PROPERTIES ##
    
    def getaddress(self):
        '''
        Read the current instrument address
        '''
        raise NotImplementedError
    def setaddress(self, newval):
        '''
        Change the instrument address
        '''
        raise NotImplementedError
    address = abc.abstractproperty(getaddress, setaddress)

