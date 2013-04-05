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

tek = Tektds224('/dev/ttyUSB0',1,30)

t0=time.time()
[x,y] = tek.readWaveform('CH1','BINARY')
print time.time()-t0

