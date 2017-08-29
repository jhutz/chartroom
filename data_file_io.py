import csv
from warnings import warn

CR_MAGIC = '#>ChartRoom-'

class FileFormatException(Exception): pass
class FileFormatWarning(UserWarning): pass

def _process_passings(data, reader, filename):
    fieldnames = reader.fieldnames
    for f in ['No.', 'Laps', 'Lead', 'Class', 'Name']:
        if f not in fieldnames:
            raise FileFormatException, "%s: missing field %s" % (filename,f)
    for row in reader:
        car_no = row['No.']
        if car_no == '' or car_no == '??': continue
        if row['Laps'] == '' or row['Lead'] == '':
            warn("%s[%d] (car %s): laps/lead missing" %
                    (filename, reader.line_num, car_no),
                    FileFormatWarning)
        lap = int(row['Laps'].strip('P '))
        if lap <= 0: continue
        lead = int(row['Lead'])
        class_ = row['Class']
        driver = row['Name']
        car_id = car_no + '_' + class_ + '_' + driver
        car = data.car(car_id, car_no, create=True)
        car.car_no(car_no)
        if class_ != '': car.class_(class_)
        if lap <= car.laps(): continue
        data.add(car_id, lap=lap, lead=lead)

def load_passings_txt(data, F, filename):
    reader = csv.DictReader(F, delimiter='\t', quoting=csv.QUOTE_NONE)
    _process_passings(data, reader, filename)

def load_passings_csv(data, F, filename):
    reader = csv.DictReader(F)
    _process_passings(data, reader, filename)

def load_file(data, path):
    with open(path, 'rU') as F:
        first = F.readline(1024)
        F.seek(0)
        if first.startswith(CR_MAGIC):
            raise FileFormatException, "%s: can't load charts yet" % filename
        elif '\t' in first:
            load_passings_txt(data, F, path)
        else:
            load_passings_csv(data, F, path)
