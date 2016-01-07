.. _code_style:

============
Coding Style
============

Data Types
==========

Numeric Data
------------

When appropriate, use :class:`pq.Quantity` objects to track units.
If this is not possible or appropriate, use a bare `float` for scalars
and `np.ndarray` for array-valued data.

Boolean and Enumerated Data
---------------------------

If a property or method argument can take exactly two values,
of which one can be interpreted in the affirmative, use Python
`bool` data types to represent this. Be permissive in what you accept
as `True` and `False`, in order to be consistent with Python conventions
for truthy and falsey values. This can be accomplished using the
`bool` function to convert to Booleans, and is done implicitly by
the `if` statement.

If a property has more than two permissible values, or the two allowable
values are not naturally interpreted as a Boolean (e.g.: positive/negative,
AC/DC coupling, etc.), then consider using an `~flufl.enum.Enum` or `~flufl.enum.IntEnum` as
provided by `flufl.enum`. The latter is useful in Python 2.6 and 2.7 for
wrapping integer values that are meaningful to the device.
For example, if an instrument can operate in AC or DC mode, use an enumeration
like the following::

	class SomeInstrument(Instrument):

		# Define as an inner class.
		class Mode(Enum):
			"""
			When appropriate, document the enumeration itself...
			"""
			#: ...and each of the enumeration values.
			ac = "AC"
			#: The "#:" notation means that this line documents
			#: the following member, SomeInstrument.Mode.dc.
			dc = "DC"

		# For SCPI-like instruments, enum_property
		# works well to expose the enumeration.
		# This will generate commands like ":MODE AC"
		# and ":MODE DC".
		mode = enum_property(":MODE", SomeInstrument.Mode)

	# To set the mode is now straightforward.
	ins = SomeInstrument.open_somehow()
	ins.mode = ins.Mode.ac

Note that the enumeration is an inner class, as described below
in :ref:`associated_types`.

Object Oriented Design
======================

.. _associated_types:

Associated Types
----------------

Many instrument classes have associated types, such as channels and
axes, so that these properties of the instrument can be manipulated
independently of the underlying instrument::

	>>> channels = [ins1.channel[0], ins2.channel[3]]

Here, the user of ``channels`` need not know or care that the two
channels are from different instruments, as is useful for large
installations. This lets users quickly redefine their setups
with minimal code changes.

To enable this, the associated types should be made inner classes
that are exposed using :class:`~instruments.util_fns.ProxyList`.
For example::

	class SomeInstrument(Instrument):
		# If there's a more appropriate base class, please use it
		# in preference to object!
		class Channel(object):
			# We use a three-argument initializer,
			# to remember which instrument this channel belongs to,
			# as well as its index or label on that instrument.
			# This will be useful in sending commands, and in exposing
			# via ProxyList.
			def __init__(self, parent, idx):
				self._parent = parent
				self._idx = idx
			# define some things here...

		@property
		def channel(self):
			return ProxyList(self, SomeInstrument.Channel, range(2))

This defines an instrument with two channels, having labels ``0`` and ``1``.
By using an inner class, the channel is clearly associated with the instrument,
and appears with the instrument in documentation.

Since this convention is somewhat recent, you may find older code that uses
a style more like this::

	class _SomeInstrumentChannel(object):
		# stuff

	class SomeInstrument(Instrument):
		@property
		def channel(self):
			return ProxyList(self, _SomeInstrumentChannel, range(2))

This can be redefined in a backwards-compatible way by bringing the channel
class inside, then defining a new module-level variable for the old name::

	class SomeInstrument(Instrument):
		class Channel(object):
			# stuff

		@property
		def channel(self):
			return ProxyList(self, _SomeInstrumentChannel, range(2))

	_SomeInstrumentChannel = SomeInstrument.Channel
