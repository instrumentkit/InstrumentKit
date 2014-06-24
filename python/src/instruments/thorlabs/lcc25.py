from instruments.abstract_instruments import Instrument
import quantities as pq


class LCC25(Instrument):
    """
    The LCC25 is a controller for the thorlabs liquid crystal modules.
    it can set two voltages and then oscillate between them at a specific repition rate
    The user manual can be found here:
    http://www.thorlabs.com/thorcat/18800/LCC25-Manual.pdf
    """
    def __init__(self, filelike):
        super(LCC25, self).__init__(filelike)
        self.terminator = "\r"
        self.endTerminator = ">"

    def checkCommand(self,command):
        """
        Checks for the \"Command error CMD_NOT_DEFINED\" error, which can sometimes occur if there were
        incorrect terminators on the previous command. If the command is successful, it returns the value,
        if not, it returns CMD_NOT_DEFINED
        checkCommand will also clear out the query string
        """
        response = self.query(command)
        cmdFind = response.find("CMD_NOT_DEFINED")
        if cmdFind ==-1:
            errorFind = response.find("CMD_ARG_INVALID")
            if errorFind ==-1:
                outputStr = response.replace(command,"")
                outputStr = outputStr.replace(self.terminator,"")
                outputStr = outputStr.replace(self.endTerminator,"")
            else:
                outputStr = "CMD_ARG_INVALID"
        else:
            outputStr = "CMD_NOT_DEFINED"
        return outputStr


    def identity(self):
        """
        gets the name and version number of the device
        """
        response = self.checkCommand("*idn?")
        if response is "CMD_NOT_DEFINED":
            self.identity()          
        else:
            return response

    ### LCC SETTINGS ###

    @property
    def frequency(self):
        """
        The frequency at which the LCC oscillates between the two voltages
        """
        response = self.checkCommand("freq?")
        if not response is "CMD_NOT_DEFINED":
            return float(response)*pq.Hz
    @frequency.setter
    def frequency(self, newval):
        if newval < 5:
            raise ValueError("Frequency is too low.")
        if newval >150:
            raise ValueError("Frequency is too high")
        self.sendcmd("freq={}".format(newval))

    @property
    def mode(self):
        """
        The output mode of the LCC
        mode 0 modulates between voltage 1 and voltage 2
        mode 1 sets the output to voltage 1
        mode 2 sets the output to voltage 2
        """
        response = self.checkCommand("mode?")
        if not response is "CMD_NOT_DEFINED":
            return float(response)
    @mode.setter
    def mode(self, newval):
        if newval != 0 and newval != 1 and newval !=2:
            raise ValueError("Not a valid output mode")
        self.sendcmd("mode={}".format(newval))

    @property
    def enable(self):
        """
        If output enable is on, there is a voltage on the output
        """
        response = self.checkCommand("enable?")
        if not response is "CMD_NOT_DEFINED":
            return float(response)
    @enable.setter
    def enable(self, newval):
        if newval != 0 and newval != 1:
            raise ValueError("Not a valid value for output enable")
        self.sendcmd("enable={}".format(newval))
    
    @property
    def extern(self):
        """
        0 for internal modulation, 1 for external TTL modulation
        """
        response = self.checkCommand("extern?")
        if not response is "CMD_NOT_DEFINED":
            return float(response)
    @extern.setter
    def extern(self, newval):
        if newval != 0 and newval != 1:
            raise ValueError("Not a valid value for external modulation enable")
        self.sendcmd("extern={}".format(newval))

    @property
    def remote(self):
        """
        0 for normal operation, 1 to lock out buttons
        """
        response = self.checkCommand("remote?")
        if not response is "CMD_NOT_DEFINED":
            return float(response)
    @remote.setter
    def remote(self, newval):
        if newval != 0 and newval != 1:
            raise ValueError("Not a valid value for remote operation enable")
        self.sendcmd("remote={}".format(newval))

    @property
    def voltage1(self):
        """
        The voltage value for output 1
        """
        response = self.checkCommand("volt1?")
        if not response is "CMD_NOT_DEFINED":
            return float(response)*pq.V
    @voltage1.setter
    def voltage1(self, newval):
        if newval < 0:
            raise ValueError("Voltage is too low.")
        if newval >25:
            raise ValueError("Voltage is too high")
        self.sendcmd("volt1={}".format(newval))

    @property
    def voltage2(self):
        """
        The voltage value for output 2
        """
        response = self.checkCommand("volt2?")
        if not response is "CMD_NOT_DEFINED":
            return float(response)*pq.V
    @voltage1.setter
    def voltage2(self, newval):
        if newval < 0:
            raise ValueError("Voltage is too low.")
        if newval >25:
            raise ValueError("Voltage is too high")
        self.sendcmd("volt2={}".format(newval))


    @property
    def minVoltage(self):
        """
        The minimum voltage value for the test mode
        """
        response = self.checkCommand("min?")
        if not response is "CMD_NOT_DEFINED":
            return float(response)*pq.V
    @minVoltage.setter
    def minVoltage(self, newval):
        if newval < 0:
            raise ValueError("Voltage is too low.")
        if newval >25:
            raise ValueError("Voltage is too high")
        self.sendcmd("min={}".format(newval))

    
    @property
    def maxVoltage(self):
        """
        The maximum voltage value for the test mode
        if the maximum voltage is greater than the minimum voltage, nothing happens
        """
        response = self.checkCommand("max?")
        if not response is "CMD_NOT_DEFINED":
            return float(response)*pq.V
    
    @maxVoltage.setter
    def maxVoltage(self, newval):
        if newval < 0:
            raise ValueError("Voltage is too low.")
        if newval >25:
            raise ValueError("Voltage is too high")
        self.sendcmd("max={}".format(newval))

    @property
    def dwell(self):
        """
        The dwell time for voltages for the test mode
        """
        response = self.checkCommand("dwell?")
        if not response is "CMD_NOT_DEFINED":
            return float(response)*pq.ms
    
    @dwell.setter
    def dwell(self, newval):
        if newval < 0:
            raise ValueError("Dwell time must be positive")
        self.sendcmd("dwell={}".format(newval))

    @property
    def increment(self):
        """
        The voltage increment for voltages for the test mode
        """
        response = self.checkCommand("increment?")
        if not response is "CMD_NOT_DEFINED":
            return float(response)*pq.V
    
    @increment.setter
    def increment(self, newval):
        if newval < 0:
            raise ValueError("Increment voltage must be positive")
        self.sendcmd("increment={}".format(newval))


    ### LCC Methods ###
    def default(self):
        """
        restores factory settings
        returns 1 if successful
        """
        response = self.checkCommand("default")
        if not response is "CMD_NOT_DEFINED":
            return 1
        else:
            return 0

    def save(self):
        """
        stores the parameters in static memory
        returns 1 if successful
        """
        response = self.checkCommand("save")
        if not response is "CMD_NOT_DEFINED":
            return 1
        else:
            return 0

    def setSettings(self,slot):
        """
        saves the current settings to memory
        returns 1 if successful
        """
        if slot < 0:
            raise ValueError("Slot number is less than 0")
        if slot > 4:
            raise ValueError("Slot number is greater than 4")
        response = self.checkCommand("set={}".format(slot))
        if response != "CMD_NOT_DEFINED" and response != "CMD_ARG_INVALID":
            return 1
        else:
            return 0

    def getSettings(self,slot):
        """
        gets the current settings from memory
        returns 1 if successful
        """
        if slot < 0:
            raise ValueError("Slot number is less than 0")
        if slot > 4:
            raise ValueError("Slot number is greater than 4")
        response = self.checkCommand("get={}".format(slot))
        if response != "CMD_NOT_DEFINED" and response != "CMD_ARG_INVALID":
            return 1
        else:
            return 0

    def testMode(self):
        """
        Puts the LCC in test mode - meaning it will increment the output voltage from the minimum value to the maximum value, in increments, waiting for the dwell time
        returns 1 if successful
        """
        response = self.checkCommand("test")
        if not response is "CMD_NOT_DEFINED":
            return 1
        else:
            return 0

