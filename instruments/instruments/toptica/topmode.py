import quantities as pq
from flufl.enum import IntEnum
from datetime import datetime

from instruments.abstract_instruments import Instrument


def convert_toptica_boolean(response):
    """
    Converts the toptica boolean expression to a boolean
    :param response: response string
    :type response: str
    :return: the converted boolean
    :rtype: bool
    """
    if response.find('f')>-1:
        return False
    elif response.find('t')>-1:
        return True
    else:
        raise ValueError("cannot convert: "+str(response)+" to boolean")


def convert_toptica_datetime(response):
    """
    Converts the toptical date format to a python time date
    :param response: the string from the topmode
    :type response: str
    :return: the converted date
    :rtype: 'datetime.datetime'
    """
    return datetime.strptime(response, '%b %d %Y %I:%M%p')


class TopMode(Instrument):
    """
    The TopMode is a diode laser with active stabilization, produced by Toptica.
    The spec sheet is available here:
    http://www.toptica.com/fileadmin/user_upload/products/Diode_Lasers/Industrial_OEM/Single_Frequency/TopMode/toptica_BR_TopMode.pdf
    """
    class CharmStatus(IntEnum):
        un_initialized = 0
        in_progress = 1
        success = 2
        failure = 3

    class Laser(object):
        """
        Since the topmode can have multiple lasers attached to it, a laser object will be defined.
        """
        def __init__(self, number=1, parent=None):
            self.number = number
            self.parent = parent
            self.name = "laser"+str(self.number)

        @property
        def serial_number(self):
            return self.parent.reference(self.name+":serial-number")

        @property
        def model(self):
            return self.parent.reference(self.name+":model")

        @property
        def wavelength(self):
            return float(self.parent.reference(self.name+":wavelength"))*pq.nm

        @property
        def production_date(self):
            return self.parent.reference(self.name+":production-date")

        @property
        def enable(self):
            return convert_toptica_boolean(self.parent.reference(self.name+":emission"))

        @enable.setter
        def enable(self, newval):
            if type(newval) is not bool:
                raise TypeError("Laser emmission must be a boolean, got: "+type(newval))
            return self.parent.set(self.name+":enable-emission", newval)

        @property
        def on_time(self):
            return float(self.parent.reference(self.name+":ontime"))*pq.s

        @property
        def charm_status(self):
            response = int(self.parent.reference(self.name+":health"))
            return (response >> 7) % 2

        @property
        def temperature_control_status(self):
            response = int(self.parent.reference(self.name+":health"))
            return (response >> 5) % 2

        @property
        def current_control_status(self):
            response = int(self.parent.reference(self.name+":health"))
            return (response >> 6) % 2

        @property
        def tec_status(self):
            return convert_toptica_boolean(self.parent.reference(self.name+":tec:ready"))

        @property
        def intensity(self):
            """
            This parameter is unitless
            """
            return convert_toptica_boolean(self.parent.reference(self.name+":intensity"))

        @property
        def mode_hop(self):
            """
            Checks whether the laser has mode-hopped
            """
            return convert_toptica_boolean(self.parent.reference(self.name+":charm:reg:mh-occured"))

        @property
        def lock_start(self):
            """
            Returns the date and time of the start of mode-locking
            """
            return convert_toptica_datetime(self.parent.reference(self.name+":charm:reg:started"))

        @property
        def first_mode_hop_time(self):
            """
            Returns the date and time of the first mode hop
            """
            return convert_toptica_datetime(self.parent.reference(self.name+":charm:reg:first-mh"))

        @property
        def latest_mode_hop_time(self):
            """
            Returns the date and time of the latest mode hop
            """
            return convert_toptica_datetime(self.parent.reference(self.name+":charm:reg:latest-mh"))

        @property
        def correction_status(self):
            return TopMode.CharmStatus[int(self.parent.reference(self.name+":charm:correction-status"))]

        def correction(self):
            """
            run the correction
            """
            if self.correction_status == TopMode.CharmStatus.un_initialized:
                self.parent.execute(self.name+":charm:start-correction-initial")
            else:
                self.parent.execute(self.name+":charm:start-correction")


    def __init__(self, filelike):
        super(TopMode, self).__init__(filelike)
        self.prompt = ">"
        self.terminator = "\n"
        self.echo = False
        self.laser1 = TopMode.Laser(1, self)
        self.laser2 = TopMode.Laser(2, self)

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
        return convert_toptica_boolean(self.reference("emission"))

    @enable.setter
    def enable(self, newenable):
        if type(newenable) is not bool:
            raise TypeError("Emission status must be a boolean, got: "+str(type(newenable)))
        self.set("enable-emission", newenable)

    @property
    def locked(self):
        """
        Is the key switch unlocked?
        :return:
        """
        return convert_toptica_boolean(self.reference("front-key-locked"))

    @property
    def interlock(self):
        """
        Is the interlock switch open?
        :return:
        """
        return convert_toptica_boolean(self.reference("interlock-open"))

    @property
    def fpga_status(self):
        """
        returns false on FPGA failure
        :return:
        """
        response = int(self.reference("system-health"))
        return False if response % 2 else True

    @property
    def temperature_status(self):
        """
        returns false if there is a temperature controller board failure
        :return:
        """
        response = int(self.reference("system-health"))
        return False if (response >> 1) % 2 else True

    @property
    def current_status(self):
        """
        returns false if there is a current controller board failure
        :return:
        """
        response = int(self.reference("system-health"))
        return False if (response >> 2) % 2 else True

    def reboot(self):
        """
        Reboots the system (note, this will end the serial connection)
        """
        self.execute("reboot-system")


    ## Network configuration is unimplemented

