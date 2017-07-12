#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing tests for named structures.
"""

# IMPORTS ####################################################################

from __future__ import absolute_import

from hypothesis import given
import hypothesis.strategies as st

from unittest import TestCase

from instruments.named_struct import (
    Field, StringField, Padding, NamedStruct
)

# TESTS ######################################################################

# pylint: disable=no-member,protected-access,blacklisted-name,missing-docstring

class TestNamedStruct(TestCase):
    @given(st.integers(min_value=0, max_value=0x7FFF*2+1), st.integers(min_value=0, max_value=0xFF))
    def test_roundtrip(self, var1, var2):
        class Foo(NamedStruct):
            a = Field('H')
            padding = Padding(12)
            b = Field('B')

        foo = Foo(a=var1, b=var2)
        assert Foo.unpack(foo.pack()) == foo


    def test_str(self):
        class Foo(NamedStruct):
            a = StringField(8)
            b = StringField(9, strip_null=True)

        foo = Foo(a="0123456\x00", b='abc')
        assert Foo.unpack(foo.pack()) == foo


    def test_negative_len(self):
        """
        Checks whether negative field lengths correctly raise.
        """
        with self.assertRaises(TypeError):
            class Foo(NamedStruct):
                a = StringField(-1)
