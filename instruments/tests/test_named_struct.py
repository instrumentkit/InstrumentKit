#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing tests for named structures.
"""

# IMPORTS ####################################################################

from __future__ import absolute_import

from instruments.named_struct import (
    Field, Padding, NamedStruct
)

# TESTS ######################################################################

# pylint: disable=no-member,protected-access,blacklisted-name,missing-docstring

def test_named_struct_roundtrip():
    class Foo(NamedStruct):
        a = Field('H')
        padding = Padding(12)
        b = Field('B')

    foo = Foo(a=0x1234, b=0xab)
    assert Foo.unpack(foo.pack()) == foo
