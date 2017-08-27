class chartcar:
    # XXX update GUI when something changes
    def __init__(self, parent, car_id, car_no='??'):
        self.parent = parent
        self.id = id
        self._car_no = car_no
        self._laps = 0
        self._class = None

    def car_no(self, val=None):
        if val != None: self._car_no = val
        return self._car_no

    def laps(self, val=None):
        if val != None: self._laps = val
        return self._laps

    def class_(self, val=None):
        if val != None: self._class = val
        return self._class

class chartdatacell:
    # XXX update GUI when something changes
    def __init__(self, parent, lap, pos, gui=None):
        self.parent = parent
        self.lap = lap
        self.pos = pos
        if gui: self.gui = gui.getCell(lap, pos)
        else:   self.gui = None
        self._car = None
        self._lead = None

    def reset(self):
        self._car = None
        self._lead = None
        if self.gui: self.gui.set(None)

    def car(self, val=None):
        if val != None:
            self._car = val
            if self.gui: self.gui.set(val)
        return self._car

    def lead(self, val=None):
        if val != None: self._lead = val
        return self._lead


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
        if lap == None: return self.maxpos
        if lap > len(self.cells): return None
        return len(self.cells[lap-1])

    def lookup(self, lap, pos):
        if lap > len(self.cells): return None
        if pos > len(self.cells[lap-1]): return None
        return self.cells[lap-1][pos-1]

    def add(self, car_id, lap=None, pos=None, lead=None):
        car = self.car(car_id, car_no=car_id, create=True)

        # Determine lap and make sure we have enough columns
        if lap == None:
            lap = car.laps() + 1
        if lap > len(self.cells):
            self.cells.extend([[] for i in range(lap - len(self.cells))])
        if lap > car.laps():
            car.laps(lap)

        # Determine lead lap
        if lead == None:
            lead = len(self.cells)
            if lead < lap: lead = lap

        # Determine position and make sure we have enough cells
        if pos == None:
            pos = self.max_pos(lap) + 1
        if pos > self.maxpos:
            self.maxpos = pos
        if pos > self.max_pos(lap):
            self.cells[lap-1].extend([None] * (pos - self.max_pos(lap)))
        if self.cells[lap-1][pos-1] == None:
            self.cells[lap-1][pos-1] = chartdatacell(self, lap, pos, self.gui)

        # Update the cell
        cell = self.cells[lap-1][pos-1]
        cell.car(car)
        cell.lead(lead)