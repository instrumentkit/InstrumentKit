#!/usr/bin/python
# Qubitekk Coincidence Counter example
import matplotlib

matplotlib.use("TkAgg")

from matplotlib.figure import Figure

from numpy import arange, sin, pi
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg

# implement the default mpl key bindings
from matplotlib.backend_bases import key_press_handler
from sys import platform as _platform

import instruments as ik
import tkinter as tk
import re


def clear_counts(*args):
    cc.clear_counts()


def getvalues(i):
    # set counts labels
    chan1counts.set(cc.channel[0].count)
    chan2counts.set(cc.channel[1].count)
    coinc_counts.set(cc.channel[2].count)
    # add count values to arrays for plotting
    chan1vals.append(chan1counts.get())
    chan2vals.append(chan1counts.get())
    coincvals.append(chan1counts.get())
    if cc.channel[0].count < 0:
        chan1counts.set("Overflow")
    if cc.channel[1].count < 0:
        chan2counts.set("Overflow")
    if cc.channel[2].count < 0:
        coinc_counts.set("Overflow")
    t.append(i * time_diff)
    i += 1
    # plot values
    (p1,) = a.plot(t, coincvals, color="r", linewidth=2.0)
    (p2,) = a.plot(t, chan1vals, color="b", linewidth=2.0)
    (p3,) = a.plot(t, chan2vals, color="g", linewidth=2.0)
    a.legend([p1, p2, p3], ["Coincidences", "Channel 1", "Channel 2"])
    a.set_xlabel("Time (s)")
    a.set_ylabel("Counts (Hz)")

    canvas.show()
    # get the values again in the specified amount of time
    root.after(int(time_diff * 1000), getvalues, i)


def gate_enable():
    if gate_enabled.get():
        cc.gate = True
    else:
        cc.gate = False


def subtract_enable():
    if subtract_enabled.get():
        cc.subtract = True
    else:
        cc.subtract = False


def trigger_enable():
    if trigger_enabled.get():
        cc.trigger = cc.TriggerMode.continuous
    else:
        cc.trigger = cc.TriggerMode.start_stop


def parse(*args):
    cc.dwell_time = float(re.sub("[A-z]", "", dwell_time.get()))
    cc.window = float(re.sub("[A-z]", "", window.get()))


def reset(*args):
    cc.reset()
    dwell_time.set(cc.dwell_time)
    window.set(cc.window)
    trigger_enabled.set(cc.count_enable)
    gate_enabled.set(cc.gate_enable)


if __name__ == "__main__":
    cc = ik.qubitekk.CC1.open_serial(vid=1027, pid=24577, baud=19200, timeout=10)
    print(cc.firmware)
    # i is used to keep track of time
    i = 0
    # read counts every 0.5 seconds
    time_diff = 0.5

    root = tk.Tk()
    root.title("Qubitekk Coincidence Counter Control Software")

    # set up the Tkinter grid layout
    mainframe = tk.Frame(root)
    mainframe.padding = "3 3 12 12"
    mainframe.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
    mainframe.columnconfigure(0, weight=1)
    mainframe.rowconfigure(0, weight=1)

    # set up the label text
    dwell_time = tk.StringVar()
    dwell_time.set(cc.dwell_time)

    window = tk.StringVar()
    window.set(cc.window)

    chan1counts = tk.StringVar()
    chan1counts.set(cc.channel[0].count)
    chan2counts = tk.StringVar()
    chan2counts.set(cc.channel[1].count)
    coinc_counts = tk.StringVar()
    coinc_counts.set(cc.channel[2].count)

    gate_enabled = tk.IntVar()
    subtract_enabled = tk.IntVar()
    trigger_enabled = tk.IntVar()

    # set up the initial checkbox value for the gate enable
    if cc.gate:
        gate_enabled.set(1)
    else:
        gate_enabled.set(0)

    # set up the initial checkbox value for the trigger enable
    if cc.subtract:
        subtract_enabled.set(1)
    else:
        subtract_enabled.set(0)

    # set up the initial checkbox value for the trigger enable
    if cc.trigger:
        trigger_enabled.set(1)
    else:
        trigger_enabled.set(0)

    # set up the plotting area

    f = Figure(figsize=(10, 8), dpi=100)
    a = f.add_subplot(111, axisbg="black")

    t = []
    coincvals = []
    chan1vals = []
    chan2vals = []

    # a tk.DrawingArea
    canvas = FigureCanvasTkAgg(f, mainframe)
    canvas.get_tk_widget().grid(column=3, row=1, rowspan=11, sticky=tk.W)

    # label initialization
    dwell_time_entry = tk.Entry(
        mainframe, width=7, textvariable=dwell_time, font="Verdana 20"
    )
    dwell_time_entry.grid(column=2, row=2, sticky=(tk.W, tk.E))
    window_entry = tk.Entry(mainframe, width=7, textvariable=window, font="Verdana 20")
    window_entry.grid(column=2, row=3, sticky=(tk.W, tk.E))

    tk.Label(mainframe, text="Dwell Time:", font="Verdana 20").grid(
        column=1, row=2, sticky=tk.W
    )
    tk.Label(mainframe, text="Window size:", font="Verdana 20").grid(
        column=1, row=3, sticky=tk.W
    )

    tk.Checkbutton(
        mainframe, font="Verdana 20", variable=gate_enabled, command=gate_enable
    ).grid(column=2, row=4)
    tk.Label(mainframe, text="Gate Enable: ", font="Verdana 20").grid(
        column=1, row=4, sticky=tk.W
    )

    tk.Checkbutton(
        mainframe, font="Verdana 20", variable=subtract_enabled, command=subtract_enable
    ).grid(column=2, row=5)
    tk.Label(mainframe, text="Subtract Accidentals: ", font="Verdana 20").grid(
        column=1, row=5, sticky=tk.W
    )

    tk.Checkbutton(
        mainframe, font="Verdana 20", variable=trigger_enabled, command=trigger_enable
    ).grid(column=2, row=6)
    tk.Label(mainframe, text="Continuous Trigger: ", font="Verdana 20").grid(
        column=1, row=6, sticky=tk.W
    )

    tk.Label(mainframe, text="Channel 1: ", font="Verdana 20").grid(
        column=1, row=7, sticky=tk.W
    )
    tk.Label(mainframe, text="Channel 2: ", font="Verdana 20").grid(
        column=1, row=8, sticky=tk.W
    )
    tk.Label(mainframe, text="Coincidences: ", font="Verdana 20").grid(
        column=1, row=9, sticky=tk.W
    )

    tk.Label(
        mainframe, textvariable=chan1counts, font="Verdana 34", fg="white", bg="black"
    ).grid(column=2, row=7, sticky=tk.W)
    tk.Label(
        mainframe, textvariable=chan2counts, font="Verdana 34", fg="white", bg="black"
    ).grid(column=2, row=8, sticky=tk.W)
    tk.Label(
        mainframe, textvariable=coinc_counts, font="Verdana 34", fg="white", bg="black"
    ).grid(column=2, row=9, sticky=tk.W)

    tk.Button(mainframe, text="Reset", font="Verdana 24", command=reset).grid(
        column=1, row=10, sticky=tk.W
    )

    tk.Button(
        mainframe, text="Clear Counts", font="Verdana 24", command=clear_counts
    ).grid(column=2, row=10, sticky=tk.W)

    tk.Label(
        mainframe, text="Firmware Version: " + str(cc.firmware), font="Verdana 20"
    ).grid(column=1, row=11, columnspan=2, sticky=tk.W)

    for child in mainframe.winfo_children():
        child.grid_configure(padx=5, pady=5)
    # when the enter key is pressed, send the current values in the entries to the dwelltime and window to the
    # coincidence counter
    root.bind("<Return>", parse)
    # in 100 milliseconds, get the counts values off of the coincidence counter
    root.after(int(time_diff * 1000), getvalues, i)
    # start the GUI
    root.mainloop()
