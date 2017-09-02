import Tkinter as tk
import tkFileDialog
import os.path
from lapchart_data import chartdata
from data_file_io import load_file, save_data_file
from data_file_io import FileFormatException
from printing import save_ps
from config_data import *

cell_width=34
cell_height=20

FILL_PARENT = tk.N+tk.S+tk.E+tk.W

highlights = [
        (HIGHLIGHT_CARS, 'Cars'),
        (HIGHLIGHT_LAP,  'Lead Lap'),
        ]
highlight_label = { k:v for (k,v) in highlights }
highlight_mode  = { v:k for (k,v) in highlights }
shadings = [
        (SHADE_NONE,  'nothing'),
        (SHADE_CLASS, 'by class'),
        (SHADE_DOWN,  'by laps down'),
        ]
shading_label = { k:v for (k,v) in shadings }
shading_mode  = { v:k for (k,v) in shadings }

def visible(cond): return tk.NORMAL if cond else tk.HIDDEN

class LapChartGUICell:
    def __init__(self, canvas, fill_state, lap, pos):
        self.data = None
        self.canvas = canvas
        self.fill_state = fill_state
        self.lap = lap
        self.pos = pos

        x = (lap - 1) * cell_width
        y = (pos - 1) * cell_height
        x0 = x - (cell_width/2)
        y0 = y - (cell_height/2)
        x1 = x + (cell_width/2)
        y1 = y + (cell_height/2)

        self.fill = canvas.create_rectangle(x0, y0, x1, y1, state=tk.HIDDEN,
                width=0, tags="cell")
        self.text = canvas.create_text(x, y, text='', justify=tk.CENTER, tags="cell_text")
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

    def update_fill(self):
        if not self.data:
            self.canvas.itemconfigure(self.fill, state=tk.HIDDEN)
            return

        down = self.data.laps_down()
        car_no = self.data.car().car_no()
        lead = self.data.lead()
        if self.fill_state[0] == HIGHLIGHT_CARS and car_no in self.fill_state[1]:
            self.canvas.itemconfigure(self.fill, state=tk.NORMAL, fill=config.highlight_color)
        elif self.fill_state[0] == HIGHLIGHT_LAP and str(lead) in self.fill_state[1]:
            self.canvas.itemconfigure(self.fill, state=tk.NORMAL, fill=config.highlight_color)
        elif self.fill_state[2] == SHADE_CLASS:
            class_ = self.data.car().class_()
            pass # XXX
        elif self.fill_state[2] == SHADE_DOWN and down:
            if down > len(config.laps_down_colors):
                self.canvas.itemconfigure(self.fill, state=tk.NORMAL,
                        fill=config.laps_down_colors[-1])
            else:
                self.canvas.itemconfigure(self.fill, state=tk.NORMAL,
                        fill=config.laps_down_colors[down-1])
        else:
            self.canvas.itemconfigure(self.fill, state=tk.HIDDEN)

    def update(self):
        text_tags = ['cell_text']
        fill_tags = ['cell']
        text = ''
        if self.data and self.data.car():
            car_no = self.data.car().car_no()
            class_ = self.data.car().class_()
            lead = self.data.lead()
            down = self.data.laps_down()
            text = car_no
            fill_tags.append('car_%s' % text)
            if class_ is not None: fill_tags.append('class_%s' % class_)
            if down   is not None: fill_tags.append('down_%d' % down)
            if lead   is not None:
                fill_tags.append('lead_%d' % lead)
                text_tags.append('lead_%d_text' % lead)
        else:
            text = ''
        self.canvas.itemconfigure(self.text, text=text, tags=text_tags)
        self.canvas.itemconfigure(self.fill, tags=fill_tags)
        self.update_bars()
        self.update_fill()

class LapChartFrame(tk.Frame):
    def __init__(self, parent, data, fill_state):
        self.n_laps = 0
        self.n_pos = 0
        self.cells = []
        self.data = data
        self.fill_state = fill_state

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
        self.rowconfigure(2, weight=1)
        tk.Label(self, text='Laps').grid(row=0, column=1, sticky=tk.NS+tk.W)
        tk.Label(self, text='Pos').grid(row=1, column=0, sticky=FILL_PARENT)
        self.lap_canvas.grid(row=1, column=1, sticky=tk.EW)
        self.pos_canvas.grid(row=2, column=0, sticky=tk.NS)
        self.lc_canvas.grid     (row=2, column=1, sticky=FILL_PARENT)
        self.lc_vscrollbar.grid (row=2, column=2, sticky=tk.NS)
        self.lc_hscrollbar.grid (row=3, column=1, sticky=tk.EW)

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

    def update_fills(self, highlight, items, shade):
        self.fill_state[:] = [ highlight, items, shade ]
        self.lc_canvas.itemconfigure('cell', state=tk.HIDDEN)
        if self.fill_state[2] == SHADE_CLASS:
            for (cls,color) in zip(self.data.classes(), config.class_colors):
                self.lc_canvas.itemconfigure("class_%s" % cls, state=tk.NORMAL, fill=color)
        elif self.fill_state[2] == SHADE_DOWN:
            n = min(self.data.max_down(), len(config.laps_down_colors))
            for i in range(n):
                self.lc_canvas.itemconfigure("down_%d" % (i+1),
                        state=tk.NORMAL, fill=config.laps_down_colors[i])
            if n < self.data.max_down():
                for i in range(n, self.data.max_down()):
                    self.lc_canvas.itemconfigure("down_%d" % i,
                            state=tk.NORMAL, fill=config.laps_down_colors[-1])
        if self.fill_state[0] == HIGHLIGHT_CARS:
            for car in self.fill_state[1]:
                self.lc_canvas.itemconfigure("car_%s" % car,
                        state=tk.NORMAL, fill=config.highlight_color)
        elif self.fill_state[0] == HIGHLIGHT_LAP:
            for lead in self.fill_state[1]:
                self.lc_canvas.itemconfigure("lead_%d" % int(lead),
                        state=tk.NORMAL, fill=config.highlight_color)

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
            cell = LapChartGUICell(self.lc_canvas, self.fill_state,
                    lap, len(self.cells[lap-1])+1)
            self.cells[lap-1].append(cell)
        return self.cells[lap-1][pos-1]

        
class LapChartWindow(tk.Toplevel):
    def __init__(self, data=None, filename=None):
        tk.Toplevel.__init__(self)
        self.filename = filename
        self.update_title()
        self.protocol('WM_DELETE_WINDOW', self.closeWindow)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        fill_state = [ config.def_highlight, '', config.def_shading ]
        self.control_frame = tk.Frame(self)
        self.control_frame.grid(sticky=FILL_PARENT)
        self.control_frame.columnconfigure(3, weight=1)
        self.chart_frame = LapChartFrame(self, data, fill_state)
        self.chart_frame.grid(sticky=FILL_PARENT)

        tk.Label(self.control_frame, text="Highlight:").grid(row=0, column=0)
        opts = [ x[1] for x in highlights ]
        self.highlight_v = tk.StringVar()
        self.highlight_v.set(highlight_label[config.def_highlight])
        self.highlight_v.trace('w', lambda name, index, mode:
                self.update_fills())
        tk.OptionMenu(self.control_frame, self.highlight_v, *opts).grid(row=0, column=1)
        self.highlight_items_v = tk.StringVar()
        self.highlight_items_v.trace('w', lambda name, index, mode:
                self.update_fills())
        tk.Entry(self.control_frame, textvariable=self.highlight_items_v).grid(row=0, column=2)
        self.hl_saved = config.def_highlight
        self.hl_saved_items = { x[0]:'' for x in highlights }

        tk.Label(self.control_frame, text="Shade:").grid(row=0, column=4)
        opts = [ x[1] for x in shadings ]
        self.shading_v = tk.StringVar()
        self.shading_v.set(shading_label[config.def_shading])
        self.shading_v.trace('w', lambda name, index, mode:
                self.update_fills())
        tk.OptionMenu(self.control_frame, self.shading_v, *opts).grid(row=0, column=5)

        self.menubar = tk.Menu(self)
        self.config(menu=self.menubar)

        menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=menu)
        menu.add_command(label="New", command=self.master.newWindow,
                accelerator="Ctrl+N")
        menu.add_command(label="Open...", command=self.master.openFileDialog,
                accelerator="Ctrl+O")
        menu.add_command(label="Save", command=self.saveOrSaveAs,
                accelerator="Ctrl+S")
        menu.add_command(label="Save as...", command=self.saveAsDialog)
        menu.add_command(label="Print to file...",
                command=self.printFileDialog,
                accelerator="Ctrl+P")
        menu.add_command(label="Close", command=self.closeWindow,
                accelerator="Ctrl+W")
        menu.add_command(label="Quit", command=self.master.quit,
                accelerator="Ctrl+Q")
        if data:
            self.data = data
            data.attach_gui(self)
        else:
            self.data = chartdata(self)

    def update_title(self):
        if self.filename:
            self.title("%s - ChartRoom v%s" % (self.filename, CR_VERSION))
        else:
            self.title('ChartRoom v%s' % CR_VERSION)

    def update_fills(self):
        hl    = highlight_mode[self.highlight_v.get()]
        shade = shading_mode[self.shading_v.get()]
        items = self.highlight_items_v.get()
        if hl != self.hl_saved:
            self.hl_saved_items[self.hl_saved] = items
            self.hl_saved = hl
            items = self.hl_saved_items[hl]
            self.highlight_items_v.set(items)
        items = items.replace(',',' ').split()
        self.chart_frame.update_fills(hl, items, shade)

    def getCell(self, lap, pos):
        return self.chart_frame.getCell(lap, pos)

    def saveAsDialog(self):
        update_filename = False
        if self.filename is None:
            update_filename = True
            path = tkFileDialog.asksaveasfilename(
                    parent = self, title = 'Save',
                    defaultextension='.crx',
                    filetypes=[("ChartRoom Data", "*.crx")])
        elif self.filename.endswith('.crx'):
            defdir  = os.path.dirname(self.filename)
            path = tkFileDialog.asksaveasfilename(
                    parent = self, title = 'Save',
                    initialdir = defdir, initialfile = self.filename,
                    defaultextension='.crx',
                    filetypes=[("ChartRoom Data", "*.crx")])
        else:
            defdir  = os.path.dirname(self.filename)
            defpath = os.path.splitext(self.filename)[0] + '.crx'
            path = tkFileDialog.asksaveasfilename(
                    parent = self, title = 'Save',
                    initialdir = defdir, initialfile = defpath,
                    defaultextension='.crx',
                    filetypes=[("ChartRoom Data", "*.crx")])
        if path:
            save_data_file(self.data, path)
            if update_filename:
                self.filename = path

    def saveOrSaveAs(self):
        if self.filename is None or not self.filename.endswith('.crx'):
            self.saveAsDialog()
        else:
            save_data_file(self.data, self.filename)

    def printFileDialog(self):
        if self.filename is not None:
            defdir  = os.path.dirname(self.filename)
            defpath = os.path.splitext(self.filename)[0] + '.ps'
            path = tkFileDialog.asksaveasfilename(
                    parent = self, title = 'Print to File',
                    initialdir = defdir, initialfile = defpath,
                    defaultextension='.ps',
                    filetypes=[("PostScript", "*.ps")])
        else:
            path = tkFileDialog.asksaveasfilename(
                    parent = self, title = 'Print to File',
                    defaultextension='.ps',
                    filetypes=[("PostScript", "*.ps")])
        if path:
            save_ps(self.data, path)

    def closeWindow(self):
        self.destroy()
        self.master._deref()


class LapChartGUI(tk.Tk):
    def __init__(self, files=[], data=None):
        tk.Tk.__init__(self)
        self.overrideredirect(1)
        self.withdraw()
        self.bind_all('<Control-KeyPress-n>', self.newWindow)
        self.bind_all('<Control-KeyPress-o>', self.openFileDialog)
        self.bind_all('<Control-KeyPress-s>', self.saveOrSaveAs)
        self.bind_all('<Control-KeyPress-p>', self.printFileDialog)
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

    def newWindow(self, event=None, data=None, filename=None):
        return LapChartWindow(data, filename)

    def openFile(self, file):
        newdata = chartdata()
        load_file(newdata, file)
        self.newWindow(data=newdata, filename=file)

    def openFileDialog(self, event=None):
        path = tkFileDialog.askopenfilename( filetypes=[
            ("Orbits Passings CSV", "*.csv"),
            ("Orbits Passings (tab-separated)", "*.txt"),
            ])
        if path: self.openFile(path)

    def saveOrSaveAs(self, event):
        event.widget.winfo_toplevel().saveOrSaveAs()

    def printFileDialog(self, event):
        event.widget.winfo_toplevel().printFileDialog()

    def closeWindow(self, event):
        event.widget.winfo_toplevel().closeWindow()

    def quitEvent(self, event):
        self.quit()

    def _deref(self):
        if not self.winfo_children(): self.quit()
