from instruments.abstract_instruments import Instrument
import quantities as pq


class CC1(Instrument):
    """
    The CC1 is a hand-held coincidence counter.
    It has two setting values, the dwell time and the coincidence window. The coincidence window determines the amount of time (in ns) that the two detections may be from each other and still be considered a coincidence. The dwell time is the amount of time that passes before the counter will send the clear signal.
    More information can be found at :
    http://www.qubitekk.com
    """
    def __init__(self, filelike):
        super(CC1, self).__init__(filelike)
        self.terminator = "\n"
        self.endTerminator = "\n"

    def identity(self):
        """
        gets the name and version number of the device
        """
        response = self.query("*idn?")
        if response is "Unknown command":
            self.identity()          
        else:
            return response

    ### CC SETTINGS ###

    @property
    def window(self):
        """
        The length of the coincidence window between the two signals
        """
        response = self.query("w?")
        if not response is "Unknown command":
            response = response[:-3]
            return float(response)*pq.ns
            
    @window.setter
    def window(self, newval):
        if newval < 0:
            raise ValueError("Window is too small.")
        if newval >7:
            raise ValueError("Window is too big")
        self.sendcmd("c{}".format(newval))
    
    @property
    def dwelltime(self):
        """
        The length of time before a clear signal is sent to the counters
        """
        response = self.query("d?")
        if not response is "Unknown command":
            response = response[:-2]
            return float(response)*pq.s
            

    @dwelltime.setter
    def dwelltime(self, newval):
        if newval < 0:
            raise ValueError("Dwell time cannot be negative.")
        self.sendcmd("d{}".format(newval))
            
    @property
    def gateenable(self):
        """
        The Gate mode of the CC
        enabled means the input signals are anded with the gate signal
        disabled means the input signals are not anded with the gate signal
        """
        response = self.query("e?")
        if not response is "Unknown command":
            return response

    @gateenable.setter
    def gateenable(self, newval):
        """
        Set the gate either enabled (1) or disabled (0)
        """
        if newval != 0 and newval != 1:
            raise ValueError("Not a valid output mode")
        self.sendcmd("e{}".format(newval))

    ### return values ###
    
    @property
    def chan1counts(self):
        """
        Channel 1 counts
        """
        response = self.query("c1?")
        if not response is "Unknown command":
            try:
                float(response)
                return response
            except ValueError:
                return self.coinccounts
    
    @property
    def chan2counts(self):
        """
        Channel 2 counts
        """
        response = self.query("c2?")
        if not response is "Unknown command":
            try:
                float(response)
                return response
            except ValueError:
                return self.coinccounts
    
    
    @property
    def coinccounts(self):
        """
        Coincidence counts
        """
        response = self.query("co?")
        if not response is "Unknown command":
            try:
                float(response)
                return response
            except ValueError:
                return self.coinccounts
    
    def getCounts(self):
        chan1counts = self.chan1counts
        chan2counts = self.chan2counts
        coinccounts = self.coinccounts
        return [chan1counts,chan2counts,coinccounts]
    
    ### functions ###
    def clearCounts(self):
        """
        Clears the current total counts on the counters
        """
        self.query("clr")