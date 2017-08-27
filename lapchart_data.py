class chartcar:
    def __init__(self, parent, car_id, car_no='??'):
        self.parent = parent
        self.id = id
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
            self.parent.refresh_gui_for_car(self)
        return self._class

class chartdatacell:
    def __init__(self, parent, lap, pos, gui=None):
        self.parent = parent
        self.lap = lap
        self.pos = pos
        self._car = None
        self._lead = None
        self.bar_above = False
        self.bar_left = False
        if gui:
            self.gui = gui.getCell(lap, pos)
            self.gui.set_data(self)
        else:
            self.gui = None

    def update_gui(self):
        if self.gui: self.gui.update()

    def update_bars(self):
        self.bar_above = False
        self.bar_left = False
        if self._lead is None:
            if self.gui: self.gui.update()
            return
        down = self.laps_down()
        if self.pos > 1:
            other_cell = self.parent.lookup(self.lap, self.pos - 1)
            if other_cell:
                other_down = other_cell.laps_down()
                if other_down: self.bar_above = (down != other_down)
        if self.lap > 1:
            other_cell = self.parent.lookup(self.lap - 1, self.pos)
            if other_cell:
                other_down = other_cell.laps_down()
                if other_down: self.bar_left = (down != other_down)
        if self.gui: self.gui.update()

    def reset(self):
        self._car = None
        self._lead = None
        if self.gui: self.gui.update()

    def car(self, val=None):
        if val is not None:
            self._car = val
            if self.gui: self.gui.update()
        return self._car

    def lead(self, val=None):
        if val is not None:
            self._lead = val
            self.update_bars()
            other_cell = self.parent.lookup(self.lap, self.pos + 1)
            if other_cell: other_cell.update_bars()
            other_cell = self.parent.lookup(self.lap + 1, self.pos)
            if other_cell: other_cell.update_bars()
            if self.gui: self.gui.update()
        return self._lead

    def laps_down(self):
        if self._lead is None: return None
        return self._lead - self.lap

    def bars(self):
        return (self.bar_above, self.bar_left)


class chartdata:
    def __init__(self, gui=None):
        self.gui = gui
        self.cars = {}
        self.cells = []
        self.maxpos = 0

    def car(self, car_id, car_no='??', create=False):
        if car_id not in self.cars and not create:
            return None
        if car_id not in self.cars:
            self.cars[car_id] = chartcar(self, car_id, car_no)
        return self.cars[car_id]

    def num_laps(self):
        return len(self.cells)

    def max_pos(self, lap=None):
        if lap is None: return self.maxpos
        if lap > len(self.cells): return None
        return len(self.cells[lap-1])

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
            self.cells.extend([[] for i in range(lap - len(self.cells))])
        if lap > car.laps():
            car.laps(lap)

        # Determine lead lap
        if lead is None:
            lead = len(self.cells)
            if lead < lap: lead = lap

        # Determine position and make sure we have enough cells
        if pos is None:
            pos = self.max_pos(lap) + 1
        if pos > self.maxpos:
            self.maxpos = pos
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
