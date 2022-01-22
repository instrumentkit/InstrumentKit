# <nbformat>3.0</nbformat>

# <headingcell level=1>

# InstrumentKit Library Examples

# <headingcell level=2>

# Tektronix DPO 4104 Oscilloscope

# <markdowncell>

# In this example, we will demonstrate how to connect to a Tektronix DPO 4104
# oscilloscope and transfer the waveform from channel 1 into memory.

# <markdowncell>

# We start by importing the InstrumentKit and numpy packages. In this example
# we require numpy because the waveforms will be returned as numpy arrays.

# <codecell>

import instruments as ik
import numpy as np

# <markdowncell>

# Next, we open our connection to the oscilloscope. Here we use the associated
# TekDPO4104 class and open the connection via TCP/IP to address 192.168.0.2 on
# port 8080.

# <markdowncell>

# The connection method used will have to be changed to match your setup.

# <codecell>

tek = ik.tektronix.TekTDS224.open_tcpip("192.168.0.2", 8080)

# <markdowncell>

# Now that we are connected to the instrument, we can transfer the waveform
# from the oscilloscope. Note that Python channel[0] specifies the physical
# channel 1. This is due to Python's zero-based numbering vs Tektronix's
# one-based numbering.

# <codecell>

[x, y] = tek.channel[0].read_waveform()

# <markdowncell>

# With the waveform now in memory, any other data analysis can be performed.
# Here we simply compute the mean value from the y-data.

# <codecell>

print(np.mean(y))
