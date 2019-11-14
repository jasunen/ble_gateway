import time
from queue import SimpleQueue

from influxdb import InfluxDBClient

from ble_gateway import helpers


class MessageBuffer:
    def __init__(self, batch_size):
        self.buffer = SimpleQueue()
        self.max_batch = batch_size

    def put(self, mesg):
        self.buffer.put(mesg)
        return self.max_batch - self.buffer.qsize()

    def get(self):
        if not self.buffer.empty():
            return self.buffer.get()
        return None

    def is_batch_ready(self):
        return self.max_batch <= self.buffer.qsize()


class IntervalChecker:
    def __init__(self, config=None):
        self.last_sent = {}
        self.intervals = {}
        self.default_interval = 0

        if isinstance(config, (int, float)):
            # Optional default_interval sets default time between packets
            self.default_interval = config
        elif isinstance(config, dict):
            for mac in config:
                if helpers.check_and_format_mac(mac):
                    i = config[mac].get("interval", config[mac].get("*", None))
                    if i is not None:
                        self.intervals[mac] = i
            self.default_interval = config[mac].get("*", 0)

    def is_wait_over(self, mac, interval=None, now=None):
        # named argument interval is optional and
        # if not specified (None) we use self.default_interval
        if interval is None:
            interval = self.intervals.get(mac, self.default_interval)
        if interval <= 0:  # No wait time
            return True

        # if optional now is not specified (None) we use time()
        if now is None:
            now = time.time()

        if mac not in self.last_sent:  # Must be first packet, so no need to wait
            self.last_sent[mac] = now  # mark last sent time
            return True

        if now - self.last_sent[mac] < interval:  # Must wait still to reach interval
            print("{} has interval {}, must wait.".format(mac, interval))
            return False  # Packet will be discarded

        self.last_sent[mac] = now  # mark last sent time
        return True


class Writer:
    # Parent class for all the writer classes
    type = "WriterBaseClass"

    def __init__(self, name=None, wconfig={}):
        if name:
            self.name = name
        else:
            self.name = self.type
        self.packetcount = 0
        self.waitlist = IntervalChecker(wconfig.get("interval", 0))
        self.buffer = MessageBuffer(wconfig.get("batch", 0))

        # Lastly call configure:
        self.configure(wconfig)

    def configure(self, wconfig):
        # Each subclass must define class specific configure()
        # which is then called by __init__ of the Writer base class
        pass

    def close(self):
        self.buffer.max_batch = 0
        self._process_buffer()  # Process remaining messages
        self._close()

    def send(self, mesg):
        self.packetcount += 1
        self.buffer.put(mesg)
        self._process_buffer()

    def _process_buffer(self):
        # Each writer subclass should implement destination specific process
        pass

    def rename_fields(self, mesg, fields):
        # NOTE! this will not preserve order of the fields
        for f in fields:
            (t, v) = f.split("=")
            if t and v and t in mesg:
                mesg[v] = mesg.pop(t)
        return mesg

    def remove_fields(self, mesg, fields):
        for f in fields:
            if f in mesg:
                mesg.pop(f)
        return mesg

    def add_fields(self, mesg, fields):
        for f in fields:
            (t, v) = f.split("=")
            if t and v:
                mesg[t] = v
        return mesg

    def order_fields(self, mesg, fields):
        ordered_fields = {}
        for f in fields:
            if f in mesg:
                ordered_fields[f] = mesg.pop(f)
        mesg = {**ordered_fields, **mesg}
        return mesg


class InfluxDBWriter(Writer):
    # Writer class for InfluxDB destination
    type = "influxdb"
    connection_defaults = {
        "host": "localhost",
        "port": 8086,
        "database": "",
        "username": "root",
        "password": "root",
    }
    # NOTE! Timestamp must be integer in milliseconds for the influxDB

    def configure(self, wconfig):
        # {k:d[k] for k in set(d).intersection(l)}
        self.connection_settings = self.connection_defaults.copy()
        self.connection_settings.update(
            {k: wconfig[k] for k in set(wconfig).intersection(self.connection_defaults)}
        )
        self.conn = InfluxDBClient(**self.connection_settings)

    def _process_buffer(self):
        pass


class FileWriter(Writer):
    # Writer class for file destination
    type = "file"

    def configure(self, wconfig):
        self.filename = wconfig.get("filename", "")
        self.f_handle = None
        if not self.filename:
            print("No filename specified!")
            return

        self.f_handle = open(self.filename, "a+")

    def _process_buffer(self):
        if self.f_handle is not None:
            if self.buffer.is_batch_ready():
                while not self.buffer.empty():
                    mesg = self.buffer.get()
                    mesg["timestamp"] = time.ctime(mesg["timestamp"])
                    self.f_handle.write("{}\r\n".format(mesg))

    def _close(self):
        if self.f_handle is not None:
            self.f_handle.close()


class ThingspeakWriter(Writer):
    # Writer class for Thingspeak destination
    type = "thingspeak"

    def configure(self, wconfig):
        pass

    def _process_buffer(self):
        pass


class DropWriter(Writer):
    # Will simply drop the packet
    type = "DROP"


class ScanWriter(Writer):
    type = "SCAN"

    def configure(self, wconfig={}):
        self.seen_macs = {}

    def _process_buffer(self):
        if self.buffer.is_batch_ready():
            while not self.buffer.empty():
                mesg = self.buffer.get()
                mesg["timestamp"] = time.ctime(mesg["timestamp"])
                self.seen_macs[mesg["mac"]] = mesg["decoder"]
                print(mesg)

    def _close(self):
        print("--------- Collected macs ------------:")
        for mac, decoder in self.seen_macs.items():
            print(mac, decoder)


class Writers:
    # collection of writer classes

    def __init__(self):
        self.all_writers = {}
        self.destinations = {}
        self.writer_classes = {}
        for cls in Writer.__subclasses__():
            self.writer_classes[cls.type] = cls

        # add built-in Writers
        self.add_writers({"DROP": {"type": "DROP"}, "SCAN": {"type": "SCAN"}})

    def setup_routing(self, sources_config):
        for mac in sources_config:
            self.destinations[mac] = sources_config[mac].get("destinations", "DROP")
        print(sources_config)
        print(self.destinations)

    def send(self, mesg):
        if not self.destinations:
            print("{} - Routing not setup!".format(self))
            return

        print("Writers.send(): mesg:", mesg)
        dest_list = self.destinations.get(mesg["mac"], self.destinations.get("*"))
        for dest in dest_list:
            if dest in self.all_writers:
                print("Sending {} to {}.".format(mesg["mac"], self.all_writers[dest]))
                self.all_writers[dest].send(mesg.copy())

    def close(self):
        for w in self.all_writers.items():
            w.close()

    def add_writer(self, wname, wconfig):
        wtype = wconfig.get("type", None)
        if wtype in self.writer_classes:
            new_writer = self.writer_classes[wtype](wname, wconfig)
            if new_writer:
                self.all_writers[wname] = new_writer
                return new_writer
            else:
                return None

    def add_writers(self, wconfigs):
        for wname in wconfigs:
            if wname != "defaults":
                self.add_writer(wname, wconfigs[wname])
        return self.all_writers

    def get_writer(self, wname):
        return self.all_writers.get[wname, None]
