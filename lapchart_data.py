from config_data import config

class chartcar:
    def __init__(self, parent, car_id, car_no='??'):
        self.parent = parent
        self.id = car_id
        self._car_no = car_no
        self._laps = 0
        self._class = None

    def car_no(self, val=None):
        if val is not None:
            self._car_no = val
            self.parent.refresh_gui_for_car(self)
        return self._car_no

    def laps(self, val=None):
        if val is not None:
            self._laps = val
        return self._laps

    def class_(self, val=None):
        if val is not None:
            self._class = val
            self.parent.add_class(val)
            self.parent.clean_classes()
            self.parent.refresh_gui_for_car(self)
        return self._class

    def encode(self):
        return {
            'car_no' : self._car_no,
            'class'   : self._class,
        }

    def decode(self, code):
        if 'car_no' in code: self._car_no = code['car_no']
        if 'class'  in code:
            self._class  = code['class']
            self.parent.add_class(self._class)
        return self

class chartdatacell:
    def __init__(self, parent, lap, pos, gui=None):
        self.parent = parent
        self.lap = lap
        self.pos = pos
        self._reset()
        self.gui = None
        if gui: self.attach_gui(gui)

    def attach_gui(self, gui):
        self.gui = gui.getCell(self.lap, self.pos)
        self.gui.set_data(self)

    def _reset(self):
        self._car = None
        self._lead = None
        self.bar_above = False
        self.bar_left = False

    def update_gui(self):
        if self.gui: self.gui.update()

    def reset(self):
        self._reset()
        self.update_gui()

    def update_bars(self):
        self.bar_above = False
        self.bar_left = False
        if self._lead is None:
            self.update_gui()
            return
        down = self.laps_down()
        if self.pos > 1:
            other_cell = self.parent.lookup(self.lap, self.pos - 1)
            if other_cell:
                other_down = other_cell.laps_down()
                self.bar_above = down and other_down == 0
        if self.lap > 1:
            other_cell = self.parent.lookup(self.lap - 1, self.pos)
            if other_cell:
                other_down = other_cell.laps_down()
                self.bar_left = down and other_down == 0
        self.update_gui()

    def car(self, val=None):
        if val is not None:
            self._car = val
            if self.lap > self._car.laps():
                self._car.laps(self.lap)
            self.update_gui()
        return self._car

    def lead(self, val=None):
        if val is not None:
            self._lead = val
            self.update_bars()
            other_cell = self.parent.lookup(self.lap, self.pos + 1)
            if other_cell: other_cell.update_bars()
            other_cell = self.parent.lookup(self.lap + 1, self.pos)
            if other_cell: other_cell.update_bars()
        return self._lead

    def laps_down(self):
        if self._lead is None: return None
        return self._lead - self.lap

    def bars(self):
        return (self.bar_above, self.bar_left)

    def encode(self):
        return (self._car.id, self._lead)

    def decode(self, code):
        self._car = self.parent.car(code[0])
        self._lead = code[1]
        if self.lap > self._car.laps():
            self._car.laps(self.lap)
        return self


class chartdata:
    def __init__(self, gui=None):
        self.gui = gui
        self.props = config.default_props.copy()
        self.cars = {}
        self.cells = []
        self._max_pos = 0
        self._max_down = 0
        self._classes = []

    def car(self, car_id, car_no='??', create=False):
        if car_id not in self.cars and not create:
            return None
        if car_id not in self.cars:
            self.cars[car_id] = chartcar(self, car_id, car_no)
        return self.cars[car_id]

    def num_laps(self):
        return len(self.cells)

    def max_pos(self, lap=None):
        if lap is None: return self._max_pos
        if lap > len(self.cells): return None
        return len(self.cells[lap-1])

    def max_down(self):
        return self._max_down

    def classes(self): return self._classes

    def add_class(self, class_):
        if class_ not in self._classes: self._classes.append(class_)

    def clean_classes(self):
        existing = set([car.class_() for car in self.cars.itervalues()])
        if len([c for c in self._classes if c not in existing]):
            self._classes[:] = [c for c in self._classes if c in existing]
            self.gui.update_fills()

    def lookup(self, lap, pos):
        if lap > len(self.cells): return None
        if pos > len(self.cells[lap-1]): return None
        return self.cells[lap-1][pos-1]

    def add(self, car_id, lap=None, pos=None, lead=None):
        car = self.car(car_id, car_no=car_id, create=True)

        # Determine lap and make sure we have enough columns
        if lap is None:
            lap = car.laps() + 1
        if lap > len(self.cells):
            old_nlaps = len(self.cells)
            self.cells.extend([[] for i in range(lap - len(self.cells))])
            if self.gui:
                self.gui.update_coloring(since=old_nlaps)
        if lap > car.laps():
            car.laps(lap)

        # Determine lead lap
        if lead is None:
            lead = len(self.cells)
            if lead < lap: lead = lap
        if lead - lap > self._max_down:
            self._max_down = lead - lap

        # Determine position and make sure we have enough cells
        if pos is None:
            pos = self.max_pos(lap) + 1
        if pos > self._max_pos:
            self._max_pos = pos
        if pos > self.max_pos(lap):
            self.cells[lap-1].extend([None] * (pos - self.max_pos(lap)))
        if not self.cells[lap-1][pos-1]:
            self.cells[lap-1][pos-1] = chartdatacell(self, lap, pos, self.gui)

        # Update the cell
        cell = self.cells[lap-1][pos-1]
        cell.car(car)
        cell.lead(lead)

    def refresh_gui_for_car(self, car):
        # Refresh all GUI cells containing a car
        # This is used when the car's attributes change
        if not self.gui: return
        for col in self.cells:
            for cell in col:
                if cell.car is car: cell.update_gui()

    def attach_gui(self, gui):
        self.gui = gui
        for col in self.cells:
            for cell in col:
                cell.attach_gui(gui)

    def encode(self):
        return {
            'cars' :  { k : v.encode() for (k,v) in self.cars.iteritems() },
            'cells' : [
                [ cell.encode() if cell else None for cell in lap ]
                for lap in self.cells ],
            'props' : self.props,
        }

    def decode(self, code):
        self.cars = { k : chartcar(self, k).decode(v)
                for (k,v) in code['cars'].iteritems() }
        self.cells = [
                [ chartdatacell(self, lap, pos).decode(attrs)
                    if attrs else None
                    for pos, attrs in enumerate(col, start=1) ]
                for lap, col in enumerate(code['cells'], start=1) ]
        if 'props' in code:
            for k,v in code['props'].iteritems():
                self.props[k] = v
        self._max_pos = max(len(lap) for lap in self.cells)
        self._max_down = max(cell.laps_down()
                for lap in self.cells
                for cell in lap)
        for cell in [ cell for lap in self.cells for cell in lap if cell ]:
            cell.update_bars()
