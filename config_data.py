CR_VERSION = '0.1'
CR_YEARS   = '2017'
CR_AUTHOR  = 'Jeffrey Hutzelman'
CR_URL     = ''
CR_EMAIL   = 'jhutz@cmu.edu'

CR_COPYRIGHT = '''
Copyright C %s, %s.  All rights reserved.

%s
%s
'''

HIGHLIGHT_CARS = 'cars'
HIGHLIGHT_LAP  = 'lead_lap'

SHADE_NONE  = 'none'
SHADE_CLASS = 'class'
SHADE_DOWN  = 'laps_down'

COLOR_NONE = 'none'
COLOR_NORMAL  = 'traditional'
COLOR_RAINBOW = 'rainbow'


class ChartRoomConfig:
    def __init__(self):
        self.def_highlight = HIGHLIGHT_CARS
        self.def_shading = SHADE_NONE
        self.color_mode = COLOR_NORMAL

        # Settings for traditional coloring
        self.color_laps = True        # Color...
        self.color_bold = True        # Bold...
        self.color_period = 5         # ... every Nth lap
        self.color_final = True       # Last lap in reserved color
        self.bold_final = True        # Last lap in bold

        # Settings for rainbox coloring
        self.rainbow_bold = True      # Last lap in bold

        self.global_props = {}
        self.default_props = {}

        # Colors for lap coloring (traditional or rainbow modes)
        # In traditional mode, the first color is used for uncolored laps.
        # In traditional mode, if color_final is true, the last color is
        # reserved for use on the final lap.
        self.lap_colors       = [
                '#000', # black
                '#00f', # blue
                '#f00', # red
                '#080', # green
                '#f0f', # purple
                ]

        # Color for car or lap highlighting
        self.highlight_color = '#ff0' # bright yellow

        # Colors for shading by class
        self.class_colors     = [
                '#fcc', # red
                '#cfc', # green
                '#aef', # blue
                '#ffc', # yellow
                '#fda', # orange
                '#fcf', # purple
                '#ddd', # gray
                ]

        # Colors for shading by laps down
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
