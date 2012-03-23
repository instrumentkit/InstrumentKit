#!/usr/bin/python
# Filename: example1.py

# Example 1:
#	- Import required packages
#	- Create object for our Tek TDS 224
#	- Query the object for its identification
#	- Print the result to screen

from instruments import *
import time
import numpy as np
import time

tek = Tektds224('COM5',1,30)

t0=time.clock()
[x,y] = tek.readWaveform('CH1','BINARY')
print time.clock()-t0

