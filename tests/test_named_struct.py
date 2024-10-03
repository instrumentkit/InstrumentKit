#!/usr/bin/env python
"""
Module containing tests for named structures.
"""

# IMPORTS ####################################################################


from unittest import TestCase

from hypothesis import given
import hypothesis.strategies as st

from instruments.named_struct import Field, StringField, Padding, NamedStruct


# TESTS ######################################################################

# We disable pylint warnings that are not as applicable for unit tests.
# pylint: disable=no-member,protected-access,blacklisted-name,missing-docstring,no-self-use


class TestNamedStruct(TestCase):
    @given(
        st.integers(min_value=0, max_value=0x7FFF * 2 + 1),
        st.integers(min_value=0, max_value=0xFF),
    )
    def test_roundtrip(self, var1, var2):
        class Foo(NamedStruct):
            a = Field("H")
            padding = Padding(12)
            b = Field("B")

        foo = Foo(a=var1, b=var2)
        assert Foo.unpack(foo.pack()) == foo

    def test_str(self):
        class Foo(NamedStruct):
            a = StringField(8, strip_null=False)
            b = StringField(9, strip_null=True)
            c = StringField(2, encoding="utf-8")

        foo = Foo(a="0123456\x00", b="abc", c="α")
        assert Foo.unpack(foo.pack()) == foo

        # Also check that we can get fields out directly.
        self.assertEqual(foo.a, "0123456\x00")
        self.assertEqual(foo.b, "abc")
        self.assertEqual(foo.c, "α")

    def test_negative_len(self):
        """
        Checks whether negative field lengths correctly raise.
        """
        with self.assertRaises(TypeError):

            class Foo(NamedStruct):  # pylint: disable=unused-variable
                a = StringField(-1)

    def test_equality(self):
        class Foo(NamedStruct):
            a = Field("H")
            b = Field("B")
            c = StringField(5, encoding="utf8", strip_null=True)

        foo1 = Foo(a=0x1234, b=0x56, c="ω")
        foo2 = Foo(a=0xABCD, b=0xEF, c="α")

        assert foo1 == foo1
        assert foo1 != foo2
