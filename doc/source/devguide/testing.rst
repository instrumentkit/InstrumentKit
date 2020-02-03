================================
Testing Instrument Functionality
================================

.. currentmodule:: instruments.tests

Overview
========

When developing new instrument classes, or adding functionality to existing
instruments, it is important to also add automated checks for the correctness
of the new functionality. Such tests serve two distinct purposes:

- Ensures that the protocol for each instrument is being followed correctly,
  even with changes in the underlying InstrumentKit behavior.
- Ensures that the API seen by external users is kept stable and consistent.

The former is especially important for instrument control, as the developers
of InstrumentKit will not, in general, have access to each instrument that
is supported--- we rely on automated testing to ensure that future changes
do not cause invalid or undesired operation.

For InstrumentKit, we rely heavily on `pytest`_, a mature and flexible
unit-testing framework for Python. When run from the command line via
``pytest``, or when run by Travis CI, pytest will automatically execute
functions and methods whose names start with ``test`` in packages, modules
and classes whose names start with ``test`` or ``Test``, depending. (Please
see the `pytest`_ documentation for full details, as this is not intended
to be a guide to pytest so much as a guide to how we use it in IK.)
Because of this, we keep all test cases in the ``instruments.tests``
package, under a subpackage named for the particular manufacturer,
such as ``instruments.tests.test_srs``. The tests for each instrument should
be contained within its own file. Please see current tests as an example. If
the number of tests for a given instrument is numerous, please consider making
modules within a manufacturer test subpackage for each particular device.

Below, we discuss two distinct kinds of unit tests: those that check
that InstrumentKit functionality such as :ref:`property_factories` work correctly
for new instruments, and those that check that existing instruments produce
correct protocols.

Mock Instruments
================

TODO

Expected Protocols
==================

As an example of asserting correctness of implemented protocols, let's consider
a simple test case for :class:`instruments.srs.SRSDG645``::

	def test_srsdg645_output_level():
	    """
	    SRSDG645: Checks getting/setting unitful ouput level.
	    """
	    with expected_protocol(ik.srs.SRSDG645,
	            [
	                "LAMP? 1",
	                "LAMP 1,4.0",
	            ], [
	                "3.2"
	            ],
	            sep="\n"
	    ) as ddg:
	        unit_eq(ddg.output['AB'].level_amplitude, u.Quantity(3.2, "V"))
	        ddg.output['AB'].level_amplitude = 4.0

Here, we see that the test has a name beginning with ``test_``, has a simple
docstring that will be printed in reports on failing tests, and then has a
call to :func:`expected_protocol`. The latter consists of specifying an
instrument class, here given as ``ik.srs.DG645``, then a list of expected
outputs and playback to check property accessors.

Note that :func:`expected_protocol` acts as a context manager, such that it will,
at the end of the indented block, assert the correct operation of the contents of
that block. In this example, the second argument to :func:`expected_protocol`
specifies that the instrument class should have sent out two strings,
``"LAMP? 1"`` and ``LAMP 1,4.0``, during the block, and should act correctly
when given an answer of ``"3.2"`` back from the instrument. The third parameter,
``sep`` specifies what will be appended to the end of each lines in the
previous parameters. This lets you specify the termination character that
will be used in the communication without having to write it out each and
every time.

Protocol Assertion Functions
----------------------------

.. autofunction:: expected_protocol

.. _pytest: https://docs.pytest.org/en/latest/
