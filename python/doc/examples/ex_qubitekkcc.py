#Qubitekk Coincidence Counter example
import matplotlib
matplotlib.use('TkAgg')

from matplotlib.figure import Figure

from numpy import arange, sin, pi
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
# implement the default mpl key bindings
from matplotlib.backend_bases import key_press_handler

import instruments as ik

import Tkinter as tk

#windows example
cc = ik.qubitekk.CC1.open_serial('COM8', 19200,timeout=1)
i = 0
def clearcounts(*args):
    try:
        cc.clearCounts()
    except ValueError:
        pass

def getvalues(i):
    chan1counts.set(cc.chan1counts)
    chan2counts.set(cc.chan2counts)
    coinccounts.set(cc.coinccounts)
    chan1vals.append(cc.chan1counts)
    chan2vals.append(cc.chan2counts)
    coincvals.append(cc.coinccounts)
    t.append(i*0.1)
    i = i+1
    p1, = a.plot(t,coincvals,color="r",linewidth=2.0)
    p2, = a.plot(t,chan1vals,color="b",linewidth=2.0)
    p3, = a.plot(t,chan2vals,color="g",linewidth=2.0)
    a.legend([p1,p2,p3],["Coincidences","Channel 1", "Channel 2"])
    a.set_xlabel('Time (s)')
    a.set_ylabel('Counts (Hz)')

    canvas.show()
    root.after(100,getvalues,i)
root = tk.Tk()
root.title("Qubitekk Coincidence Counter Control Software")

mainframe = tk.Frame(root)
mainframe.padding = "3 3 12 12"
mainframe.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
mainframe.columnconfigure(0, weight=1)
mainframe.rowconfigure(0, weight=1)

dwelltime = tk.StringVar()
dwelltime.set(cc.dwelltime)

window = tk.StringVar()
window.set(cc.window)

gateenabled = tk.IntVar()

if(cc.gateenabled=="enabled"):
    gateenabled = 1
else:
    gateenabled = 0


chan1counts = tk.StringVar()
chan1counts.set(cc.chan1counts)
chan2counts = tk.StringVar()
chan2counts.set(cc.chan2counts)
coinccounts = tk.StringVar()
coinccounts.set(cc.coinccounts)

f = Figure(figsize=(5,4), dpi=100)
a = f.add_subplot(111,axisbg='black')

t = []
coincvals = []
chan1vals = []
chan2vals = []


# a tk.DrawingArea
canvas = FigureCanvasTkAgg(f, mainframe)
canvas.get_tk_widget().grid(column=3,row=1,rowspan=8,sticky=tk.W)

#canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

#toolbar = NavigationToolbar2TkAgg( canvas, root )
#toolbar.update()
#canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)



dwelltime_entry = tk.Entry(mainframe, width=7, textvariable=dwelltime,font="Verdana 20")
dwelltime_entry.grid(column=2,row=2,sticky=(tk.W,tk.E))
window_entry = tk.Entry(mainframe, width=7, textvariable=window,font="Verdana 20")
window_entry.grid(column=2,row=3,sticky=(tk.W,tk.E))
qubitekklogo = tk.PhotoImage(file="qubitekklogo.gif")

tk.Label(mainframe,image=qubitekklogo).grid(column=1,row=1,columnspan=2)

tk.Label(mainframe, text="Dwell Time:",font="Verdana 20").grid(column=1,row=2,sticky=tk.W)
tk.Label(mainframe, text="Window size:",font="Verdana 20").grid(column=1,row=3,sticky=tk.W)

tk.Checkbutton(mainframe,font="Verdana 20",variable = gateenabled).grid(column=2,row=4)
tk.Label(mainframe,text="Gate Enable: ",font="Verdana 20").grid(column=1,row=4,sticky=tk.W)


tk.Label(mainframe, text="Channel 1: ",font="Verdana 20").grid(column=1,row=5,sticky=tk.W)
tk.Label(mainframe, text="Channel 2: ",font="Verdana 20").grid(column=1,row=6,sticky=tk.W)
tk.Label(mainframe, text="Coincidences: ",font="Verdana 20").grid(column=1,row=7,sticky=tk.W)



tk.Label(mainframe, textvariable=chan1counts,font="Verdana 24",fg="white",bg="black").grid(column=2,row=5,sticky=tk.W)
tk.Label(mainframe, textvariable=chan2counts,font="Verdana 24",fg="white",bg="black").grid(column=2,row=6,sticky=tk.W)
tk.Label(mainframe, textvariable=coinccounts,font="Verdana 24",fg="white",bg="black").grid(column=2,row=7,sticky=tk.W)

tk.Button(mainframe,text="Clear Counts",command=clearcounts).grid(column=2,row=8,sticky = tk.W)

for child in mainframe.winfo_children(): child.grid_configure(padx=5, pady=5)

root.after(100,getvalues,i)
root.mainloop()