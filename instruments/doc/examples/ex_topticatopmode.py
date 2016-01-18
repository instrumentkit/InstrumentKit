#Thorlabs Temperature Controller example

import instruments as ik
import quantities
tm = ik.toptica.TopMode.open_serial('/dev/ttyACM0', 115200)


print("The current emission state is: ", tm.enable)
print("The current lock state is: ", tm.locked)
print("The current interlock state is: ", tm.interlock)
print("The current fpga state is: ", tm.fpga_status)
print("The current temperature state is: ", tm.temperature_status)
print("The current current state is: ", tm.current_status)

print("The laser1's serial number is: ", tm.laser1.serial_number)
print("The laser1's model number is: ", tm.laser1.model)
print("The laser1's wavelength is: ", tm.laser1.wavelength)
print("The laser1's production date is: ", tm.laser1.production_date)
print("The laser1's enable state is: ", tm.laser1.enable)
print("The laser1's up time is: ", tm.laser1.on_time)
print("The laser1's charm state is: ", tm.laser1.charm_status)
print("The laser1's temperature controller state is: ", tm.laser1.temperature_control_status)
print("The laser1's current controller state is: ", tm.laser1.current_control_status)
print("The laser1's tec state is: ", tm.laser1.tec_status)
print("The laser1's intensity is: ", tm.laser1.intensity)
print("The laser1's mode hop state is: ", tm.laser1.mode_hop)
print("The laser1's lock start time is: ", tm.laser1.lock_start)
print("The laser1's first mode hop time is: ", tm.laser1.first_mode_hop_time)
print("The laser1's latest mode hop time is: ", tm.laser1.latest_mode_hop_time)
print("The laser1's correction status is: ", tm.laser1.correction_status)











