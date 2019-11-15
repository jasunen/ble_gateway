import time
from queue import SimpleQueue

from influxdb import InfluxDBClient

from ble_gateway import helpers


class MessageBuffer:
    def __init__(self, batch_size):
        self._buffer = SimpleQueue()
        self.max_batch = batch_size

    def put(self, mesg):
        self._buffer.put(mesg)
        return self.max_batch - self._buffer.qsize()

    def get(self):
        if not self._buffer.empty():
            return self._buffer.get()
        return None

    def is_batch_ready(self):
        return self.max_batch <= self._buffer.qsize()

    def empty(self):
        return self._buffer.empty()


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
            # print("{} has interval {}, must wait.".format(mac, interval))
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
        self.config = wconfig
        # Lastly call configure:
        self.configure(wconfig)

    def configure(self, wconfig):
        # Each subclass must define class specific configure()
        # which is then called by __init__ of the Writer base class
        pass

    def close(self):
        self.buffer.max_batch = 0
        self._process_buffer()  # Process remaining messages
        print(self.name, "closing,", self.packetcount, "messages processed.")
        self._close()

    def send(self, mesg):
        if self.waitlist.is_wait_over(mesg["mac"]):
            self.packetcount += 1
            mesg = self.modify_packet(mesg, self.config)
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

    def modify_packet(self, mesg, mconfig):
        # *** do per source modifications:
        # 1. Remove fields
        mesg = self.remove_fields(mesg, mconfig.get("fields_remove", []))
        # 2. Rename fields
        mesg = self.rename_fields(mesg, mconfig.get("fields_rename", []))
        # 3. Add fields
        mesg = self.add_fields(mesg, mconfig.get("fields_add", []))
        # 4. Order fields
        mesg = self.order_fields(mesg, mconfig.get("fields_order", []))

        return mesg


class InfluxDBWriter(Writer):
    # Writer class for InfluxDB destination
    type = "influxdb"
    connection_defaults = {
        "host": "localhost",
        "port": 8086,
        "database": "none",
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
        self.tags = wconfig.get("tags", [])
        self.measurement = wconfig.get("measurement", None)

    def _process_buffer(self):
        if self.f_handle is not None:
            if self.buffer.is_batch_ready():
                data = []
                influx_mesg = "{measurement},{tags} {fields} {timestamp}"
                while not self.buffer.empty():
                    mesg = self.buffer.get()
                    mesg["timestamp"] = int(mesg["timestamp"] * 1000)
                    # Construct InfluxDB line protocol message
                    measurement = self.measurement
                    timestamp = mesg.pop("timestamp")
                    tags = []
                    for tag in self.tags:
                        if tag in list(mesg.keys()):
                            tags.append("{}={}".format(tag, mesg.pop(tag)))
                    tags.sort()
                    fields = []
                    for field, value in mesg.items():
                        fields.append("{}={}".format(field, value))
                    data.append(
                        influx_mesg.format(
                            measurement=measurement,
                            tags=",".join(tags),
                            fields=",".join(fields),
                            timestamp=timestamp,
                        )
                    )


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
        print(self.filename, self.f_handle.writable())

    def _process_buffer(self):
        if self.f_handle is not None:
            if self.buffer.is_batch_ready():
                while not self.buffer.empty():
                    mesg = self.buffer.get()
                    mesg["timestamp"] = time.ctime(mesg["timestamp"])
                    self.f_handle.write("{}\r\n".format(mesg))

    def _close(self):
        if self.f_handle is not None:
            self.f_handle.flush()
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
        while not self.buffer.empty():
            mesg = self.buffer.get()
            mesg["timestamp"] = time.ctime(mesg["timestamp"])
            self.seen_macs[mesg["mac"]] = mesg

    def _close(self):
        print("--------- Scanned macs ------------:")
        for mac, mesg in self.seen_macs.items():
            mesg = self.order_fields(mesg, ["timestamp" "mac" "decoder"])
            print(mesg)


class Writers:
    # collection of writer classes

    def __init__(self):
        self.all_writers = {}
        self.destinations = {}
        self.writer_classes = {}
        for cls in Writer.__subclasses__():
            self.writer_classes[cls.type] = cls

    def setup_routing(self, sources_config):
        for mac in sources_config:
            self.destinations[mac] = sources_config[mac].get("destinations", "DROP")

    def send(self, mesg):
        if not self.destinations:
            print("{} - Routing not setup!".format(self))
            return

        # print("Writers.send(): mesg:", mesg)
        dest_list = self.destinations.get(mesg["mac"], self.destinations.get("*"))
        for dest in dest_list:
            if dest in self.all_writers:
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
