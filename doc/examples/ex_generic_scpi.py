# <nbformat>3.0</nbformat>

# <headingcell level=1>

# InstrumentKit Library Examples

# <headingcell level=2>

# Generic SCPI Instrument

# <markdowncell>

# In this example, we will demonstrate how to connect to a generic SCPI
# instrument and query its identification information.

# <markdowncell>

# We start by importing the InstrumentKit package.

# <codecell>

import instruments as ik

# <markdowncell>

# Next, we open our connection to the instrument. Here we use the generic
# SCPIInstrument class and open the connection using the Galvant Industries'
# GPIBUSB adapter. Our connection is made to the virtual serial port located at
# /dev/ttyUSB0 and GPIB address 1

# <markdowncell>

# The connection method used will have to be changed to match your setup.

# <codecell>

inst = ik.generic_scpi.SCPIInstrument.open_gpibusb("/dev/ttyUSB0", 1)

# <markdowncell>

# Now that we are connected to the instrument, we can query its identification
# information. We will do this by using the SCPIInstrument property 'name'.

# <codecell>

print(inst.name)
