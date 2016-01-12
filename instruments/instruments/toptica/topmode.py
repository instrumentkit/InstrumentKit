import quantities as pq
from flufl.enum import IntEnum

from instruments.abstract_instruments import Instrument

class Laser(object):
    """
    Since the topmode can have multiple lasers attached to it, a laser object will be defined.
    """
    def __init__(self, filelike,

class TopMode(Instrument):
    """
    The TopMode is a diode laser with active stabilization, produced by Toptica.
    The spec sheet is available here:
    http://www.toptica.com/fileadmin/user_upload/products/Diode_Lasers/Industrial_OEM/Single_Frequency/TopMode/toptica_BR_TopMode.pdf
    """
    def __init__(self, filelike):
        super(TopMode, self).__init__(filelike)
        self.prompt = ">"
        self.terminator = "\n"
        self.echo = False

    # The TopMode has its own control language, here we define each command individually:
    def execute(self, command):
        self.sendcmd("(exec '"+command+")")

    def set(self, param, value):
        if type(value) is str:
            self.sendcmd("(param-set! '"+param+" \""+value+"\")")
        elif type(value) is tuple or type(value) is list:
            self.sendcmd("(param-set! '"+param+" '("+value.join(" ")+"))")
        elif type(value) is bool:
            out_str = "t" if value else "f"
            self.sendcmd("(param-set! '"+param+" #"+out_str+")")

    def reference(self, param):
        return self.query("(param-ref '"+param+")")

    def display(self, param):
        return self.query("(param-disp '"+param+")")

    @property
    def enable(self):
        """
        is the laser lasing?
        :return:
        """
    @enable.setter
    def enable(self, newenable):

    @property
    def locked(self):
        """
        Is the key switch unlocked?
        :return:
        """

    @property
    def interlock(self):
        """
        Is the interlock switch open?
        :return:
        """

    @property