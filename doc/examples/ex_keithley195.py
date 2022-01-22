# <nbformat>3.0</nbformat>

# <headingcell level=1>

# InstrumentKit Library Examples

# <headingcell level=2>

# Keithley 195 Multimeter

# <markdowncell>

# In this example, we will demonstrate how to connect to a Keithley 195
# multimeter and transfer a single reading to the PC.

# <markdowncell>

# We start by importing the InstrumentKit package.

# <codecell>

import instruments as ik

# <markdowncell>

# Next, we open our connection to the instrument. Here we use the
# Keithley195 class and open the connection using Galvant Industries'
# GPIBUSB adapter. Our connection is made to the virtual serial port located at
# /dev/ttyUSB0 and GPIB address 16.

# <codecell>

dmm = ik.keithley.Keithley195.open_gpibusb("/dev/ttyUSB0", 1)

# <markdowncell>

# Now, we retreive the measurement currently displayed on the front panel.

# <codecell>

print(dmm.measure())
