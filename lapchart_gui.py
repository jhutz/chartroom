import Tkinter as tk
import tkFont
import tkFileDialog
import os.path
from lapchart_data import chartdata
from data_file_io import load_file, save_data_file
from data_file_io import FileFormatException
from printing import save_ps
from config_data import *
from config_gui import PreferencesDialog, PropertyListDialog

cell_width  = 34
cell_height = 20
bar_width   = 1.6
scales = [ 25, 33, 50, 67, 75, 80, 90, 100, 110, 125, 150, 175, 200, 250, 300, 400, 500 ]
def_scale = scales.index(100)

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

def lap_color(lap, nlaps):
    if config.color_mode == COLOR_NORMAL:
        # Traditional coloring
        n_colors = len(config.lap_colors) - (2 if config.color_final else 1)
        is_colored = (lap % config.color_period) == 0
        bold = ((config.bold_final and lap == nlaps)
                or (config.color_bold and is_colored))
        if config.color_final and lap == nlaps:
            return (config.lap_colors[-1], bold)
        elif config.color_laps and is_colored:
            color = (lap // config.color_period - 1) % n_colors
            return (config.lap_colors[1+color], bold)
        else:
            return (config.lap_colors[0], bold)

    elif config.color_mode == COLOR_RAINBOW:
        # Rainbow coloring
        color = config.lap_colors[(lap - 1) % len(config.lap_colors)]
        bold  = config.rainbow_bold and lap == nlaps
        return (color, bold)

    else:
        # No coloring
        return ('black', False)


class LapChartGUICell:
    def __init__(self, canvas, lap, pos, ui_state):
        self.data = None
        self.canvas = canvas
        self.ui_state = ui_state
        self.lap = lap
        self.pos = pos

        x = (lap - 1) * self.ui_state['c_width']
        y = (pos - 1) * self.ui_state['c_height']
        x0 = x - (self.ui_state['c_width']/2)
        y0 = y - (self.ui_state['c_height']/2)
        x1 = x + (self.ui_state['c_width']/2)
        y1 = y + (self.ui_state['c_height']/2)

        self.fill = canvas.create_rectangle(x0, y0, x1, y1, state=tk.HIDDEN,
                width=0, tags="cell")
        self.text = canvas.create_text(x, y, text='', justify=tk.CENTER,
                font=self.ui_state['fonts']['data'][0],
                tags="cell_text")
        self.bar_above = canvas.create_line(x0, y0, x1, y0, state=tk.HIDDEN,
                width=max(1, int(bar_width * self.ui_state['factor'])),
                tags="bars")
        self.bar_left  = canvas.create_line(x0, y0, x0, y1, state=tk.HIDDEN,
                width=max(1, int(bar_width * self.ui_state['factor'])),
                tags="bars")

    def reconfigure(self):
        # recompute locations of our elements
        # call this whenever the cell height/width changes
        x = (self.lap - 1) * self.ui_state['c_width']
        y = (self.pos - 1) * self.ui_state['c_height']
        x0 = x - (self.ui_state['c_width']/2)
        y0 = y - (self.ui_state['c_height']/2)
        x1 = x + (self.ui_state['c_width']/2)
        y1 = y + (self.ui_state['c_height']/2)

        self.canvas.coords(self.fill, x0, y0, x1, y1)
        self.canvas.coords(self.text, x, y)
        self.canvas.coords(self.bar_above, x0, y0, x1, y0)
        self.canvas.coords(self.bar_left, x0, y0, x0, y1)

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
        if self.ui_state['hl_mode'] == HIGHLIGHT_CARS and car_no in self.ui_state['hl_list']:
            self.canvas.itemconfigure(self.fill, state=tk.NORMAL, fill=config.highlight_color)
        elif self.ui_state['hl_mode'] == HIGHLIGHT_LAP and str(lead) in self.ui_state['hl_list']:
            self.canvas.itemconfigure(self.fill, state=tk.NORMAL, fill=config.highlight_color)
        elif self.ui_state['shading'] == SHADE_CLASS:
            class_ = self.data.car().class_()
            pass # XXX
        elif self.ui_state['shading'] == SHADE_DOWN and down:
            if down > len(config.laps_down_colors):
                self.canvas.itemconfigure(self.fill, state=tk.NORMAL,
                        fill=config.laps_down_colors[-1])
            else:
                self.canvas.itemconfigure(self.fill, state=tk.NORMAL,
                        fill=config.laps_down_colors[down-1])
        else:
            self.canvas.itemconfigure(self.fill, state=tk.HIDDEN)

    def update_text(self):
        if self.data:
            lead = self.data.lead()
            nlaps = self.data.parent.num_laps()
            (color, bold) = lap_color(lead, nlaps)
        else:
            (color, bold) = ('black', False)
        font = self.ui_state['fonts']['bold' if bold else 'data'][0]
        self.canvas.itemconfigure(self.text, font=font, fill=color)

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
        self.update_text()
        self.update_bars()
        self.update_fill()


class LapChartFrame(tk.Frame):
    def __init__(self, parent, data, ui_state):
        self.parent = parent
        self.data = data
        self.ui_state = ui_state
        self.n_laps = 0
        self.n_pos = 0
        self.lap_labels = []
        self.pos_labels = []
        self.cells = []

        # overall frame and scrollbars
        tk.Frame.__init__(self, parent)
        self.lc_vscrollbar = tk.Scrollbar(self, orient=tk.VERTICAL, command = self.yview)
        self.lc_hscrollbar = tk.Scrollbar(self, orient=tk.HORIZONTAL, command = self.xview)

        # create canvases for lap and position labels and the car cells
        self.lap_canvas = tk.Canvas(self, height=ui_state['c_height'],
                xscrollcommand=self.lc_hscrollbar.set)
        self.pos_canvas = tk.Canvas(self, width=ui_state['c_width'],
                yscrollcommand=self.lc_vscrollbar.set)
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
        label = tk.Label(self, text='Laps',
                font=self.ui_state['fonts']['header'][0])
        label.grid(row=0, column=1, sticky=tk.NS+tk.W)
        label = tk.Label(self, text='Pos',
                font=self.ui_state['fonts']['header'][0])
        label.grid(row=1, column=0, sticky=FILL_PARENT)
        self.lap_canvas.grid(row=1, column=1, sticky=tk.EW)
        self.pos_canvas.grid(row=2, column=0, sticky=tk.NS)
        self.lc_canvas.grid     (row=2, column=1, sticky=FILL_PARENT)
        self.lc_vscrollbar.grid (row=2, column=2, sticky=tk.NS)
        self.lc_hscrollbar.grid (row=3, column=1, sticky=tk.EW)

        # bind mouse controls
        parent.bind('<Button-4>', self.scroll_event)
        parent.bind('<Button-5>', self.scroll_event)
        parent.bind('<MouseWheel>', self.scroll_event)

    def reconfigure(self):
        # recompute locations of everything
        # call this whenever the cell height/width changes
        self.lap_canvas.configure(height=self.ui_state['c_height'])
        self.pos_canvas.configure(width=self.ui_state['c_width'])
        for lap, label in enumerate(self.lap_labels):
            self.lap_canvas.coords(label, lap * self.ui_state['c_width'], 0)
        for pos, label in enumerate(self.pos_labels):
            self.pos_canvas.coords(label, 0, pos * self.ui_state['c_height'])
        for cell in [ cell for lap in self.cells for cell in lap ]:
            cell.reconfigure()
        self.lc_canvas.itemconfigure('bars',
                width=max(1, int(bar_width * self.ui_state['factor'])))
        self.update_scrollregions()

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
            if reverse: self.parent.zoom(count)
            else:       self.parent.zoom(-count)

    def update_scrollregions(self):
        xpos = self.lc_hscrollbar.get()[0]
        ypos = self.lc_vscrollbar.get()[0]
        x0 = - (self.ui_state['c_width'] / 2)
        y0 = - (self.ui_state['c_height'] / 2)
        width = self.ui_state['c_width'] * self.n_laps
        height = self.ui_state['c_height'] * self.n_pos
        self.lap_canvas.config(scrollregion=(x0, y0, width, self.ui_state['c_height']))
        self.pos_canvas.config(scrollregion=(x0, y0, self.ui_state['c_width'], height))
        self.lc_canvas.config(scrollregion=(x0, y0, width, height))
        self.lap_canvas.yview_moveto(0)
        self.pos_canvas.xview_moveto(0)
        self.xview(tk.MOVETO, xpos)
        self.yview(tk.MOVETO, ypos)

    def update_fills(self):
        self.lc_canvas.itemconfigure('cell', state=tk.HIDDEN)
        if self.ui_state['shading'] == SHADE_CLASS:
            for (cls,color) in zip(self.data.classes(), config.class_colors):
                self.lc_canvas.itemconfigure("class_%s" % cls, state=tk.NORMAL, fill=color)
        elif self.ui_state['shading'] == SHADE_DOWN:
            n = min(self.data.max_down(), len(config.laps_down_colors))
            for i in range(n):
                self.lc_canvas.itemconfigure("down_%d" % (i+1),
                        state=tk.NORMAL, fill=config.laps_down_colors[i])
            if n < self.data.max_down():
                for i in range(n, self.data.max_down()):
                    self.lc_canvas.itemconfigure("down_%d" % i,
                            state=tk.NORMAL, fill=config.laps_down_colors[-1])
        if self.ui_state['hl_mode'] == HIGHLIGHT_CARS:
            for car in self.ui_state['hl_list']:
                self.lc_canvas.itemconfigure("car_%s" % car,
                        state=tk.NORMAL, fill=config.highlight_color)
        elif self.ui_state['hl_mode'] == HIGHLIGHT_LAP:
            for lead in self.ui_state['hl_list']:
                self.lc_canvas.itemconfigure("lead_%d" % int(lead),
                        state=tk.NORMAL, fill=config.highlight_color)

    def update_coloring(self, since=1):
        nlaps = self.data.num_laps()
        for lap in range(since, nlaps + 1):
            (color, bold) = lap_color(lap, nlaps)
            font = self.ui_state['fonts']['bold' if bold else 'data'][0]
            self.lc_canvas.itemconfigure("lead_%d_text" % lap, font=font, fill=color)

    def getCell(self, lap, pos):
        update = lap > self.n_laps or pos > self.n_pos
        while lap > self.n_laps:
            self.lap_labels.append(
                    self.lap_canvas.create_text(
                        self.n_laps * self.ui_state['c_width'], 0,
                        font=self.ui_state['fonts']['header'][0],
                        text=self.n_laps+1))
            self.n_laps = self.n_laps + 1
            self.cells.append([])
        while pos > self.n_pos:
            self.pos_labels.append(
                    self.pos_canvas.create_text(
                        0, self.n_pos * self.ui_state['c_height'],
                        font=self.ui_state['fonts']['header'][0],
                        text=self.n_pos+1))
            self.n_pos = self.n_pos + 1
        if update: self.update_scrollregions()
        while pos > len(self.cells[lap-1]):
            cell = LapChartGUICell(
                    self.lc_canvas, lap, len(self.cells[lap-1])+1,
                    self.ui_state)
            self.cells[lap-1].append(cell)
        return self.cells[lap-1][pos-1]

        
class LapChartWindow(tk.Toplevel):
    def __init__(self, fonts, data=None, filename=None):
        tk.Toplevel.__init__(self)
        self.filename = filename
        self.update_title()
        self.protocol('WM_DELETE_WINDOW', self.closeWindow)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.ui_state = {
                'hl_mode'   : config.def_highlight,
                'hl_list'   : [],
                'shading'   : config.def_shading,
                'scale'     : def_scale,
                'fonts'     : {
                    name : (font.copy(), size)
                    for (name,(font,size)) in fonts.iteritems()
                    }
                }
        self.scale()

        self.control_frame = tk.Frame(self)
        self.control_frame.grid(sticky=FILL_PARENT)
        self.control_frame.columnconfigure(3, weight=1)
        self.chart_frame = LapChartFrame(self, data, self.ui_state)
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
        tk.Entry(self.control_frame,
                textvariable=self.highlight_items_v,
                insertofftime=0,
                ).grid(row=0, column=2)
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

        menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Edit", menu=menu)
        menu.add_command(label="Default Properties",
                command=self.master.editDefaultProps)
        menu.add_command(label="Global Properties",
                command=self.master.editGlobalProps)
        menu.add_command(label="Preferences", command=self.master.prefsDialog)

        menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Help", menu=menu)
        menu.add_command(label="About", command=self.master.aboutDialog)

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
        self.ui_state['hl_mode'] = highlight_mode[self.highlight_v.get()]
        self.ui_state['shading'] = shading_mode[self.shading_v.get()]
        items = self.highlight_items_v.get()
        if self.ui_state['hl_mode'] != self.hl_saved:
            self.hl_saved_items[self.hl_saved] = items
            self.hl_saved = self.ui_state['hl_mode']
            items = self.hl_saved_items[self.ui_state['hl_mode']]
            self.highlight_items_v.set(items)
        self.ui_state['hl_list'] = items.replace(',',' ').split()
        self.chart_frame.update_fills()

    def update_coloring(self, since=1):
        self.chart_frame.update_coloring(since)

    def scale(self):
        self.ui_state['factor'] = scales[self.ui_state['scale']] * .01
        self.ui_state['c_width']  = cell_width *  self.ui_state['factor']
        self.ui_state['c_height'] = cell_height *  self.ui_state['factor']
        for (name,(font,size)) in self.ui_state['fonts'].iteritems():
            font.configure(size = - int(size * self.ui_state['factor']))

    def zoom(self, count):
        self.ui_state['scale'] = max(0, min(len(scales)-1, self.ui_state['scale'] + count))
        self.scale()
        self.chart_frame.reconfigure()

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

        headerFont = tkFont.nametofont('TkHeadingFont').copy()
        dataFont = tkFont.nametofont('TkDefaultFont').copy()
        boldFont = dataFont.copy()
        boldFont.configure(weight='bold')
        self.fonts = {
                'header' : (headerFont, headerFont.metrics('ascent')),
                'data'   : (dataFont,   dataFont.metrics('ascent')),
                'bold'   : (boldFont,   boldFont.metrics('ascent')),
                }

        self.bind_all('<Control-KeyPress-n>', self.newWindow)
        self.bind_all('<Control-KeyPress-o>', self.openFileDialog)
        self.bind_all('<Control-KeyPress-s>', self.saveOrSaveAs)
        self.bind_all('<Control-KeyPress-p>', self.printFileDialog)
        self.bind_all('<Control-KeyPress-w>', self.closeWindow)
        self.bind_all('<Control-KeyPress-q>', self.quitEvent)
        self.bind_all('<Control-KeyPress-plus>',  self.zoom_in)
        self.bind_all('<Control-KeyPress-equal>', self.zoom_in)
        self.bind_all('<Control-KeyPress-minus>', self.zoom_out)

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

    def zoom_in(self, event):
        it = event.widget.winfo_toplevel()
        if hasattr(it, 'zoom'): it.zoom(1)

    def zoom_out(self, event):
        it = event.widget.winfo_toplevel()
        if hasattr(it, 'zoom'): it.zoom(-1)

    def update_coloring(self):
        for win in self.winfo_children():
            if hasattr(win, 'update_coloring'):
                win.update_coloring()
            if hasattr(win, 'update_fills'):
                win.update_fills()

    def newWindow(self, event=None, data=None, filename=None):
        return LapChartWindow(self.fonts, data, filename)

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
        it = event.widget.winfo_toplevel()
        if hasattr(it, 'saveOrSaveAs'): it.saveOrSaveAs()

    def printFileDialog(self, event):
        it = event.widget.winfo_toplevel()
        if hasattr(it, 'printFileDialog'): it.printFileDialog()

    def closeWindow(self, event):
        it = event.widget.winfo_toplevel()
        if hasattr(it, 'closeWindow'): it.closeWindow()

    def quitEvent(self, event):
        self.quit()

    def editGlobalProps(self):
        PropertyListDialog(config.global_props, 'Global Properties')

    def editDefaultProps(self):
        PropertyListDialog(config.default_props, 'Default Properties')

    def prefsDialog(self):
        PreferencesDialog(self)

    def aboutDialog(self):
        pass

    def _deref(self):
        if not self.winfo_children(): self.quit()
