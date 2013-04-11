..
    TODO: put documentation license header here.
    
============
Introduction
============

Installing
==========

Dependencies
------------

- NumPy
- `PySerial`_
- `quantities`_
- `flufl.enum`_

Optional Dependencies
~~~~~~~~~~~~~~~~~~~~~

- PyYAML
- PyUSB (version 1.0a or higher)

.. _PySerial: http://pyserial.sourceforge.net/
.. _quantities: http://pythonhosted.org/quantities/
.. _flufl.enum: http://pythonhosted.org/flufl.enum/

Setting Up USB Devices
======================

Roughly, add the following to udev::

    ATTRS{idVendor}=="213e", ATTRS{idProduct}=="000a", SYMLINK+="phasematrix", MODE="0666"
    ATTRS{idVendor}=="0699", ATTRS{idProduct}=="0401", SYMLINK+="tekdpo4104", MODE="0666"
