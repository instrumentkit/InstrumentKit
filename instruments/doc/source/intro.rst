..
    TODO: put documentation license header here.
    
============
Introduction
============

**InstrumentKit** allows for the control of scientific instruments in a
platform-independent manner, abstracted from the details of how the instrument
is connected. In particular, InstrumentKit supports connecting to instruments
via serial port (including USB-based virtual serial connections), GPIB, USBTMC,
TCP/IP or by using the VISA layer.

Installing
==========

Dependencies
------------

Most of the required and optional dependencies can be obtained using
``easy_install`` or ``pip`` (preferred).

Required Dependencies
~~~~~~~~~~~~~~~~~~~~~

If you're using ``pip``, these requirements can be obtained automatically
by using the provided ``requirements.txt``::

$ pip install -r requirements.txt

- NumPy
- `PySerial`_
- `quantities`_
- `flufl.enum`_ version 4.0 or later

Optional Dependencies
~~~~~~~~~~~~~~~~~~~~~

- `PyYAML`_ (required for configuration file support)
- `PyUSB`_ (version 1.0a or higher, required for raw USB support)
- `PyVISA`_ (required for accessing instruments via VISA library)

.. _PySerial: http://pyserial.sourceforge.net/
.. _quantities: http://pythonhosted.org/quantities/
.. _flufl.enum: http://pythonhosted.org/flufl.enum/
.. _PyYAML: https://bitbucket.org/xi/pyyaml
.. _PyUSB: http://sourceforge.net/apps/trac/pyusb/
.. _PyVISA: http://pyvisa.sourceforge.net/

Getting Started
===============

Instruments and Instrument Classes
----------------------------------

Each make and model of instrument that is supported by InstrumentKit is
represented by a specific class, as documented in the :ref:`apiref`.
Instruments that offer common functionality, such as multimeters, are
represented by base classes, such that specific instruments can be exchanged
without affecting code, so long as the proper functionality is provided.

For some instruments, a specific instrument class is not needed, as the
:ref:`apiref-generic_scpi` classes can be used to expose functionality of these
instruments. If you don't see your specific instrument listed, then, please
check in the instrument's manual whether it uses a standard set of SCPI
commands.

Connecting to Instruments
-------------------------

Each instrument class in InstrumentKit is constructed using a *communicator*
class that wraps a file-like object with additional information about newlines,
terminators and other useful details. Most of the time, it is easiest to not
worry with creating communicators directly, as convienence methods are provided
to quickly connect to instruments over a wide range of common communication
protocols and physical connections.

For instance, to connect to a generic SCPI-compliant multimeter using a
`Galvant Industries GPIB-USB adapter`_, the
`~instruments.Instrument.open_gpibusb` method can be used::

>>> import instruments as ik
>>> inst = ik.generic_scpi.SCPIMultimeter.open_gpibusb('/dev/ttyUSB0', 1)

Similarly, many instruments connected by USB use an FTDI or similar chip to
emulate serial ports, and can be connected using the
`~instruments.Instrument.open_serial` method by specifying the serial port
device file (on Linux) or name (on Windows) along with the baud rate of the
emulated port::

>>> inst = ik.generic_scpi.SCPIMultimeter.open_serial('COM10', 115200)

As a convienence, an instrument connection can also be specified using a
uniform resource identifier (URI) string::

>>> inst = ik.generic_scpi.SCPIMultimeter.open_from_uri('tcpip://192.168.0.10:4100')

Instrument connection URIs of this kind are useful for storing in configuration
files, as the same method, `~instruments.Instrument.open_from_uri`, is used,
regardless of the communication protocol and physical connection being used.
InstrumentKit provides special support for this usage, and can load instruments
from specifications listed in a YAML-formatted configuration file. See the
`~instruments.load_instruments` function for more details.

.. _Galvant Industries GPIB-USB adapter: http://galvant.ca/shop/gpibusb/


Using Connected Instruments
---------------------------

Once connected, functionality of each instrument is exposed by methods and
properties of the instrument object. For instance, the name of an instrument
can be queried by getting the ``name`` property::

>>> print inst.name

For details of how to use each instrument, please see the :ref:`apiref` entry
for that instrument's class. If that class does not implement a given command,
raw commands and queries can be issued by using the
`~instruments.Instrument.sendcmd` and `~instruments.Instrument.query` methods,
respectively::

>>> inst.sendcmd('DATA') # Send command with no response
>>> resp = inst.query('*IDN?') # Send command and retrieve response

OS-Specific Instructions
========================

Linux
-----

Raw USB Device Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To enable writing to a USB device in raw or usbtmc mode, the device file
must be readable writable by users. As this is not normally the default, you
need to add rules to ``/etc/udev/rules.d`` to override the default permissions.
For instance, to add a Tektronix DPO 4104 oscilloscope with world-writable
permissions, add the following to rules.d::

    ATTRS{idVendor}=="0699", ATTRS{idProduct}=="0401", SYMLINK+="tekdpo4104", MODE="0666"
    
.. warning::
    This configuration causes the USB device to be world-writable. Do not do
    this on a multi-user system with untrusted users.

