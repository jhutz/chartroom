import sys
import os
import re
import time
import codecs, struct
from config_data import config, CR_VERSION

## All dimensions in points
PAGE_WIDTH    = 8.5 * 72
PAGE_HEIGHT   = 11 * 72
MARGIN_LEFT   = 18
MARGIN_RIGHT  = 18
MARGIN_TOP    = 36
MARGIN_BOTTOM = 36
CELL_WIDTH    = 22.32
CELL_HEIGHT   = 8.5
FRAME_OFFSET  = 2
HEADER_ORIGIN = PAGE_HEIGHT - MARGIN_TOP - 59.5
CHART_ORIGIN  = HEADER_ORIGIN - 7 * CELL_HEIGHT

Fonts = {
        'TitleFont'     : ('Helvetica-Bold',      24),
        'SubtitleFont'  : ('Helvetica-Bold',      18),
        'InfoFont'      : ('Helvetica-Condensed',  9),
        'ChartFont'     : ('Helvetica',            7),
        'ChartBoldFont' : ('Helvetica-Bold',       7),
        }

Headers = [
        # row  right  font        prop,       text
        (  -3, False, 'Subtitle', 'session',  None),
        (   0, False, 'Title',    None,       'Chart'),
        (   2, False, 'Info',     'sanction', None),
        (   3, False, 'Info',     'venue',    None),
        (   4, False, 'Info',     'course',   None),

        (   0, True,  'Title',    'group',    None),
        (   3, True,  'Info',     'time',     None),
        (   4, True,  'Info',     'date',     None),
        ]

# XXX KLUDGE
progdir=os.path.dirname(os.path.realpath(sys.argv[0]))
Images = [
        # x,y are from top-left corner of page (None means use margin or center)
        # halign can be left/right/center (None means center)
        # valign can be top/bottom/center (None means center)
        #
        # x     y     halign    valign    scale  filename
        ( None, 12,    'center', 'top',    0.18,  progdir+'/logo.eps' ),
        ]

def propval(data, prop, default=None):
    if prop in data.props: return data.props[prop]
    if prop in config.global_props: return config.global_props[prop]
    if default is None: return ''
    return default

def ps_string(str): return re.sub(r'[()\\]', r'\\0', str)

def bbox_union(a, b):
    if   a[0] is None: r0 = b[0]
    elif b[0] is None: r0 = a[0]
    elif a[0] < b[0]:  r0 = a[0]
    else:              r0 = b[0]

    if   a[1] is None: r1 = b[1]
    elif b[1] is None: r1 = a[1]
    elif a[1] < b[1]:  r1 = a[1]
    else:              r1 = b[1]

    if   a[2] is None: r2 = b[2]
    elif b[2] is None: r2 = a[2]
    elif a[2] > b[2]:  r2 = a[2]
    else:              r2 = b[2]

    if   a[3] is None: r3 = b[3]
    elif b[3] is None: r3 = a[3]
    elif a[3] > b[3]:  r3 = a[3]
    else:              r3 = b[3]

    return (r0, r1, r2, r3)


def place_image(output, x0, y0, halign, valign, scale, path):
    with open(path, 'rb') as imgfile:
        data = imgfile.read()
    if data.startswith(codecs.decode('C5D0D3C6', 'hex')):
        (ps_off, ps_len) = struct.unpack_from('<II', data, offset=4)
        data = data[ps_off:ps_off+ps_len]

    match = re.search(r'(?im)^\%\%BoundingBox:\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*$', data)
    if not match:
        print '%s: no bbox' % path
        return

    # figure out the lower-left corner of the placement box
    bbox = [ int(x) for x in match.groups() ]
    width  = (bbox[2] - bbox[0]) * scale
    height = (bbox[3] - bbox[1]) * scale
    if halign == 'center':
        if x0 is None: x0 = PAGE_WIDTH / 2
        x0 = x0 - width / 2
    elif halign == 'right':
        if x0 is None: x0 = PAGE_WIDTH - MARGIN_RIGHT
        x0 = x0 - width
    elif x0 is None:
        x0 = MARGIN_LEFT
    if y0 is not None: y0 = PAGE_HEIGHT - y0
    if valign == 'center':
        if y0 is None: y0 = PAGE_HEIGHT // 2
        y0 = y0 - height / 2
    elif valign == 'bottom':
        if y0 is None: y0 = MARGIN_BOTTOM
    else:
        if y0 is None: y0 = PAGE_HEIGHT - MARGIN_TOP
        y0 = y0 - height
    output.write('BeginEPSF\n')
    output.write('%.2f %.2f translate %.2f %.2f scale\n' % (x0, y0, scale, scale))
    output.write('%.2f %.2f translate\n' % (-bbox[0], -bbox[1]))
    output.write('%%%%BeginDocument: %s\n' % path)
    output.write(data)
    output.write('%%EndDocument\n')
    output.write('EndEPSF\n')
    return (x0, y0, x0 + width, y0 + height)

def emit_one_page(data, output, pageno, first_lap, n_laps, top_pos, n_pos):
    page_bbox = (MARGIN_LEFT, None, None, PAGE_HEIGHT - MARGIN_TOP)

    output.write('%%%%Page: %d %d\n' % (pageno, pageno))

    # Page Headers
    # We consider headers in the bounding box calculation, but only loosely. 
    # Specifically, we stretch the bbox to include the "outside" edge of the
    # text (toward the marging), but not the "inside" edge, which would require
    # string width calculations. And we include the top and bottom of a region
    # which begins at the specified row and extends upwards as far as the font
    # size in points. This _should_ all be OK because the chart edges will be
    # beyond the "inside" text edges, and we always stretch the bbox all the
    # way to the top page margin.
    lastfont = ''
    for (row, right, font, prop, default) in Headers:
        text = propval(data, prop, default)
        row_y = HEADER_ORIGIN - row * CELL_HEIGHT
        text_h = Fonts[font+'Font'][1]
        if font != lastfont:
            lastfont = font
            output.write('%sFont setfont\n' % font)
        if right:
            output.write('(%s) %d ralign %d moveto show\n' %
                    (ps_string(text), PAGE_WIDTH - MARGIN_RIGHT, row_y))
            page_bbox = bbox_union(page_bbox,
                    (None, row_y, PAGE_WIDTH - MARGIN_RIGHT, row_y + CELL_HEIGHT))
        else:
            output.write('(%s) %d %d moveto show\n' % (text, MARGIN_LEFT, row_y))
            page_bbox = bbox_union(page_bbox,
                    (MARGIN_LEFT, row_y, None, row_y + CELL_HEIGHT))
    for img in Images:
        bbox = place_image(output, *img)
        page_bbox = bbox_union(page_bbox, bbox)

    # Column/Row headers
    # Including the frame in the page bbox covers all the chart's contents,
    # the width of the lap headers, and the height of the row headers. The
    # other header dimensions are covered by extending to the left and top
    # margins.
    output.write('ChartBoldFont setfont\n')
    output.write('(Laps) %d %d moveto show\n' % (
        MARGIN_LEFT + CELL_WIDTH, CHART_ORIGIN + CELL_HEIGHT))
    output.write('(Pos) %d %d moveto show\n' % (MARGIN_LEFT, CHART_ORIGIN))
    x0 = MARGIN_LEFT + CELL_WIDTH               + FRAME_OFFSET
    y0 = CHART_ORIGIN                           - FRAME_OFFSET
    x1 = MARGIN_LEFT  + CELL_WIDTH * (n_laps+1) + FRAME_OFFSET
    y1 = CHART_ORIGIN - CELL_HEIGHT * n_pos     - FRAME_OFFSET
    output.write('%d %d moveto %d %d lineto %d %d lineto stroke\n' %
            (x0, y1, x0, y0, x1, y0))
    page_bbox = bbox_union(page_bbox, (x0, y1, x1, y0))
    for lap in range(n_laps):
        cell_x = MARGIN_LEFT + (lap + 1) * CELL_WIDTH
        output.write('(%d) %d %d center %d moveto show\n' % (
            first_lap + lap, cell_x, CELL_WIDTH, CHART_ORIGIN))
    for pos in range(n_pos):
        cell_y = CHART_ORIGIN - (pos + 1) * CELL_HEIGHT
        output.write('(%d) %d ralign %d moveto show\n' % (
            top_pos + pos, MARGIN_LEFT + CELL_WIDTH, cell_y))

    # laps
    laps = data.num_laps()
    output.write('ChartModePlain\n')
    mode = "Plain"
    for lap in range(n_laps):
        cell_x = MARGIN_LEFT + (lap + 1) * CELL_WIDTH

        last_pos = min(n_pos, data.max_pos(first_lap + lap) - top_pos + 1)
        if last_pos <= 0: continue
        for pos in range(last_pos):
            cell_y = CHART_ORIGIN - (pos + 1) * CELL_HEIGHT
            cell = data.lookup(first_lap + lap, top_pos + pos)
            lead = cell.lead()
            bars = cell.bars()

            if lead == laps: newmode = "Final"
            elif lead % 5:   newmode = "Plain"
            elif lead % 10:  newmode = "Odd"
            else:            newmode = "Even"
            if mode != newmode:
                output.write("ChartMode%s\n" % newmode)
                mode = newmode
            output.write('(%s) %d %d center %d moveto show\n' % (
                ps_string(cell.car().car_no()),
                cell_x, CELL_WIDTH, cell_y))
            if bars[0] and bars[1]:
                output.write('%d %d moveto %d %d lineto %d %d lineto stroke\n' % (
                    cell_x + FRAME_OFFSET,
                    cell_y - FRAME_OFFSET,
                    cell_x + FRAME_OFFSET,
                    cell_y - FRAME_OFFSET + CELL_HEIGHT,
                    cell_x + FRAME_OFFSET + CELL_WIDTH,
                    cell_y - FRAME_OFFSET + CELL_HEIGHT))
            elif bars[0]:
                output.write('%d %d moveto %d %d lineto stroke\n' % (
                    cell_x + FRAME_OFFSET,
                    cell_y - FRAME_OFFSET + CELL_HEIGHT,
                    cell_x + FRAME_OFFSET + CELL_WIDTH,
                    cell_y - FRAME_OFFSET + CELL_HEIGHT))
            elif bars[1]:
                output.write('%d %d moveto %d %d lineto stroke\n' % (
                    cell_x + FRAME_OFFSET,
                    cell_y - FRAME_OFFSET,
                    cell_x + FRAME_OFFSET,
                    cell_y - FRAME_OFFSET + CELL_HEIGHT))
    output.write('showpage\n\n')
    return page_bbox


def save_ps(data, path):
    fontfaces = { x[0] for x in Fonts.values() }
    doc_bbox = (None, None, None, None)

    with open(path, 'w') as output:
        output.write('%!PS-Adobe-3.0\n')
        output.write('%%Pages: (atend)\n')
        output.write('%%%%Creator: ChartRoom v%s\n' % CR_VERSION)
        output.write('%%%%CreationDate: %s\n' % time.ctime())
        output.write('%%Title: Lap Chart\n')
        output.write('%%BoundingBox: (atend)\n')
        output.write('%%%%DocumentMedia: Plain %d %d 0 white ()\n' %
                (PAGE_WIDTH, PAGE_HEIGHT))
        output.write('%%Orientation: Portrait\n')
        output.write('%%%%DocumentNeededResources: font %s\n' % ' '.join(fontfaces))
        output.write('%%EndComments\n')

        output.write('%%BeginProlog\n')
        output.write(PS_PROLOG)
        output.write('%%EndProlog\n')

        output.write('%%BeginSetup\n')
        for font in fontfaces:
            output.write('%%%%IncludeResource: font %s\n' % font)
        for (name, font) in Fonts.iteritems():
            output.write('/%s /%s findfont %d scalefont def\n' % (name, font[0], font[1]))
        output.write('%%EndSetup\n')

        page_bbox = emit_one_page(data, output, 1, 1, data.num_laps(), 1, data.max_pos())
        doc_bbox = bbox_union(doc_bbox, page_bbox)
        output.write('%%Trailer\n')
        output.write('%%%%Pages: %d\n' % 1)
        output.write('%%%%BoundingBox: %d %d %d %d\n' % doc_bbox)


PS_PROLOG = """
/ralign { 1 index stringwidth pop sub } def
/center { 2 index stringwidth pop sub 2 div add } def
/ChartModePlain { ChartFont     setfont 0 setgray } def
/ChartModeOdd   { ChartBoldFont setfont 0 0 1 setrgbcolor } def
/ChartModeEven  { ChartBoldFont setfont 1 0 0 setrgbcolor } def
/ChartModeFinal { ChartBoldFont setfont 1 0 1 setrgbcolor } def

/BeginEPSF { %def
  /b4_Inc_state save def                % Save state for cleanup
  /dict_count countdictstack def        % Count objects on dict stack
  /op_count count 1 sub def             % Count objects on operand stack
  userdict begin                        % Push userdict on dict stack
  /showpage { } def                     % Redefine showpage, { } = null proc
  0 setgray 0 setlinecap                % Prepare graphics state
  1 setlinewidth 0 setlinejoin
  10 setmiterlimit [ ] 0 setdash newpath
  /languagelevel where                  % If level not equal to 1 then
  {pop languagelevel                    % set strokeadjust and
  1 ne                                  % overprint to their defaults.
    {false setstrokeadjust false setoverprint
    } if
  } if
} bind def

/EndEPSF { %def
  count op_count sub {pop} repeat       % Clean up stacks
  countdictstack dict_count sub {end} repeat
  b4_Inc_state restore
} bind def
"""
