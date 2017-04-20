#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Class for quickly defining C-like structures with named fields.
"""

# IMPORTS #####################################################################

from __future__ import absolute_import
from __future__ import division

import struct
from collections import OrderedDict

from future.utils import with_metaclass

# DESIGN NOTES ################################################################
"""
This class uses the Django-like strategy described at
    http://stackoverflow.com/a/3288988/267841
to assign a "birthday" to each Field as it's instantiated. We can thus sort
each Field in a NamedStruct by its birthday.

Notably, this hack is not at all required on Python 3.6:
    https://www.python.org/dev/peps/pep-0520/

TODO: arrays other than string arrays do not currently work.
"""

# CLASSES #####################################################################

class Field(object):
    """
    A named field within a C-style structure.

    :param str fmt: Format for the field, corresponding to the
        documentation of the :mod:`struct` standard library package.
    """

    __n_fields_created = 0
    _field_birthday = None

    _fmt = ''
    _name = None
    _owner_type = object

    def __init__(self, fmt):
        super(Field, self).__init__()

        # Record our birthday so that we can sort fields later.
        self._field_birthday = Field.__n_fields_created
        Field.__n_fields_created += 1

        self._fmt = fmt

    def is_significant(self):
        return not self._fmt.strip().endswith('x')

    def __repr__(self):
        if self._owner_type:
            return "<Field {} of {}, fmt={}>".format(
                self._name, self._owner_type, self._fmt
            )

        return "<Unbound field, fmt={}>".format(
            self._fmt
        )

    def __str__(self):
        fmt = self._fmt.strip()
        n, fmt_char = fmt[:-1], fmt[-1]
        c_type = {
            'x': 'char',
            'c': 'char',
            'b': 'char',
            'B': 'unsigned char',
            '?': 'bool',
            'h': 'short',
            'H': 'unsigned short',
            'i': 'int',
            'I': 'unsigned int',
            'l': 'long',
            'L': 'unsigned long',
            'q': 'long long',
            'Q': 'unsigned long long',
            'f': 'float',
            'd': 'double',
            # NB: no [], since that will be implied by n.
            's': 'char',
            'p': 'char',
            'P': 'void *'
        }[fmt_char]

        if n:
            c_type = "{}[{}]".format(c_type, n)
        return (
            "{c_type} {self._name}".format(c_type=c_type, self=self)
            if self.is_significant()
            else c_type
        )

    # DESCRIPTOR PROTOCOL #

    def __get__(self, obj, type=None):
        return obj._values[self._name]

    def __set__(self, obj, value):
        obj._values[self._name] = value

class Padding(Field):
    def __init__(self, n_bytes=1):
        super(Padding, self).__init__('{}x'.format(n_bytes))

class HasFields(type):
    def __new__(mcls, name, bases, attrs):
        # Since this is a metaclass, the __new__ method observes
        # creation of new *classes* and not new instances.
        # We call the superclass of HasFields, which is another
        # metaclass, to do most of the heavy lifting of creating
        # the new class.
        cls = super(HasFields, mcls).__new__(mcls, name, bases, attrs)

        # We now sort the fields by their birthdays and store them in an
        # ordered dict for easier look up later.
        cls._fields = OrderedDict([
            (field_name, field)
            for field_name, field in sorted(
                [
                    (field_name, field)
                    for field_name, field in attrs.items()
                    if isinstance(field, Field)
                ],
                key=lambda item: item[1]._field_birthday
            )
        ])

        # Assign names and owner types to each field so that they can follow
        # the descriptor protocol.
        for field_name, field in cls._fields.items():
            field._name = field_name
            field._owner_type = cls

        # Associate a struct.Struct instance with the new class
        # that defines how to pack/unpack the new type.
        cls._struct = struct.Struct(
            # TODO: support alignment char at start.
            " ".join([
                field._fmt for field in cls._fields.values()
            ])
        )

        return cls

class NamedStruct(with_metaclass(HasFields, object)):
    def __init__(self, **kwargs):
        super(NamedStruct, self).__init__()
        self._values = OrderedDict([
            (
                field._name,
                kwargs[field._name] if field._name in kwargs else None
            )
            for field in filter(Field.is_significant, self._fields.values())
        ])

    def _to_seq(self):
        return tuple(self._values.values())

    @classmethod
    def _from_seq(cls, new_values):
        return cls(**{
            field._name: new_value
            for field, new_value in
            zip(filter(Field.is_significant, cls._fields.values()), new_values)
        })

    def pack(self):
        return self._struct.pack(*self._to_seq())

    @classmethod
    def unpack(cls, buffer):
        return cls._from_seq(cls._struct.unpack(buffer))

    def __str__(self):
        return "{name} {{\n{fields}\n}}".format(
            name=type(self).__name__,
            fields="\n".join([
                "    {field}{value};".format(
                    field=field,
                    value=(
                        " = {}".format(repr(self._values[field._name]))
                        if field.is_significant()
                        else ""
                    )
                )
                for field in self._fields.values()
            ])
        )
