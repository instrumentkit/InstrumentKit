# <nbformat>3.0</nbformat>

# <headingcell level=1>

# InstrumentKit Library Examples

# <headingcell level=2>

# Stanford Research Systems DG645 Digital Delay Generator

# <markdowncell>

# In this example, we will demonstrate how to connect to an SRS DG645 digital delay generator, and how to set a new delay pattern.

# <markdowncell>

# We start by importing the `srs` package from within the main `instruments` package, along with the `instruments.units` package
# that is used to track physical quantities.

# <codecell>

from instruments.srs import SRSDG645
import instruments.units as u

# <markdowncell>

# Next, we open the instrument, assuming that it is connected via GPIB. Note that you may have to change this line
# to match your setup.

# <codecell>

ddg = SRSDG645.open_gpibusb("/dev/ttyUSB0", 15)

# <markdowncell>

# We can now set the delay on channel $A$ to be $B + 10\ \mu\text{s}$.

# <codecell>

ddg.channel[ddg.Channels.A].delay = (ddg.Channels.B, u.Quantity(10, "us"))

# <codecell>
