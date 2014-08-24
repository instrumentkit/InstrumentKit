=================
Design Philosophy
=================

Here, we describe the design philosophy behind InstrumentKit at a high-level.
Specific implications of this philosophy for coding style and practices
are detailed in :ref:`code_style`.

Pythonic
========

InstrumentKit aims to make instruments and devices look and feel native to the
Python development culture. Users should not have to worry if a given
instrument names channels starting with 1 or 0, because Python itself is zero-
based.

>>> scope.data_source = scope.channel[0] # doctest: +SKIP

Accessing parts of an instrument should be supported in a way that supports
standard Python idioms, most notably iteration.

>>> for channel in scope.channel: # doctest: +SKIP
...     channel.coupling = scope.Coupling.ground

Values that can be queried and set should be exposed as properties.
Instrument modes that should be entered and exited on a temporary basis should
be exposed as context managers. In short, anyone familiar with Python should
be able to read InstrumentKit-based programs with little to no confusion.

Abstract
========

Users should not have to worry overmuch about the particular instruments that
are being used, but about the functionality that instrument exposes. To a large
degree, this is enabled by using common base classes, such as
:class:`instruments.generic_scpi.SCPIOscilloscope`. While every instrument does
offer its own unique functionality, by consolidating common functionality in
base classes, users can employ some subset without worrying too much about the
particulars.

This also extends to communications methods. By consolidating communication
logic in the
:class:`instruments.abstract_instruments.comm.AbstractCommunicator` class,
users can connect instruments however is convienent for them, and can change
communications methods without affecting their software very much.

Robust
======

Communications with instruments should be handled in such a way that errors
are reported in a natural and Python-ic way, such that incorrect or unsafe
operation is avoided, and such that all communications are correct.

An important consequence of this is that all quantities communicated to or from
the instrument should be *unitful*. In this way, users can specify the
dimensionality of values to be sent to the device without regards for what the
instrument expects; the unit conversions will be handled by InstrumentKit in a
way that ensures that the expectations of the instrument are properly met,
irrespective of the user.

