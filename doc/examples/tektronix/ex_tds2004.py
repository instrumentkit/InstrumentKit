from instruments.tektronix import TekTDS224
from pyqtgraph import QtGui, PlotWidget, PlotCurveItem
from PySide import QtCore
import sys
from numpy import ndarray


class ScopeGui(QtGui.QWidget):
    def __init__(self):
        super(ScopeGui, self).__init__()
        self.instrument_thread = InstrumentThread()
        self.instrument_thread.plot_signal.connect(self.update_plot)

    @QtCore.Slot(ndarray, ndarray)
    def update_plot(self, x_array, y_array):
        self.plot_widget.setXRange(min(x_array), max(x_array))
        self.plot_widget.setYRange(min(y_array), max(y_array))
        self.plot.setData(x=x_array, y=y_array, pen={'color': "FF0", 'width': 2})

    def init_ui(self):
        """
        All definitions for the gui will go here.
        """

        self.main_layout = QtGui.QGridLayout()
        self.plot_widget = PlotWidget()
        self.plot = PlotCurveItem()
        self.plot_widget.addItem(self.plot)
        self.plot.clear()
        self.plot_widget.setLabel('bottom', "Time",
                                  units="s")
        self.plot_widget.setLabel('left', "Signal", units="mV")
        self.plot_widget.setTitle("Scope")

        self.main_layout.addWidget(self.plot_widget, 1, 1, 1, 1)

        self.setLayout(self.main_layout)

        self.setGeometry(0, 0, 1600, 900)
        self.setWindowTitle('Oscilloscope program')
        self.show()
        if not self.instrument_thread.isRunning():
            self.instrument_thread.exiting = False
            self.instrument_thread.start()


class InstrumentThread(QtCore.QThread):
    plot_signal = QtCore.Signal(ndarray, ndarray)

    def __init__(self):
        super(InstrumentThread, self).__init__()
        self.tek = TekTDS224.open_usbtmc(idVendor=0x0699, idProduct=0x0365)

    def get_waveform(self):
        x, y = self.tek.channel[0].read_waveform()
        points_spacing = 5
        self.plot_signal.emit(x[::points_spacing], y[::points_spacing])

    def run(self):
        while True:
            self.get_waveform()


def main():
    """
    Runs the gui on its own
    :return:
    """
    app = QtGui.QApplication(sys.argv)
    testing_gui = ScopeGui()
    testing_gui.init_ui()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()