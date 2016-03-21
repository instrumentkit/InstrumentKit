InstrumentKit
=============

[![Build Status](https://travis-ci.org/Galvant/InstrumentKit.svg?branch=dev)](https://travis-ci.org/Galvant/InstrumentKit) [![Coverage Status](https://coveralls.io/repos/Galvant/InstrumentKit/badge.svg?branch=dev)](https://coveralls.io/r/Galvant/InstrumentKit?branch=dev) [![Documentation Status](https://readthedocs.org/projects/instrumentkit/badge/?version=latest)](https://readthedocs.org/projects/instrumentkit/?badge=latest)

This project contains code to easily interact with laboratory equipment using
various communication buses.

Supported means of communication are:
- Galvant Industries GPIBUSB adapter (`open_gpibusb`)
- Serial (`open_serial`)
- Sockets (`open_tcpip`)
- VISA (`open_visa`)
- Read/write from unix files (`open_file`)
- USBTMC (`open_usbtmc`)

There is planned support for VXI11 (current under development) and eventually
HiSLIP.

If you have any problems or have code you wish to contribute back to the
project please feel free to open an issue or a pull request!

Installation
------------

The `instruments` package can be installed from this repository by the
following means:

From Git:
```bash
$ git clone git@github.com:Galvant/InstrumentKit.git
$ cd InstrumentKit
$ python setup.py install
```

From Github using pip:
``` bash
$ pip install -e git@github.com:Galvant/InstrumentKit.git
```

From pypi using pip (planned, not yet implemented):
```bash
$ pip install instruments
```

Usage Example
-------------

To open a connection to a generic SCPI-compatible multimeter using a Galvant
Industries' GPIBUSB adapter:

```python
>>> import instruments as ik
>>> inst = ik.generic_scpi.SCPIMultimeter.open_gpibusb('/dev/ttyUSB0', 1)
```

From there, various built-in properties and functions can be called. For
example, the instrument's identification information can be retrieved by
calling the name property:

```python
>>> print(inst.name)
```

Or, since in the demo we connected to an `SCPIMultimeter`, we can preform
multimeter-specific tasks, such as switching functions, and taking a
measurement reading:

```python
>>> reading = inst.measure(inst.Mode.voltage_dc)
>>> print("Value: {}, units: {}".format(reading.magnitude, reading.units))
```

Due to the sheer number of commands most instruments support, not every single 
one is included in InstrumentKit. If there is a specific command you wish to 
send, one can use the following functions to do so:

```python
>>> inst.sendcmd("DATA") # Send command with no response
>>> resp = inst.query("*IDN?") # Send command and retrieve response
```

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
install `numpy` under each Python version. On Debian/Ubuntu systems this means
you will need to install the `python-dev` package for each version of Python
supported (`python2.7-dev`, `python3.3-dev`, etc).

With the required system packages installed, all tests can be run with `tox`:

```bash
$ pip install tox
$ tox
```

License
-------

All code in this repository is released under the AGPL-v3 license. Please see
the `license` folder for more information.