#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# events.py: Small framework for C#-style delegate/event handling.
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


## FEATURES ###################################################################

from __future__ import division

## FUNCTIONS ##################################################################

def event_property(event_name, doc=None):
    """
    Exposes an event as a property, so that callers cannot change the value of
    the event, but may only add or remove delegates.
    """
    def fget(self):
        return getattr(self, event_name)
    def fset(self, new_event):
        old_event = getattr(self, event_name)
        if new_event is not old_event:
            raise AttributeError("can't set attribute")
    return property(fget, fset, doc=doc)

## CLASSES ####################################################################

class Event(object):
    """
    Represents an event that can be listened to by zero or more delegates
    (callbacks).
    
    Delegates are callables that accept three arguments, ``(sender, event,
    event_obj)``. Here, ``event`` is the instance of `Event` that the delegate
    was added to, and ``event_obj`` is an object prepared by the sender
    containing additional information about the event. If the sender did not
    provide any additional information, then ``event_obj`` is `None`.
    
    :param object sender: An object to mark as the *sender* of an event, useful
        for delegates that listen to the same event from multiple objects.        
    """
    
    def __init__(self, sender):
        self._sender = sender
        self._delegates = []
        
    def __iadd__(self, delegate):
        self._delegates.append(delegate)
        return self
        
    def __isub__(self, delegate):
        if delegate not in self._delegates:
            raise ValueError("Given delegate was not registered.")
        else:
            del self._delegates[self._delegates.index(delegate)]
        return self
            
    def __call__(self, event_obj=None):
        for delegate in self._delegates:
            delegate(self._sender, self, event_obj)

