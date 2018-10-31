import socket
import threading
import codecs
import csv


try:
    import fcntl
    def cloexec(sock):
        flags = fcntl.fcntl(sock.fileno(), fcntl.F_GETFD)
        flags |= fcntl.FD_CLOEXEC
        fcntl.fcntl(sock.fileno(), fcntl.F_SETFD, flags)
except ImportError:
    def cloexec(sock):
        pass


class RMonitorRelay(object):
    def __init__(self, host, port, win):
        self.server = (host, port)
        self.win = win

    def _relay(self):
        sock = socket.create_connection(self.server, 5)
        cloexec(sock)
        sock.setblocking(True)
        rmon_file = sock.makefile("rb")
        rmon_csv = csv.reader(rmon_file)
        hb = False

        while True:
            try: fields = rmon_csv.next()
            except StopIteration: break
            if not fields:
                break
            fields = [ codecs.decode(x, 'cp1252') for x in fields ]
            if fields[0] == '$F':
                hb = not hb
                self.win.enqueue('hb', (hb,))
            elif fields[0] == '$G' and fields[3] != '':
                (stmt, pos, car, laps, time) = fields[0:5]
                self.win.enqueue('add', (car, car, None, int(laps), None))

    def start(self):
        server_thread = threading.Thread(target=self._relay)
        server_thread.name = 'RMonitor Relay'
        server_thread.daemon = True
        server_thread.start()
