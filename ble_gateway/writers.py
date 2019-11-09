from influxdb import InfluxDBClient


class Writer:
    # Parent class for all the writer classes

    def __init__(self, wname, wconfig):
        # each subclass init() should call super().__init__()
        self.name = wname
        self.type = wconfig["type"]
        self.intervall = wconfig.get("intervall", 0)
        self.packetcount = 0

    def process_msg(self, mesg, mconfig):
        # Each writer subclass should implement destination specific process
        # and call super().process_msg()
        self.packetcount += 1

    def order_fields(self, mesg, fields):
        ordered_fields = {}
        for f in fields:
            if f in mesg:
                ordered_fields[f] = mesg.pop(f)
        mesg = {**ordered_fields, **mesg}

    def rename_fields(self, mesg, fields):
        # NOTE! this will not preserve order of the fields
        for f in fields:
            if f in mesg:
                mesg[f] = mesg.pop(f)

    def remove_fields(self, mesg, fields):
        for f in fields:
            if f in mesg:
                mesg.pop(f)

    def add_fields(self, mesg, fields):
        for f in fields:
            (t, v) = f.split("=")
            if t and v:
                mesg[t] = v


class InfluxDBWriter(Writer):
    # Writer class for InfluxDB destination

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
    def __init__(self, wname, wconfig):
        super().__init__(wname, wconfig)
        self.filename = wconfig.get("filename", "default_file.out")


class ThingspeakWriter(Writer):
    # Writer class for Thingspeak destination
    def __init__(self, wname, wconfig):
        super().__init__(wname, wconfig)


class DropWriter(Writer):
    # Will simply drop the packet
    def __init__(self, wname, wconfig):
        super().__init__(wname, wconfig)

    def process_msg(self, mesg, mconfig):
        super().process_msg(mesg, mconfig)
        return True


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

    def add_writer(self, wname, wconfig):
        wtype = wconfig.get("type", None)
        if wtype in self.writer_classes:
            new_writer = self.writer_classes[wtype](wname, wconfig)
        if new_writer:
            self.all_writers[wname] = new_writer
            return new_writer
        else:
            return None

    def add_writers(self, wnames, wconfig):
        if isinstance(wnames, (list, tuple)):
            for wname in wnames:
                self.addWriter(wname, wconfig)
            return self.all_writers

    def get_writer(self, wname):
        return self.all_writers.get[wname, None]
