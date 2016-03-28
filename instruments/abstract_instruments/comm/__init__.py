#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module containing communication layers
"""

from __future__ import absolute_import

from .abstract_comm import AbstractCommunicator

from .socket_communicator import SocketCommunicator
from .usb_communicator import USBCommunicator
from .serial_communicator import SerialCommunicator
from .visa_communicator import VisaCommunicator
from .loopback_communicator import LoopbackCommunicator
from .gi_gpib_communicator import GPIBCommunicator
from .file_communicator import FileCommunicator
from .usbtmc_communicator import USBTMCCommunicator
from .vxi11_communicator import VXI11Communicator
