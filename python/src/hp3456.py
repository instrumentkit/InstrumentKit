import logging
import time
import instruments as ik
import quantities as pq

dmm = ik.hp.HP3456a.open_gpibusb('/dev/ttyUSB0', 22)
logging.basicConfig(level=logging.DEBUG)
dmm._file.debug = True
dmm.trigger_mode = dmm.TriggerMode.hold
dmm.number_of_digits = 6
dmm.auto_range()

n = 10
dmm.number_of_readings = n
dmm.nplc = 1
dmm.mode = dmm.Mode.resistance_2wire
dmm.trigger()
time.sleep(n * 0.04)
v = dmm.fetch(dmm.Mode.resistance_2wire)
print len(v)

# Read registers
dmm.nplc = 10
print "n = {}".format(dmm.number_of_readings)
print "g = {}".format(dmm.number_of_digits)
print "p = {}".format(dmm.nplc)
print "d = {}".format(dmm.delay)
print dmm.mean
print dmm.variance
print dmm.count
print dmm.lower
print dmm.upper
print dmm.r
print dmm.y
print dmm.z

# Walk through input range
dmm.nplc = 100
print dmm.count
print dmm.measure(dmm.Mode.ratio_dcv_dcv)
print dmm.measure(dmm.Mode.resistance_2wire)
for i in range(-1, 4):
    value = (10 ** i) * pq.volt
    dmm.input_range = value
    print dmm.measure(dmm.Mode.dcv)

# Walk through relative / null mode
print dmm.relative
dmm.relative = False
print dmm.measure(dmm.Mode.resistance_2wire)
dmm.relative = True
print dmm.measure(dmm.Mode.resistance_2wire)
dmm.relative = False
print dmm.measure(dmm.Mode.resistance_2wire)

# Measure with autozero off
dmm.autozero = 0
dmm.filter = 0
dmm.auto_range()

print dmm.measure(dmm.Mode.dcv)
dmm.autozero = 1
print dmm.measure(dmm.Mode.dcv)
dmm.filter = 1
print dmm.measure(dmm.Mode.dcv)
dmm.autozero = 0
print dmm.measure(dmm.Mode.dcv)

