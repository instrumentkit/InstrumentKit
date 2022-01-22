=============================
Utility Functions and Classes
=============================

.. currentmodule:: instruments.util_fns

Unit Handling
=============

.. autofunction:: assume_units

.. autofunction:: split_unit_str

.. autofunction:: convert_temperature

Enumerating Instrument Functionality
====================================

To expose parts of an instrument or device in a Python-ic way, the
:class:`ProxyList` class can be used to emulate a list type by calling the
initializer for some inner class. This is used to expose everything from
channels to axes.

.. _property_factories:

Property Factories
==================

To help expose instrument properties in a consistent and predictable manner,
InstrumentKit offers several functions that return instances of `property`
that are backed by the :meth:`~instruments.Instrument.sendcmd` and
:meth:`~instruments.Instrument.query` protocol. These factories assume
a command protocol that at least resembles the SCPI style::

    -> FOO:BAR?
    <- 42
    -> FOO:BAR 6
    -> FOO:BAR?
    <- 6

It is recommended to use the property factories whenever possible to help
reduce the amount of copy-paste throughout the code base. The factories allow
for a centralized location for input/output error checking, units handling,
and type conversions. In addition, improvements to the property factories
benefit all classes that use it.

Lets say, for example, that you were writing a class for a power supply. This
class might require these two properties: ``output`` and ``voltage``. The first
will be used to enable/disable the output on the power supply, while the second
will be the desired output voltage when the output is enabled. The first lends
itself well to a `bool_property`. The output voltage property corresponds with
a physical quantity (voltage, of course) and so it is best to use either
`unitful_property` or `bounded_unitful_property`, depending if you wish to
bound user input to some set limits. `bounded_unitful_property` can take
either hard-coded set limits, or it can query the instrument during runtime
to determine what those bounds are, and constrain user input to within them.

Examples
--------

These properties, when implemented in your class, might look like this::

    output = bool_property(
        "OUT",
        inst_true="1",
        inst_false="0",
        doc="""
        Gets/sets the output status of the power supply

        :type: `bool`
        """
    )

    voltage, voltage_min, voltage_max = bounded_unitful_property(
        voltage = unitful_property(
        "VOLT",
        u.volt,
        valid_range=(0*u.volt, 10*u.volt)
        doc="""
        Gets/sets the output voltage.

        :units: As specified, or assumed to be :math:`\\text{V}` otherwise.
        :type: `float` or `~pint.Quantity`
        """
    )

The most difficult to use parameters for the property factories are
``input_decoration`` and ``output_decoration``. These are callable objects
that will be applied to the data immediately after receiving it from the
instrument (input) or before it is inserted into the string that will be sent
out to the instrument (output).

Using `enum_property` as the simple example, a frequent use case for
``input_decoration`` will be to convert a `str` containing a numeric digit
into an actual `int` so that it can be looked up in `enum.IntEnum`. Here is
an example of this::

    class Mode(IntEnum):

        """
        Enum containing valid output modes of the ABC123 instrument
        """
        foo = 0
        bar = 1
        bloop = 2

    mode = enum_property(
        "MODE",
        enum=Mode,
        input_decoration=int,
        set_fmt="{}={}",
        doc="""
        Gets/sets the output mode of the ABC123 instrument

        :rtype: `ABC123.Mode`
        """
    )

So in this example, when querying the ``mode`` property, the string ``MODE?``
will first be sent to the instrument, at which point it will return one of
``"0"``, ``"1"``, or ``"2"``. However, before this value can be used to get
the correct enum value, it needs to be converted into an `int`. This is what
``input_decoration`` is used for. Since `int` is callable and can convert
a `str` to an `int`, this accomplishes exactly what we're looking for.

Pretty much anything callable can be passed into these parameters. Here is
an example using a lambda function with a `unitful_property` taken from
the `~instruments.thorlabs.TC200` class::

    temperature = unitful_property(
        "tact",
        units=u.degC,
        readonly=True,
        input_decoration=lambda x: x.replace(
            " C", "").replace(" F", "").replace(" K", ""),
        doc="""
        Gets the actual temperature of the sensor

        :units: As specified (if a `~pint.Quantity`) or assumed
            to be of units degrees C.
        :type: `~pint.Quantity` or `int`
        :return: the temperature (in degrees C)
        :rtype: `~pint.Quantity`
        """
    )

An alternative to lambda functions is passing in static methods
(`staticmethod`).

Bool Property
-------------

.. autofunction:: bool_property

Enum Property
-------------

.. autofunction:: enum_property

Unitless Property
-----------------

.. autofunction:: unitless_property

Int Property
------------

.. autofunction:: int_property

Unitful Property
----------------

.. autofunction:: unitful_property

Bounded Unitful Property
------------------------

.. autofunction:: bounded_unitful_property

String Property
---------------

.. autofunction:: string_property


Named Structures
================

The :class:`~instruments.named_struct.NamedStruct` class can be used to represent
C-style structures for serializing and deserializing data.

.. autoclass:: instruments.named_struct.NamedStruct

.. autoclass:: instruments.named_struct.Field

.. autoclass:: instruments.named_struct.Padding
