import sys
import os.path

def emit_chart_ps(data, output):
    laps = data.num_laps()
    output.write("%d %d ChartFrame\n" % (laps, data.max_pos()))
    output.write("ChartModePlain\n")
    mode = "Plain"
    for lap in range(1, 1+laps):
        for pos in range(1, 1+data.max_pos(lap)):
            cell = data.lookup(lap, pos)
            lead = cell.lead()
            bars = cell.bars()

            if lead == laps: newmode = "Final"
            elif lead % 5:   newmode = "Plain"
            elif lead % 10:  newmode = "Odd"
            else:            newmode = "Even"
            if mode != newmode:
                output.write("ChartMode%s\n" % newmode)
                mode = newmode
            output.write("%d %d (%s) ChartCell\n" %
                    (lap, pos, cell.car().car_no()))
            if bars[0]:
                output.write("%d %d ChartBarAbove\n" % (lap, pos))
            if bars[1]:
                output.write("%d %d ChartBarLeft\n" % (lap, pos))

def process_ps(data, output, template, template_dir):
    for line in template:
        if line.strip() == '%%Insert-Chart-Here':
            emit_chart_ps(data, output)
        else:
            output.write(line)

def save_ps(data, path, template_path=None):
    if template_path is None:
        if hasattr(sys, "frozen"):
            mainprog = sys.executable
        else:
            mainprog = sys.argv[0]
        template_dir = os.path.dirname(mainprog)
        template_path = os.path.join(template_dir, 'template.ps')
    else:
        template_dir = os.path.dirname(template_path)

    with open(template_path, 'r') as template, open(path, 'w') as output:
        process_ps(data, output, template, template_dir)

