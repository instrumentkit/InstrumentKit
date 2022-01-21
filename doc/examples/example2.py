#!/usr/bin/python
# Filename: example2.py

# Example 1:
# 	- Import required packages
# 	- Create object for our Tek TDS 224
# 	- Transfer the waveform from the oscilloscope on channel 1 using binary block reading
# 	- Calculate the FFT of the transfered waveform
# 	- Graph resultant data

from instruments import *

import numpy as np
import matplotlib.pyplot as plt

tek = Tektds224("/dev/ttyUSB0", 1, 30)

[x, y] = tek.readWaveform("CH1", "BINARY")
freq = np.fft.fft(y)  # Calculate FFT
timestep = float(tek.query("WFMP:XIN?"))  # Query the timestep between data points
freqx = np.fft.fftfreq(freq.size, timestep)  # Compute the x-axis for the FFT data
plt.plot(freqx, abs(freq))  # Plot the data using matplotlib
plt.ylim(0, 500)  # Adjust the vertical scale
plt.show()  # Show the graph
