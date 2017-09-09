import Tkinter as tk
import tkColorChooser
from config_data import *


class ColorListWidget(tk.Frame):
    def __init__(self, master, colors, single=False, height=25, itemwidth=40):
        self._colors = colors
        self._swatches = []
        self._itemwidth = itemwidth
        self._height    = height
        self._single    = single

        if single: del self._colors[1:]

        tk.Frame.__init__(self, master)
        self.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(self, height=self._height + 1)
        self.canvas.grid(row=0, column=0, sticky=tk.EW)
        button = tk.Button(self, width=6, text='Edit', command=self.editButton)
        button.grid(row=0, column=1, sticky=tk.E)
        self.refresh()

    def refresh(self):
        if len(self._swatches) < len(self._colors):
            self._swatches.extend([
                self.canvas.create_rectangle(
                    self._itemwidth * i + 1, 1,
                    self._itemwidth * (i+1) + 1, self._height + 1)
                for i in range(len(self._swatches), len(self._colors))
                ])
        if len(self._swatches) > len(self._colors):
            for swatch in self._swatches[len(self._colors):]:
                self.canvas.delete(swatch)
            del self._swatches[len(self._colors):]
        self.canvas.config(width=len(self._swatches) * self._itemwidth + 1)
        for color, swatch in zip(self._colors, self._swatches):
            self.canvas.itemconfigure(swatch, fill=color)

    def editButton(self):
        if self._single:
            (rgb, newcolor) = tkColorChooser.askcolor(self._colors[0],
                    parent=self.winfo_toplevel())
            if newcolor is not None:
                self._colors[0] = newcolor
                self.refresh()
        else:
            pass


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
        ColorListWidget(frame, colors=self.highlight_color, single=True,
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
        ColorListWidget(frame, colors=config.lap_colors).grid(column=1, sticky=tk.EW)
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
        ColorListWidget(frame, colors=config.class_colors).grid(column=1, sticky=tk.EW)
        tk.Radiobutton(frame,
                variable=self.def_shading_v,
                value=SHADE_DOWN,
                text='By Laps Down',
                ).grid(sticky=tk.W, columnspan=2)
        tk.Label(frame, text='Shade based on number of laps down'
                ).grid(sticky=tk.W, column=1)
        ColorListWidget(frame, colors=config.laps_down_colors).grid(column=1, sticky=tk.EW)
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
