CR_VERSION = '0.1'

HIGHLIGHT_CARS = 'cars'
HIGHLIGHT_LAP  = 'lead_lap'

SHADE_NONE  = 'none'
SHADE_CLASS = 'class'
SHADE_DOWN  = 'laps_down'

class ChartRoomConfig:
    def __init__(self):
        self.def_highlight = HIGHLIGHT_CARS
        self.def_shade = SHADE_NONE

        self.global_props = {}
        self.default_props = {}

        self.lap_colors       = [
                '#000', # black
                '#00f', # blue
                '#f00', # red
                '#0f0', # green
                '#f0f', # purple
                ]

        self.highlight_colors = [
                '#ff0', # bright yellow
                '#0ff', # cyan
                ]

        self.class_colors     = [
                '#fcc', # red
                '#cfc', # green
                '#aef', # blue
                '#ffc', # yellow
                '#fda', # orange
                '#fcf', # purple
                '#ddd', # gray
                ]

        self.laps_down_colors = [ 
                '#ddd', # gray
                '#aef', # blue
                '#cfc', # green
                '#ffc', # yellow
                '#fda', # orange
                '#fcc', # red
                '#fcf', # purple
                ]

    def load():
        pass
    
    def save():
        pass

config = ChartRoomConfig()
