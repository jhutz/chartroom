import Tkinter as tk
import tkColorChooser

SWATCH_HEIGHT=25
SWATCH_WIDTH=80
SWATCH_WIDTH_SMALL=40

PAD_LEFT  = 2
PAD_SEP   = 5
PAD_RIGHT = 2

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
