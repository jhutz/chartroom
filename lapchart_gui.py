import Tkinter as tk

lap_col_size=35
pos_row_size=20

FILL_PARENT = tk.N+tk.S+tk.E+tk.W

class LapChartGUICell:
    def __init__(self, canvas, lap, pos):
        self.car  = None
        self.lead = None
        self.car_v = tk.StringVar()

        self.canvas = canvas
        self.car_lbl = tk.Label(self.canvas, anchor=tk.CENTER,
                bg="white", textvariable=self.car_v)
        self.car_lbl.grid(column=lap-1, row=pos-1)

    def set(self, car, lead=None):
        self.car  = car
        self.lead = lead
        if car == None: self.car_v.set('')
        else:           self.car_v.set(self.car.car_no())

class LapChartFrame(tk.Frame):
    def __init__(self, master):
        self.cells = []
        self.lap_lbls = []
        self.pos_lbls = []

        # overall frame and scrollbars
        tk.Frame.__init__(self, master)
        self.lc_vscrollbar = tk.Scrollbar(self, orient=tk.VERTICAL, command = self.yview)
        self.lc_hscrollbar = tk.Scrollbar(self, orient=tk.HORIZONTAL, command = self.xview)

        # canvas and frame for lap labels (across top)
        self.lap_canvas = tk.Canvas(self, xscrollcommand=self.lc_hscrollbar.set)
        self.lap_frame  = tk.Frame(self.lap_canvas)
        self.lap_objid = self.lap_canvas.create_window(0, 0, window=self.lap_frame, anchor=tk.NW)
        self.lap_frame.bind('<Configure>', self._configure_lap_frame)
        self.lap_canvas.bind('<Configure>', self._configure_lap_canvas)

        # canvas and frame for position labels (down side)
        self.pos_canvas = tk.Canvas(self, yscrollcommand=self.lc_vscrollbar.set)
        self.pos_frame = tk.Frame(self.pos_canvas)
        self.pos_objid = self.pos_canvas.create_window(0, 0, window=self.pos_frame, anchor=tk.NW)
        self.pos_frame.bind('<Configure>', self._configure_pos_frame)
        self.pos_canvas.bind('<Configure>', self._configure_pos_canvas)

        # canvas and frame for lap chart body
        self.lc_canvas = tk.Canvas(self, bg='white',
                xscrollcommand=self.lc_hscrollbar.set,
                yscrollcommand=self.lc_vscrollbar.set)
        self.lc_frame = tk.Frame(self.lc_canvas, bg='white')
        self.lc_objid = self.lc_canvas.create_window(0, 0, window=self.lc_frame, anchor=tk.NW)
        self.lc_frame.bind('<Configure>', self._configure_lc_frame)
        self.lc_canvas.bind('<Configure>', self._configure_lc_canvas)

        # layout
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)
        self.lap_canvas.grid(row=0, column=1, sticky=tk.EW)
        self.pos_canvas.grid(row=1, column=0, sticky=tk.NS)
        self.lc_canvas.grid     (row=1, column=1, sticky=FILL_PARENT)
        self.lc_vscrollbar.grid (row=1, column=2, sticky=tk.NS)
        self.lc_hscrollbar.grid (row=2, column=1, sticky=tk.EW)

    def xview(self, *args):
        # horizontal scroll of body and lap labels
        self.lc_canvas.xview(*args)
        self.lap_canvas.xview(*args)

    def yview(self, *args):
        # vertical scroll of body and position labels
        self.lc_canvas.yview(*args)
        self.pos_canvas.yview(*args)

    def _configure_lap_frame(self, event):
        # adjust lap labels canves for frame content change
        w = self.lap_frame.winfo_reqwidth()
        h = self.lap_frame.winfo_reqheight()
        self.lap_canvas.config(scrollregion="0 0 %s %s" % (w,h))
        if h != self.lap_canvas.winfo_height():
            self.lap_canvas.config(height=h)

    def _configure_pos_frame(self, event):
        # adjust position labels canves for frame content change
        w = self.pos_frame.winfo_reqwidth()
        h = self.pos_frame.winfo_reqheight()
        self.pos_canvas.config(scrollregion="0 0 %s %s" % (w,h))
        if w != self.pos_canvas.winfo_width():
            self.pos_canvas.config(width=w)

    def _configure_lc_frame(self, event):
        # adjust body frame for window resize
        w = self.lc_frame.winfo_reqwidth()
        h = self.lc_frame.winfo_reqheight()
        self.lc_canvas.config(scrollregion="0 0 %s %s" % (w,h))

    def _configure_lap_canvas(self, event):
        # adjust lap labels frame for window resize
        h = self.lap_frame.winfo_reqheight()
        ch = self.lap_canvas.winfo_height()
        if h != ch:
            self.lap_canvas.itemconfigure(self.lap_objid, height=ch)

    def _configure_pos_canvas(self, event):
        # adjust position labels frame for window resize
        w = self.pos_frame.winfo_reqwidth()
        cw = self.pos_canvas.winfo_width()
        if w != cw:
            self.pos_canvas.itemconfigure(self.pos_objid, width=cw)

    def _configure_lc_canvas(self, event): pass

    def getCell(self, lap, pos):
        while lap > len(self.lap_lbls):
            i = len(self.lap_lbls)
            self.lc_frame.columnconfigure(i, minsize=lap_col_size)
            self.lap_frame.columnconfigure(i, minsize=lap_col_size)
            lbl = tk.Label(self.lap_frame, anchor=tk.CENTER, text=i+1)
            lbl.grid(row=0, column=i, sticky=FILL_PARENT)
            self.lap_lbls.append(lbl)
            cell = LapChartGUICell(self.lc_frame, i+1, 1)
            self.cells.append([cell])
        while pos > len(self.pos_lbls):
            i = len(self.pos_lbls)
            self.lc_frame.rowconfigure(i, minsize=pos_row_size)
            self.pos_frame.rowconfigure(i, minsize=pos_row_size)
            lbl = tk.Label(self.pos_frame, anchor=tk.E, text=i+1)
            lbl.grid(row=i, column=0, sticky=tk.E)
            self.pos_lbls.append(lbl)
        while pos > len(self.cells[lap-1]):
            cell = LapChartGUICell(self.lc_frame, lap, len(self.cells[lap-1])+1)
            self.cells[lap-1].append(cell)
        return self.cells[lap-1][pos-1]

        
class LapChartGUI(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.winfo_toplevel().rowconfigure(0, weight=1)
        self.winfo_toplevel().columnconfigure(0, weight=1)
        self.grid(sticky=FILL_PARENT)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.chart_frame = LapChartFrame(self)
        self.chart_frame.grid(sticky=FILL_PARENT)

        self.menubar = tk.Menu(self)
        self.master.config(menu=self.menubar)

        menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=menu)
        menu.add_command(label="Quit", command=self.quit,
                accelerator="Ctrl+Q")
        self.bind_all('<Control-KeyPress-q>', self.quitEvent)

    def getCell(self, lap, pos):
        return self.chart_frame.getCell(lap, pos)

    def quitEvent(self, event): self.quit()
