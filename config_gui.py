import Tkinter as tk
import tkColorChooser
from config_data import *

SWATCH_HEIGHT=25
SWATCH_WIDTH=80
SWATCH_WIDTH_SMALL=40
PROP_WIDTH=15
PVAL_WIDTH=20

PAD_LEFT  = 2
PAD_SEP   = 5
PAD_RIGHT = 2

class PropertyListRow:
    def __init__(self, parent, frame, pos, name='', value=''):
        self.parent = parent
        self.name_v = tk.StringVar(value=name)
        self.value_v = tk.StringVar(value=value)

        self.label = tk.Entry(frame, width=1, textvariable=self.name_v)
        self.entry = tk.Entry(frame, width=1, textvariable=self.value_v)
        self.rm_btn = tk.Button(frame, width=1, text=u'\u2715', command=self.remove)
        self.moveto(pos)

    def remove(self): self.parent.remove(self._pos)
    def get(self):    return (self.name_v.get(), self.value_v.get())

    def moveto(self, pos):
        self._pos = pos
        self.label.grid(row=pos, column=0, sticky=tk.EW)
        self.entry.grid(row=pos, column=1, sticky=tk.EW)
        self.rm_btn.grid(row=pos, column=2)

    def destroy(self):
        self.label.destroy()
        self.entry.destroy()
        self.rm_btn.destroy()


class PropertyListDialog(tk.Toplevel):
    def __init__(self, props, title='Property Editor'):
        self._props = props
        tk.Toplevel.__init__(self)
        self.title(title)
        self.protocol('WM_DELETE_WINDOW', self.closeWindow)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.header = tk.Frame(self, padx=2)
        self.header.columnconfigure(0, weight=2)
        self.header.columnconfigure(1, weight=3)
        self.header.columnconfigure(2, minsize=40)
        tk.Label(self.header, anchor=tk.W, width=1, padx=2,
                font='TkHeadingFont', text='Property',
                ).grid(row=0, column=0, sticky=tk.EW)
        tk.Label(self.header, anchor=tk.W, width=1, padx=2,
                font='TkHeadingFont', text='Value',
                ).grid(row=0, column=1, sticky=tk.EW)
        tk.Label(self.header, anchor=tk.E, width=1, padx=2,
                font='TkHeadingFont', text='',
                ).grid(row=0, column=2, sticky=tk.EW)
        self.header.grid(row=0, column=0, sticky=tk.EW)

        self.canvas = tk.Canvas(self, bg='white')
        self.scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL,
                command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.grid(row=1, column=0, sticky=tk.NSEW)
        self.scrollbar.grid(row=1, column=1, sticky=tk.NS+tk.W)
        self.item_frame = tk.Frame(self.canvas, bg='white')
        self.item_frame.columnconfigure(0, weight=2)
        self.item_frame.columnconfigure(1, weight=3)
        self.item_frame.columnconfigure(2, minsize=40)
        self.canvas.create_window(0, 0, window=self.item_frame, anchor=tk.NW, tags="items")
        self.item_frame.bind('<Configure>', self.resize_canvas)
        self.canvas.bind('<Configure>', self.resize_frame)

        frame = tk.Frame(self)
        frame.rowconfigure(1, weight=1)
        tk.Button(frame, width=6, text='Add', command=self.addItem,
                ).grid(row=0, sticky=tk.NE)
        tk.Button(frame, width=6, text='Reset', command=self.revertChanges,
                ).grid(row=1, sticky=tk.NE)
        frame.grid(row=1, column=2, sticky=tk.NS+tk.E)

        frame = tk.Frame(self)
        frame.columnconfigure(0, weight=1)
        tk.Button(frame, width=6, text='OK', command=self.okButton,
                ).grid(row=0, column=0, sticky=tk.SE)
        tk.Button(frame, width=6, text='Cancel', command=self.closeWindow,
                ).grid(row=0, column=1, sticky=tk.SE)
        frame.grid(row=2, columnspan=3, sticky=tk.EW+tk.S)

        self.fill()

    def resize_canvas(self, event=None):
        w = self.item_frame.winfo_reqwidth()
        h = self.item_frame.winfo_reqheight()
        self.canvas.configure(scrollregion=(0, 0, w, h))
        self.header.columnconfigure(2, minsize=max(40, self.item_frame.grid_bbox(2, 0)[2]))

    def resize_frame(self, event=None):
        cw = self.canvas.winfo_width()
        self.canvas.itemconfigure('items', width=cw-2)
        pass

    def addItem(self):
        self._items.append(PropertyListRow(self, self.item_frame, len(self._items)))
        self.resize_canvas()

    def remove(self, pos):
        if pos < 0 or pos > len(self._items) - 1: return
        self._items[pos].destroy()
        del self._items[pos]
        for i, item in enumerate(self._items[pos:], start=pos):
            item.moveto(i)
        self.resize_canvas()

    def fill(self):
        self._items = [
                PropertyListRow(self, self.item_frame, i, k, v)
                for (i, (k, v)) in enumerate(self._props.iteritems())
                ]
        self.resize_canvas()
        self.canvas.yview_moveto(0)

    def revertChanges(self):
        for item in self._items: item.destroy()
        self.fill()

    def closeWindow(self):
        self.destroy()
        self.master._deref()

    def okButton(self):
        self._props.clear()
        self._props.update(
            [ item for item in [ item.get() for item in self._items ] if item[0] != '' ])
        self.closeWindow()

class ColorListRow:
    def __init__(self, parent, canvas, pos, nrows, color):
        self.canvas = canvas
        self.parent = parent
        self.old_color = color
        self.new_color = color
        self.old_swatch = self.canvas.create_rectangle(0,0,0,0, fill=color)
        self.new_swatch = self.canvas.create_rectangle(0,0,0,0, fill=color,
                activewidth=2)
        self.btn_frame = tk.Frame(canvas)
        self.btns = self.canvas.create_window(0,0,
                anchor=tk.NW, window=self.btn_frame)
        self.up_btn = tk.Button(self.btn_frame, width=1, text=u'\u2191', command=self.up)
        self.up_btn.grid(row=0, column=0, sticky=tk.W)
        self.dn_btn = tk.Button(self.btn_frame, width=1, text=u'\u2193', command=self.down)
        self.dn_btn.grid(row=0, column=1, sticky=tk.W)
        self.rm_btn = tk.Button(self.btn_frame, width=1, text=u'\u2715', command=self.remove)
        self.rm_btn.grid(row=0, column=2, sticky=tk.W)

        width = sum([b.winfo_reqwidth() for b in [self.up_btn, self.dn_btn, self.rm_btn]])
        self.moveto(pos, nrows)
        self.canvas.configure(width=PAD_LEFT + 2*SWATCH_WIDTH + PAD_SEP + width + PAD_RIGHT)
        self.canvas.tag_bind(self.new_swatch, '<ButtonPress-1>', self.edit)

    def up(self):     self.parent.swap(self._pos - 1)
    def down(self):   self.parent.swap(self._pos)
    def remove(self): self.parent.remove(self._pos)
    def get(self):    return self.new_color

    def edit(self, event=None):
        (rgb, newcolor) = tkColorChooser.askcolor(self.new_color,
                parent=self.parent.winfo_toplevel())
        if newcolor is None: return
        self.new_color = newcolor
        self.canvas.itemconfigure(self.new_swatch, fill=self.new_color)
        self.parent.applyChanges()

    def moveto(self, pos, nrows):
        self._pos = pos
        self.canvas.coords(self.old_swatch,
                PAD_LEFT, pos * SWATCH_HEIGHT + 1,
                PAD_LEFT + SWATCH_WIDTH, (pos+1) * SWATCH_HEIGHT + 1)
        self.canvas.coords(self.new_swatch,
                PAD_LEFT + SWATCH_WIDTH, pos * SWATCH_HEIGHT + 1,
                PAD_LEFT + 2*SWATCH_WIDTH, (pos+1) * SWATCH_HEIGHT + 1)
        self.canvas.coords(self.btns,
                PAD_LEFT + 2*SWATCH_WIDTH + PAD_SEP,
                pos * SWATCH_HEIGHT)
        self.up_btn.configure(state = tk.DISABLED if pos == 0         else tk.NORMAL)
        self.dn_btn.configure(state = tk.DISABLED if pos >= nrows - 1 else tk.NORMAL)
        self.rm_btn.configure(state = tk.DISABLED if nrows == 1       else tk.NORMAL)

    def destroy(self):
        self.canvas.delete(self.old_swatch)
        self.canvas.delete(self.new_swatch)
        self.canvas.delete(self.btns)
        self.btn_frame.destroy()


class ColorListDialog(tk.Toplevel):
    def __init__(self, colors, title='Color List Editor', gui=None):
        self._colors = colors
        self._old_colors = colors[:]
        self._gui = gui
        tk.Toplevel.__init__(self)
        self.title(title)
        self.protocol('WM_DELETE_WINDOW', self.closeWindow)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(self, bg='white',
                width = 2 * SWATCH_WIDTH + 1, height = 7 * SWATCH_HEIGHT + 3)
        self.scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL,
                command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.grid(row=0, column=0, sticky=tk.NSEW)
        self.scrollbar.grid(row=0, column=1, sticky=tk.NS+tk.W)

        frame = tk.Frame(self)
        frame.rowconfigure(1, weight=1)
        tk.Button(frame, width=6, text='Add', command=self.addItem,
                ).grid(row=0, sticky=tk.NE)
        tk.Button(frame, width=6, text='Reset', command=self.revertChanges,
                ).grid(row=1, sticky=tk.NE)
        frame.grid(row=0, column=2, sticky=tk.NS+tk.E)

        frame = tk.Frame(self)
        frame.columnconfigure(0, weight=1)
        tk.Button(frame, width=6, text='OK', command=self.closeWindow,
                ).grid(row=0, column=0, sticky=tk.SE)
        tk.Button(frame, width=6, text='Cancel', command=self.cancelButton,
                ).grid(row=0, column=1, sticky=tk.SE)
        frame.grid(columnspan=3, sticky=tk.EW+tk.S)

        self.fill()

    def resize_canvas(self):
        self.canvas.configure(scrollregion=
            (0, 0, self.canvas['width'], len(self._items) * SWATCH_HEIGHT + 1))

    def addItem(self):
        (rgb, newcolor) = tkColorChooser.askcolor('black', parent=self)
        if newcolor is None: return
        newpos = len(self._items)
        self._items.append(ColorListRow(self, self.canvas, newpos, newpos+1, newcolor))
        if newpos > 0: self._items[newpos-1].moveto(newpos - 1, newpos+1)
        self.resize_canvas()
        self.applyChanges()

    def swap(self, pos):
        if pos < 0 or pos > len(self._items) - 2: return
        (self._items[pos], self._items[pos+1]) = (self._items[pos+1], self._items[pos])
        self._items[pos].moveto(pos, len(self._items))
        self._items[pos+1].moveto(pos+1, len(self._items))
        self.applyChanges()

    def remove(self, pos):
        if pos < 0 or pos > len(self._items) - 1: return
        if len(self._items) == 1: return
        self._items[pos].destroy()
        del self._items[pos]
        if pos == len(self._items):
            self._items[-1].moveto(pos-1, len(self._items))
        else:
            for i, item in enumerate(self._items[pos:], start=pos):
                item.moveto(i, len(self._items))
        self.resize_canvas()
        self.applyChanges()

    def fill(self):
        self._items = [
                ColorListRow(self, self.canvas, pos, len(self._old_colors), color)
                for pos, color in enumerate(self._old_colors)
                ]
        self.resize_canvas()
        self.canvas.yview_moveto(0)

    def applyChanges(self):
        self._colors[:] = [i.get() for i in self._items]
        if self._gui: self._gui.update_coloring()

    def revertChanges(self):
        for item in self._items: item.destroy()
        self.fill()
        self.applyChanges()

    def closeWindow(self):
        self.destroy()
        self.master._deref()

    def cancelButton(self):
        self.revertChanges()
        self.closeWindow()

class ColorListWidget(tk.Frame):
    def __init__(self, master, colors, labels=None,
            single=False, editable=True, title='Color Editor',
            height=SWATCH_HEIGHT, itemwidth=SWATCH_WIDTH_SMALL, gui=None):
        self._colors = colors
        self._labels = labels
        self._swatches = []
        self._lbltext = []
        self._itemwidth = itemwidth
        self._height    = height
        self._single    = single
        self._title     = title
        self._gui       = gui

        if single: del self._colors[1:]

        tk.Frame.__init__(self, master)
        self.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(self, height=self._height + 1)
        self.canvas.grid(row=0, column=0, sticky=tk.EW)
        if editable:
            button = tk.Button(self, width=6, text='Edit',
                    command=self.editButton)
            button.grid(row=0, column=1, sticky=tk.E)
        self.refresh()

    def refresh(self):
        count = 1 if self._single else len(self._colors)
        if self._labels is not None:
            count = min(count, len(self._labels))

        if len(self._swatches) < count:
            self._swatches.extend([
                self.canvas.create_rectangle(
                    self._itemwidth * i + 1, 1,
                    self._itemwidth * (i+1) + 1, self._height + 1)
                for i in range(len(self._swatches), count)
                ])
        if len(self._swatches) > count:
            for swatch in self._swatches[count:]:
                self.canvas.delete(swatch)
            del self._swatches[count:]

        self.canvas.config(width=len(self._swatches) * self._itemwidth + 1)
        for color, swatch in zip(self._colors, self._swatches):
            self.canvas.itemconfigure(swatch, fill=color)

        if self._labels is not None:
            if len(self._lbltext) < count:
                self._lbltext.extend([
                    self.canvas.create_text(
                        self._itemwidth * i + (self._itemwidth // 2) + 1,
                        self._height // 2 + 1)
                    for i in range(len(self._lbltext), count)
                    ])
            if len(self._lbltext) > count:
                for lbl in self._lbltext[count:]:
                    self.canvas.delete(lbl)
                del self._lbltext[count:]
            for label, lbltext in zip(self._labels, self._lbltext):
                self.canvas.itemconfigure(lbltext, text=label)

    def editButton(self):
        if self._single:
            (rgb, newcolor) = tkColorChooser.askcolor(self._colors[0],
                    title=self._title, parent=self.winfo_toplevel())
            if newcolor is not None:
                self._colors[0] = newcolor
                self.refresh()
        else:
            ColorListDialog(self._colors, title=self._title, gui=self._gui)


class PreferencesDialog(tk.Toplevel):
    def __init__(self, gui):
        tk.Toplevel.__init__(self)
        self.gui = gui
        self.title('ChartRoom Preferences')
        self.protocol('WM_DELETE_WINDOW', self.closeWindow)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)

        self.highlight_color = [ config.highlight_color ]
        self.def_highlight_v = tk.StringVar(value=config.def_highlight)
        self.def_shading_v   = tk.StringVar(value=config.def_shading)
        self.color_mode_v    = tk.StringVar(value=config.color_mode)
        self.color_period_v  = tk.StringVar(value=str(config.color_period))
        self.color_laps_v    = tk.IntVar(value=bool(config.color_laps))
        self.color_bold_v    = tk.IntVar(value=bool(config.color_bold))
        self.color_final_v   = tk.IntVar(value=bool(config.color_final))
        self.bold_final_v    = tk.IntVar(value=bool(config.bold_final))
        self.rainbow_bold_v  = tk.IntVar(value=bool(config.rainbow_bold))

        ## -- Highlight ------------
        frame = tk.LabelFrame(self, text='Highlight')
        frame.columnconfigure(0, minsize=30)
        frame.columnconfigure(2, weight=1)
        tk.Label(frame, text='Default highlight mode:').grid(sticky=tk.W)
        tk.Radiobutton(frame,
                variable=self.def_highlight_v,
                value=HIGHLIGHT_CARS,
                text='Car Numbers',
                ).grid(row=0, column=1, sticky=tk.W)
        tk.Radiobutton(frame,
                variable=self.def_highlight_v,
                value=HIGHLIGHT_LAP,
                text='Lead Laps',
                ).grid(row=0, column=2, sticky=tk.W)
        tk.Label(frame, text='Highlight color:').grid(row=1, sticky=tk.W)
        ColorListWidget(frame, gui=self.gui, colors=self.highlight_color,
                single=True, title='Highlight Color',
                ).grid(row=1, column=1, columnspan=2, sticky=tk.W)
        frame.grid(columnspan=2, sticky=tk.EW)

        ## -- Lap Coloring ---------
        frame = tk.LabelFrame(self, text='Lap Coloring')
        frame.columnconfigure(0, minsize=30)
        frame.columnconfigure(1, weight=1)
        tk.Radiobutton(frame,
                variable=self.color_mode_v,
                value=COLOR_NONE,
                text='None',
                ).grid(sticky=tk.W, columnspan=2)
        tk.Radiobutton(frame,
                variable=self.color_mode_v,
                value=COLOR_NORMAL,
                text='Traditional',
                ).grid(sticky=tk.W, columnspan=2)
        subframe=tk.Frame(frame)
        tk.Checkbutton(subframe, variable=self.color_laps_v, text='Color'
                ).grid(row=0, column=0)
        tk.Checkbutton(subframe, variable=self.color_bold_v, text='Bold'
                ).grid(row=0, column=1)
        tk.Label(subframe, text='one lap in every').grid(row=0, column=2)
        tk.Spinbox(subframe,
                textvariable=self.color_period_v,
                format='%.0f', from_=1, to=99, increment=1,
                insertofftime=0, width=2,
                ).grid(row=0, column=3)
        subframe.grid(column=1, sticky=tk.W)
        tk.Checkbutton(frame,
                variable=self.color_final_v,
                text='Use a different color for final lap'
                ).grid(column=1, sticky=tk.W)
        tk.Checkbutton(frame,
                variable=self.bold_final_v,
                text='Use bold for final lap'
                ).grid(column=1, sticky=tk.W)
        tk.Radiobutton(frame,
                variable=self.color_mode_v,
                value=COLOR_RAINBOW,
                text='Rainbow',
                ).grid(sticky=tk.W, columnspan=2)
        tk.Checkbutton(frame,
                variable=self.rainbow_bold_v,
                text='Use bold for final lap'
                ).grid(column=1, sticky=tk.W)
        ColorListWidget(frame, gui=self.gui, colors=config.lap_colors,
                title='Lead Lap Colors',
                ).grid(column=1, sticky=tk.EW)
        frame.grid(row=1, column=0, sticky=tk.NSEW)

        ## -- Shading --------------
        frame = tk.LabelFrame(self, text='Shading')
        frame.columnconfigure(0, minsize=30)
        frame.columnconfigure(1, weight=1)
        tk.Label(frame, text='Default shading mode:').grid(sticky=tk.W, columnspan=2)
        tk.Radiobutton(frame,
                variable=self.def_shading_v,
                value=SHADE_NONE,
                text='None',
                ).grid(sticky=tk.W, columnspan=2)
        tk.Radiobutton(frame,
                variable=self.def_shading_v,
                value=SHADE_CLASS,
                text='By Class',
                ).grid(sticky=tk.W, columnspan=2)
        tk.Label(frame, text='Shade each class using one of these colors:'
                ).grid(sticky=tk.W, column=1)
        ColorListWidget(frame, gui=self.gui, colors=config.class_colors,
                title='Class Shading Colors',
                ).grid(column=1, sticky=tk.EW)
        tk.Radiobutton(frame,
                variable=self.def_shading_v,
                value=SHADE_DOWN,
                text='By Laps Down',
                ).grid(sticky=tk.W, columnspan=2)
        tk.Label(frame, text='Shade based on number of laps down'
                ).grid(sticky=tk.W, column=1)
        ColorListWidget(frame, gui=self.gui, colors=config.laps_down_colors,
                title='Laps Down Colors',
                ).grid(column=1, sticky=tk.EW)
        frame.grid(row=1, column=1, sticky=tk.NSEW)

        ## Commit buttons
        frame = tk.Frame(self)
        frame.columnconfigure(0, weight=1)
        tk.Button(frame, width=6, text='OK', command=self.okButton,
                ).grid(row=0, column=0, sticky=tk.SE)
        tk.Button(frame, width=6, text='Cancel', command=self.closeWindow,
                ).grid(row=0, column=1, sticky=tk.SE)
        tk.Button(frame, width=6, text='Apply', command=self.applyChanges,
                ).grid(row=0, column=2, sticky=tk.SE)
        tk.Button(frame, width=6, text='Reset', command=self.revertChanges,
                ).grid(row=0, column=3, sticky=tk.SE)
        frame.grid(columnspan=2, sticky=tk.EW+tk.S)

    def applyChanges(self):
        config.highlight_color = self.highlight_color[0]
        config.def_highlight = self.def_highlight_v.get()
        config.def_shading   = self.def_shading_v.get()
        config.color_mode    = self.color_mode_v.get()
        config.color_laps    = bool(self.color_laps_v.get())
        config.color_bold    = bool(self.color_bold_v.get())
        config.color_period  = int(self.color_period_v.get())
        config.color_final   = bool(self.color_final_v.get())
        config.bold_final    = bool(self.bold_final_v.get())
        config.rainbow_bold  = bool(self.rainbow_bold_v.get())
        self.gui.update_coloring()

    def revertChanges(self):
        self.highlight_color[:] = [ config.highlight_color ]
        self.def_highlight_v.set(config.def_highlight)
        self.def_shading_v  .set(config.def_shading)
        self.color_mode_v   .set(config.color_mode)
        self.color_period_v .set(str(config.color_period))
        self.color_laps_v   .set(bool(config.color_laps))
        self.color_bold_v   .set(bool(config.color_bold))
        self.color_final_v  .set(bool(config.color_final))
        self.bold_final_v   .set(bool(config.bold_final))
        self.rainbow_bold_v .set(bool(config.rainbow_bold))

    def closeWindow(self):
        self.destroy()
        self.master._deref()

    def okButton(self):
        self.applyChanges()
        self.closeWindow()
