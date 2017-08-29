import Tkinter as tk
from lapchart_data import chartdata
from data_file_io import load_file, FileFormatException

LC_VERSION = '0.1'

cell_width=34
cell_height=20

FILL_PARENT = tk.N+tk.S+tk.E+tk.W

def visible(cond): return tk.NORMAL if cond else tk.HIDDEN

class LapChartGUICell:
    def __init__(self, canvas, lap, pos):
        self.data = None
        self.canvas = canvas

        x = (lap - 1) * cell_width
        y = (pos - 1) * cell_height
        x0 = x - (cell_width/2)
        y0 = y - (cell_height/2)
        x1 = x + (cell_width/2)
        y1 = y + (cell_height/2)

        self.fill = canvas.create_rectangle(x0, y0, x1, y1, state=tk.HIDDEN,
                width=0, fill="yellow")
        self.text = canvas.create_text(x, y, text='', justify=tk.CENTER)
        self.bar_above = canvas.create_line(x0, y0, x1, y0, state=tk.HIDDEN)
        self.bar_left  = canvas.create_line(x0, y0, x0, y1, state=tk.HIDDEN)

    def set_data(self, data):
        self.data  = data
        self.update()

    def update_bars(self):
        if self.data:
            bars = self.data.bars()
        else:
            bars = (False, False)
        self.canvas.itemconfigure(self.bar_above, state = visible(bars[0]))
        self.canvas.itemconfigure(self.bar_left,  state = visible(bars[1]))
        #self.canvas.itemconfigure(self.fill,      state = visible(bars[0] or bars[1]))

    def update_fill(self):
        #if self.data:
        #    down = self.data.laps_down()
        #else:
        #    down = None
        #if not down:    self.canvas.itemconfigure(self.fill, state=tk.HIDDEN)
        #elif down == 1: self.canvas.itemconfigure(self.fill, state=tk.NORMAL, fill="#8cf")
        #elif down == 2: self.canvas.itemconfigure(self.fill, state=tk.NORMAL, fill="#cfc")
        #elif down == 3: self.canvas.itemconfigure(self.fill, state=tk.NORMAL, fill="#ffc")
        #else:           self.canvas.itemconfigure(self.fill, state=tk.NORMAL, fill="#fcc")
        pass

    def update(self):
        if self.data and self.data.car():
            text = self.data.car().car_no()
            #down = self.data.laps_down()
            #if down is not None: text = text + "\n" + str(down)
            #bars = self.data.bars()
            #text = text + "\n" + ("T" if bars[0] else "F") + ("T" if bars[1] else "F")
        else:
            text = ''
        self.canvas.itemconfigure(self.text, text=text)
        self.update_bars()
        self.update_fill()

class LapChartFrame(tk.Frame):
    def __init__(self, parent):
        self.n_laps = 0
        self.n_pos = 0
        self.cells = []

        # overall frame and scrollbars
        tk.Frame.__init__(self, parent)
        self.lc_vscrollbar = tk.Scrollbar(self, orient=tk.VERTICAL, command = self.yview)
        self.lc_hscrollbar = tk.Scrollbar(self, orient=tk.HORIZONTAL, command = self.xview)

        # create canvases for lap and position labels and the car cells
        self.lap_canvas = tk.Canvas(self, height=cell_height, xscrollcommand=self.lc_hscrollbar.set)
        self.pos_canvas = tk.Canvas(self, width=cell_width, yscrollcommand=self.lc_vscrollbar.set)
        self.lc_canvas = tk.Canvas(self, bg='white',
                xscrollcommand=self.lc_hscrollbar.set,
                yscrollcommand=self.lc_vscrollbar.set)
        self.update_scrollregions()
        self.lap_canvas.xview_moveto(0)
        self.lap_canvas.yview_moveto(0)
        self.pos_canvas.xview_moveto(0)
        self.pos_canvas.yview_moveto(0)
        self.lc_canvas.xview_moveto(0)
        self.lc_canvas.yview_moveto(0)

        # layout
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)
        self.lap_canvas.grid(row=0, column=1, sticky=tk.EW)
        self.pos_canvas.grid(row=1, column=0, sticky=tk.NS)
        self.lc_canvas.grid     (row=1, column=1, sticky=FILL_PARENT)
        self.lc_vscrollbar.grid (row=1, column=2, sticky=tk.NS)
        self.lc_hscrollbar.grid (row=2, column=1, sticky=tk.EW)

        # bind mouse controls
        parent.bind('<Button-4>', self.scroll_event)
        parent.bind('<Button-5>', self.scroll_event)
        parent.bind('<MouseWheel>', self.scroll_event)

    def xview(self, *args):
        # horizontal scroll of body and lap labels
        self.lc_canvas.xview(*args)
        self.lap_canvas.xview(*args)

    def yview(self, *args):
        # vertical scroll of body and position labels
        self.lc_canvas.yview(*args)
        self.pos_canvas.yview(*args)

    def scroll_up   (self, count=1): self.yview(tk.SCROLL, -count, tk.UNITS)
    def scroll_down (self, count=1): self.yview(tk.SCROLL,  count, tk.UNITS)
    def scroll_left (self, count=1): self.xview(tk.SCROLL, -count, tk.UNITS)
    def scroll_right(self, count=1): self.xview(tk.SCROLL,  count, tk.UNITS)
    def scroll_event(self, event):
        if event.type == 4 or event.type == '4':    # Button
            count = 1
            if event.num == 4:   reverse = True
            elif event.num == 5: reverse = False
            else: return
        elif event.type == 38 or event.type == '38': # MouseWheel
            if event.delta < 0:
                count = -event.delta
                reverse = True
            else:
                count = event.delta
                reverse = False
            if not count % 120: count = count // 120  # Kludge for Windows
        else:
            return
        if not count: return
        mods = event.state & 0x8d
        if mods == 0:   # no mods - vertical scroll
            if reverse: self.scroll_up(count)
            else:       self.scroll_down(count)
        elif mods == 1: # shift - horizontal scroll
            if reverse: self.scroll_left(count)
            else:       self.scroll_right(count)
        elif mods == 4: # control - zoom
            if reverse: self.zoom_in(count)
            else:       self.zoom_out(-count)

    def zoom(self, count):
        pass

    def update_scrollregions(self):
        x0 = - (cell_width / 2)
        y0 = - (cell_height / 2)
        width = cell_width * self.n_laps
        height = cell_height * self.n_pos
        self.lap_canvas.config(scrollregion=(x0, y0, width, cell_height))
        self.pos_canvas.config(scrollregion=(x0, y0, cell_width, height))
        self.lc_canvas.config(scrollregion=(x0, y0, width, height))

    def getCell(self, lap, pos):
        update = lap > self.n_laps or pos > self.n_pos
        while lap > self.n_laps:
            self.lap_canvas.create_text(self.n_laps * cell_width, 0, text=self.n_laps+1)
            self.n_laps = self.n_laps + 1
            self.cells.append([])
        while pos > self.n_pos:
            self.pos_canvas.create_text(0, self.n_pos * cell_height, text=self.n_pos+1)
            self.n_pos = self.n_pos + 1
        if update: self.update_scrollregions()
        while pos > len(self.cells[lap-1]):
            cell = LapChartGUICell(self.lc_canvas, lap, len(self.cells[lap-1])+1)
            self.cells[lap-1].append(cell)
        return self.cells[lap-1][pos-1]

        
class LapChartWindow(tk.Toplevel):
    def __init__(self, data=None):
        tk.Toplevel.__init__(self)
        self.title('ChartRoom v%s' % LC_VERSION)
        self.protocol('WM_DELETE_WINDOW', self.closeWindow)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.chart_frame = LapChartFrame(self)
        self.chart_frame.grid(sticky=FILL_PARENT)

        self.menubar = tk.Menu(self)
        self.config(menu=self.menubar)

        menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=menu)
        menu.add_command(label="New", command=self.master.newWindow,
                accelerator="Ctrl+N")
        menu.add_command(label="Close", command=self.closeWindow,
                accelerator="Ctrl+W")
        menu.add_command(label="Quit", command=self.master.quit,
                accelerator="Ctrl+Q")
        if data:
            self.data = data
            data.attach_gui(self)
        else:
            self.data = chartdata(self)

    def getCell(self, lap, pos):
        return self.chart_frame.getCell(lap, pos)

    def closeWindow(self):
        self.destroy()
        self.master._deref()


class LapChartGUI(tk.Tk):
    def __init__(self, files=[], data=None):
        tk.Tk.__init__(self)
        self.overrideredirect(1)
        self.withdraw()
        self.bind_all('<Control-KeyPress-n>', self.newWindow)
        self.bind_all('<Control-KeyPress-w>', self.closeWindow)
        self.bind_all('<Control-KeyPress-q>', self.quitEvent)

        if data:
            self.newWindow(data=data)

        for file in files:
            try:
                self.openFile(file)
            except (FileFormatException, IOError) as e:
                warn("%s: %s" % file, e)

        if not data and not files:
            first = self.newWindow()
            first.data.add('10') # 1, 1
            first.data.add('2',) # 1, 2
            first.data.add('08') # 1, 3
            first.data.add('55') # 1, 4
            first.data.add('42') # 1, 5
            first.data.add('10') # 2, 1
            first.data.add('08') # 2, 2
            first.data.add('2',) # 2, 3
            first.data.add('55') # 2, 4
            first.data.add('08') # 3, 1
            first.data.add('42') # 2, 5
            first.data.add('10') # 3, 2
            first.data.add('2',) # 3, 3
            first.data.add('55') # 3, 4
            first.data.add('15', 1,15)
            first.data.add('1', 14, 1)

    def newWindow(self, event=None, data=None): return LapChartWindow(data)
    def closeWindow(self, event): event.widget.winfo_toplevel().closeWindow()
    def quitEvent(self, event): self.quit()

    def openFile(self, file):
        newdata = chartdata()
        load_file(newdata, file)
        self.newWindow(data=newdata)

    def _deref(self):
        if not self.winfo_children(): self.quit()
