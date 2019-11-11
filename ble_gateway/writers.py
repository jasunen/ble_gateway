import time

from influxdb import InfluxDBClient


class IntervalChecker:
    def __init__(self, default_interval=0):
        # Optional default_interval sets default time between packets
        self.default_interval = default_interval
        self.last_sent = {}

    def is_wait_over(self, mac, interval=None, now=None):
        # named argument interval is optional and
        # if not specified (None) we use self.default_interval
        if interval is None:
            interval = self.default_interval
        if interval <= 0:  # No wait time
            return True
        # if optional now is not specified (None) we use time()
        if now is None:
            now = int(time.time())

        if mac not in self.last_sent:  # Must be first packet, so no need to wait
            self.last_sent[mac] = now  # mark last sent time
            return True

        if now - self.last_sent[mac] < interval:  # Must wait still to reach interval
            return False  # Packet will be discarded

        self.last_sent[mac] = now  # mark last sent time
        return True


class Writer:
    # Parent class for all the writer classes
    type = ""

    def __init__(self, wname, wconfig):
        # each subclass init() should call super().__init__()
        self.name = wname
        # self.type = wconfig["type"]
        self.interval = wconfig.get("interval", 0)
        self.packetcount = 0
        self.waitlist = IntervalChecker(self.interval)

    def process_msg(self, mesg):
        # Each writer subclass should implement destination specific process
        # and call super().process_msg()
        self.packetcount += 1

    def rename_fields(self, mesg, fields):
        # NOTE! this will not preserve order of the fields
        for f in fields:
            if f in mesg:
                mesg[f] = mesg.pop(f)
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

    def __init__(self, wname, wconfig):
        super().__init__(wname, wconfig)
        self.host = wconfig.get("host", "localhost")
        self.port = wconfig.get("port", 8086)
        self.dbuser = wconfig.get("dbuser", "root")
        self.dbpassword = wconfig.get("dbpassword", "root")
        self.dbname = wconfig.get("dbname", "example")
        self.conn = InfluxDBClient(
            host=self.host,
            port=self.port,
            database=self.dbname,
            username=self.dbuser,
            password=self.dbpassword,
        )


class FileWriter(Writer):
    # Writer class for file destination
    type = "file"

    def __init__(self, wname, wconfig):
        super().__init__(wname, wconfig)
        self.filename = wconfig.get("filename", "default_file.out")


class ThingspeakWriter(Writer):
    # Writer class for Thingspeak destination
    type = "thingspeak"

    def __init__(self, wname, wconfig):
        super().__init__(wname, wconfig)


class DropWriter(Writer):
    # Will simply drop the packet
    type = "DROP"

    def __init__(self, wname, wconfig):
        super().__init__(wname, wconfig)


class Writers:
    # collection of writer classes

    def __init__(self):
        self.all_writers = {}
        self.writer_classes = {
            "file": FileWriter,
            "influxdb": InfluxDBWriter,
            "thingspeak": ThingspeakWriter,
            "DROP": DropWriter,
        }

    def send(self, mesg):
        pass

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
                self.addWriter(wname, wconfigs[wname])
        return self.all_writers

    def get_writer(self, wname):
        return self.all_writers.get[wname, None]
