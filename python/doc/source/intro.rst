..
    TODO: put documentation license header here.
    
============
Introduction
============

Installing
==========

Dependencies
------------

Most of the required and optional dependencies can be obtained using
``easy_intstall`` or ``pip`` (preferred).

Required Dependencies
~~~~~~~~~~~~~~~~~~~~~

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

