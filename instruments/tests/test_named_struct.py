#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing tests for named structures.
"""

# IMPORTS ####################################################################

from __future__ import absolute_import

from instruments.named_struct import (
    Field, StringField, Padding, NamedStruct
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


def test_named_struct_str():
    class Foo(NamedStruct):
        a = StringField(8)
        b = StringField(9, strip_null=True)

    foo = Foo(a="0123456\x00", b='abc')
    assert Foo.unpack(foo.pack()) == foo
