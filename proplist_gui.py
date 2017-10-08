import Tkinter as tk

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
