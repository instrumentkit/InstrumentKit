from instruments.abstract_instruments import Instrument
import quantities as pq


class SC10(Instrument):
    """
    The SC10 is a shutter controller, to be used with the Thorlabs SH05 and SH1.
    The user manual can be found here:
    http://www.thorlabs.com/thorcat/8600/SC10-Manual.pdf
    """
    def __init__(self, filelike):
        super(SC10, self).__init__(filelike)
        self.terminator = "\n"
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
        response = self.checkCommand("id?")
        if response is "CMD_NOT_DEFINED":
            self.identity()          
        else:
            return response

    ### LCC SETTINGS ###

    @property
    def enable(self):
        """
        The shutter enable status, 0 for disabled, 1 if enabled
        """
        response = self.checkCommand("ens?")
        if not response is "CMD_NOT_DEFINED":
            return response
    @enable.setter
    def enable(self, newval):
        if newval == 0 or newval ==1:
            self.sendcmd("ens={}".format(newval))
        else:
            raise ValueError("Invalid value for enable, must be 0 or 1")        

    @property
    def repeat(self):
        """
        The repeat count for repeat mode. 
        """
        response = self.checkCommand("rep?")
        if not response is "CMD_NOT_DEFINED":
            return response
    @repeat.setter
    def repeat(self, newval):
        if newval >0 or newval <100:
            self.sendcmd("rep={}".format(newval))
        else:
            raise ValueError("Invalid value for repeat count, must be between 1 and 99")        

    @property
    def mode(self):
        """
        The output mode of the SC10
        mode 1 Manual Mode
        mode 2 Auto Mode
        mode 3 Single Mode
        mode 4 Repeat Mode
        mode 5 External Gate Mode
        """
        response = self.checkCommand("mode?")
        if not response is "CMD_NOT_DEFINED":
            return float(response)
    @mode.setter
    def mode(self, newval):
        if newval >0  and newval < 6:
            self.sendcmd("mode={}".format(newval))
        else:
            raise ValueError("Not a valid operation mode")
    
    @property
    def trigger(self):
        """
        0 for internal trigger, 1 for external trigger
        """
        response = self.checkCommand("trig?")
        if not response is "CMD_NOT_DEFINED":
            return float(response)
    @trigger.setter
    def trigger(self, newval):
        if newval != 0 and newval != 1:
            raise ValueError("Not a valid value for trigger mode")
        self.sendcmd("trig={}".format(newval))

    
    @property
    def outtrigger(self):
        """
        0 trigger out follows shutter output, 1 trigger out follows controller output
        """
        response = self.checkCommand("xto?")
        if not response is "CMD_NOT_DEFINED":
            return float(response)
    @outtrigger.setter
    def outtrigger(self, newval):
        if newval != 0 and newval != 1:
            raise ValueError("Not a valid value for output trigger mode")
        self.sendcmd("xto={}".format(newval))

    ###I'm not sure how to handle checking for the number of digits yet.
    @property
    def opentime(self):
        """
        The amount of time that the shutter is open, in ms
        """
        response = self.checkCommand("open?")
        print(response)
        if not response is "CMD_NOT_DEFINED":
            return float(response)*pq.ms
    @opentime.setter
    def opentime(self, newval):
        if newval < 0:
            raise ValueError("Time cannot be negative")
        if newval >999999:
            raise ValueError("Duration is too long")
        self.sendcmd("open={}".format(newval))
    @property
    def shuttime(self):
        """
        The amount of time that the shutter is closed, in ms
        """
        response = self.checkCommand("shut?")
        if not response is "CMD_NOT_DEFINED":
            return float(response)*pq.ms
    @shuttime.setter
    def shuttime(self, newval):
        if newval < 0:
            raise ValueError("Time cannot be negative")
        if newval >999999:
            raise ValueError("Duration is too long")
        self.sendcmd("shut={}".format(newval))
    @property
    def baudrate(self):
        """
        Gets the baud rate: 0 for 9600, 1 for 115200
        """
        response = self.checkCommand("baud?")
        if not response is "CMD_NOT_DEFINED":
            return float(response)*pq.ms
    @baudrate.setter
    def baudrate(self, newval):
        if newval != 0 and newval !=1:
            raise ValueError("invalid baud rate mode")
        else:
            self.sendcmd("baud={}".format(newval))
    
    @property
    def closed(self):
        """
        1 if the shutter is closed, 0 if the shutter is open
        """
        response = self.checkCommand("closed?")
        if not response is "CMD_NOT_DEFINED":
            return float(response)
    @property
    def interlock(self):
        """
        1 if the interlock is tripped, 0 otherwise
        """
        response = self.checkCommand("interlock?")
        if not response is "CMD_NOT_DEFINED":
            return float(response)

    ### SC10 Methods ###
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
        response = self.checkCommand("savp")
        if not response is "CMD_NOT_DEFINED":
            return 1
        else:
            return 0

    def savemode(self):
        """
        stores output trigger mode and baud rate in memory
        """
        response = self.checkCommand("save")
        if not response is "CMD_NOT_DEFINED":
            return 1
        else:
            return 0

    def restore(self):
        """
        loads the settings from memory
        """
        response = self.checkCommand("resp")
        if not response is "CMD_NOT_DEFINED":
            return 1
        else:
            return 0