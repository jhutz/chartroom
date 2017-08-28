import Tkinter as tk

cell_width=34
cell_height=20

FILL_PARENT = tk.N+tk.S+tk.E+tk.W

class LapChartGUICell:
    def __init__(self, canvas, frame, lap, pos):
        self.data  = None
        self.car_v = tk.StringVar()
        self.bar_above = None
        self.bar_left = None

        self.canvas = canvas
        self.frame = frame
        self.car_lbl = tk.Label(self.frame, anchor=tk.CENTER,
                bg="white", textvariable=self.car_v)
        #if lap == pos: self.car_lbl.config(bg="yellow")
        self.car_lbl.grid(column=lap-1, row=pos-1, sticky=FILL_PARENT)

    def set_data(self, data):
        self.data  = data
        self.update()

    def update_bars(self):
        if self.data:
            bars = self.data.bars()
        else:
            bars = (False, False)
        if self.bar_above is not None:
            self.canvas.itemconfigure(self.bar_above,
                    state = tk.NORMAL if bars[0] else tk.DISABLED)
        if self.bar_left is not None:
            self.canvas.itemconfigure(self.bar_left,
                    state = tk.NORMAL if bars[1] else tk.DISABLED)
        if bars[0] or bars[1]:
            self.car_lbl.config(bg="yellow")
        else:
            self.car_lbl.config(bg="white")

    def update(self):
        if self.data:
            car = self.data.car()
            if car: self.car_v.set(car.car_no())
            else: self.car_v.set('')
        else:
            self.car_v.set('')
        self.update_bars()

class LapChartFrame(tk.Frame):
    def __init__(self, master):
        self.n_laps = 0
        self.n_pos = 0
        self.cells = []

        # overall frame and scrollbars
        tk.Frame.__init__(self, master)
        self.lc_vscrollbar = tk.Scrollbar(self, orient=tk.VERTICAL, command = self.yview)
        self.lc_hscrollbar = tk.Scrollbar(self, orient=tk.HORIZONTAL, command = self.xview)

        # canvases for lap and position labels
        self.lap_canvas = tk.Canvas(self, height=cell_height, xscrollcommand=self.lc_hscrollbar.set)
        self.pos_canvas = tk.Canvas(self, width=cell_width, yscrollcommand=self.lc_vscrollbar.set)
        self.update_scrollregions()
        self.lap_canvas.xview_moveto(0)
        self.lap_canvas.yview_moveto(0)
        self.pos_canvas.xview_moveto(0)
        self.pos_canvas.yview_moveto(0)

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

    def update_scrollregions(self):
        x0 = - (cell_width / 2)
        y0 = - (cell_height / 2)
        width = cell_width * self.n_laps
        height = cell_height * self.n_pos
        self.lap_canvas.config(scrollregion=(x0, y0, width, cell_height))
        self.pos_canvas.config(scrollregion=(x0, y0, cell_width, height))
        #self.lc_canvas.config(scrollregion=(x0, y0, width, height))

    def _configure_lc_frame(self, event):
        # adjust body frame for window resize
        w = self.lc_frame.winfo_reqwidth()
        h = self.lc_frame.winfo_reqheight()
        self.lc_canvas.config(scrollregion="0 0 %s %s" % (w,h))

    def _configure_lc_canvas(self, event): pass

    def getCell(self, lap, pos):
        update = lap > self.n_laps or pos > self.n_pos
        while lap > self.n_laps:
            self.lap_canvas.create_text(self.n_laps * cell_width, 0, text=self.n_laps+1)
            self.lc_frame.columnconfigure(self.n_laps, minsize=cell_width)
            cell = LapChartGUICell(self.lc_canvas, self.lc_frame, self.n_laps+1, 1)
            self.cells.append([cell])
            self.n_laps = self.n_laps + 1
        while pos > self.n_pos:
            self.pos_canvas.create_text(0, self.n_pos * cell_height, text=self.n_pos+1)
            self.lc_frame.rowconfigure(self.n_pos, minsize=cell_height)
            self.n_pos = self.n_pos + 1
        if update: self.update_scrollregions()
        while pos > len(self.cells[lap-1]):
            cell = LapChartGUICell(self.lc_canvas, self.lc_frame,
                    lap, len(self.cells[lap-1])+1)
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
