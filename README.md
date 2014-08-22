InstrumentKit
=============

[![Build Status](https://travis-ci.org/Galvant/InstrumentKit.svg?branch=dev)](https://travis-ci.org/Galvant/InstrumentKit)

This project contains code to easily interact with laboratory equipment using
various communication buses.

Supported means of communication are:
- Galvant Industries GPIBUSB adapter
- Serial
- Sockets
- VISA
- USB TMC files (eg /dev/ttyTMC0)

All code in this repository is released under the AGPL-v3 license.


Usage Example
-------------

To open a connection to a generic SCPI-compatible multimeter using a Galvant Industries'
GPIBUSB adapter:

```python
>>> import instruments as ik
>>> inst = ik.generic_scpi.SCPIMultimeter.open_gpibusb('/dev/ttyUSB0', 1)
```

From there, various built-in properties and functions can be called. For example, the
instrument's identification information can be retrieved by calling the name property:

```python
>>> print inst.name
```

Due to the sheer number of commands most instruments support, not every single 
one is included in InstrumentKit. If there is a specific command you wish to 
send, one can use the following functions to do so:

```python
>>> inst.sendcmd('DATA') # Send command with no response
>>> resp = inst.query('*IDN?') # Send command and retrieve response
```

Documentation
-------------

You can find the project documentation at our ReadTheDocs pages located at
http://instrumentkit.readthedocs.org/en/latest/index.html
