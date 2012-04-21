#!/usr/bin/python
# Filename: example3.py

# Example 1:
#	- Import required packages
#	- Create object for our Keithley 195
#	- Transfer the currently displayed value from the DMM to computer screen


from instruments import *

keithley = Keithley195('/dev/ttyUSB0',16,30)

print keithley.read()
