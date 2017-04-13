InstrumentKit
=============

.. image:: https://img.shields.io/travis/Galvant/InstrumentKit.svg?maxAge=2592000
    :target: https://travis-ci.org/Galvant/InstrumentKit
    :alt: Travis-CI build status

.. image:: https://img.shields.io/coveralls/Galvant/InstrumentKit/dev.svg?maxAge=2592000
    :target: https://coveralls.io/r/Galvant/InstrumentKit?branch=dev
    :alt: Coveralls code coverage

.. image:: https://readthedocs.org/projects/instrumentkit/badge/?version=latest
    :target: https://readthedocs.org/projects/instrumentkit/?badge=latest
    :alt: Documentation

.. image:: https://img.shields.io/pypi/v/instrumentkit.svg?maxAge=86400
    :target: https://pypi.python.org/pypi/instrumentkit
    :alt: PyPI version

.. image:: https://img.shields.io/pypi/pyversions/instrumentkit.svg?maxAge=2592000
    :alt: Python versions

InstrumentKit is an open source Python library designed to help the
end-user get straight into communicating with their equipment via a PC.
InstrumentKit aims to accomplish this by providing a connection- and
vendor-agnostic API. Users can freely swap between a variety of
connection types (ethernet, gpib, serial, usb) without impacting their
code. Since the API is consistent across similar instruments, a user
can, for example, upgrade from their 1980's multimeter using GPIB to a
modern Keysight 34461a using ethernet with only a single line change.

Supported means of communication are:

- Galvant Industries GPIBUSB adapter (``open_gpibusb``)
- Serial (``open_serial``)
- Sockets (``open_tcpip``)
- VISA (``open_visa``)
- Read/write from unix files (``open_file``)
- USBTMC (``open_usbtmc``)
- VXI11 over Ethernet (``open_vxi11``)

There is planned support for HiSLIP someday, but a good Python HiSLIP library will be needed first.

If you have any problems or have code you wish to contribute back to the
project please feel free to open an issue or a pull request!

Installation
------------

The ``instruments`` package can be installed from this repository by the
following means:

From Git:

.. code-block:: console

    $ git clone git@github.com:Galvant/InstrumentKit.git
    $ cd InstrumentKit
    $ python setup.py install

From Github using pip:

.. code-block:: console

    $ pip install -e git+https://www.github.com/Galvant/InstrumentKit.git#egg=instrumentkit

From pypi using pip:

.. code-block:: console

    $ pip install instrumentkit


Usage Example
-------------

To open a connection to a generic SCPI-compatible multimeter using a Galvant
Industries' GPIBUSB adapter:

.. code-block:: python

    >>> import instruments as ik
    >>> inst = ik.generic_scpi.SCPIMultimeter.open_gpibusb("/dev/ttyUSB0", 1)

From there, various built-in properties and functions can be called. For
example, the instrument's identification information can be retrieved by
calling the name property:

.. code-block:: python

    >>> print(inst.name)

Or, since in the demo we connected to an ``SCPIMultimeter``, we can preform
multimeter-specific tasks, such as switching functions, and taking a
measurement reading:

.. code-block:: python

    >>> reading = inst.measure(inst.Mode.voltage_dc)
    >>> print("Value: {}, units: {}".format(reading.magnitude, reading.units))

Due to the sheer number of commands most instruments support, not every single
one is included in InstrumentKit. If there is a specific command you wish to
send, one can use the following functions to do so:

.. code-block:: python

    >>> inst.sendcmd("DATA") # Send command with no response
    >>> resp = inst.query("*IDN?") # Send command and retrieve response

Python Version Compatibility
----------------------------

At this time, Python 2.7, 3.3, 3.4, and 3.5 are supported. Should you encounter
any problems with this library that occur in one version or another, please
do not hesitate to let us know.

Documentation
-------------

You can find the project documentation at our ReadTheDocs pages located at
http://instrumentkit.readthedocs.org/en/latest/index.html

Contributing
------------

The InstrumentKit team always welcome additional contributions to the project.
However, we ask that you please review our contributing developer guidelines
which can be found in the documentation. We also suggest that you look at
existing classes which are similar to your work to learn more about the
structure of this project.

To run the tests against all supported version of Python, you will need to
have the binary for each installed, as well as any requirements needed to
install ``numpy`` under each Python version. On Debian/Ubuntu systems this means
you will need to install the ``python-dev`` package for each version of Python
supported (``python2.7-dev``, ``python3.3-dev``, etc).

With the required system packages installed, all tests can be run with ``tox``:

.. code-block:: console

    $ pip install tox
    $ tox

License
-------

All code in this repository is released under the AGPL-v3 license. Please see
the ``license`` folder for more information.