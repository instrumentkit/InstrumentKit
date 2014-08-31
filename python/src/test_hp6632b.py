import instruments as ik
psu = ik.hp.HP6632b.open_gpibusb('/dev/ttyUSB0', 6)
print psu.name
psu.display_textmode=True
psu.display_text("HPIB TEST")
psu.output = False
psu.voltage = 10
psu.current = 0.2
print psu.voltage
print psu.voltage_sense
print psu.overvoltage
print psu.current
print psu.current_sense
print psu.overcurrent
print psu.output
print psu.current_sense_range
print psu.output_dfi_source
print psu.output_remote_inhibit
psu.output_remote_inhibit = ik.hp.HP6632b.RemoteInhibit.off
print psu.digital_function
print psu.digital_data
print psu.sense_sweep_points
print psu.sense_sweep_interval
print psu.sense_window
print psu.output_protection_delay
print psu.voltage_alc_bandwidth
psu.voltage_trigger = 1
psu.current_trigger = 0.1
print psu.voltage_trigger
print psu.current_trigger
psu.init_output_trigger()
psu.output = 1
psu.wait_to_continue()
psu.sendcmd('+get')
print psu.op_complete
print psu.check_error_queue()
print psu.output
print psu.voltage
psu.output = 0
print psu.init_output_continuous
psu.init_output_continuous = True
print psu.init_output_continuous
psu.voltage = 0
psu.current = 0
psu.voltage_trigger = 3
psu.current_trigger = 0.01
psu.init_output_trigger()
psu.output = 1
psu.trigger()
print psu.voltage
psu.voltage_trigger = 2
psu.sendcmd('+get')
print psu.voltage
psu.output = 0
