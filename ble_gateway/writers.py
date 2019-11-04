from influxdb import InfluxDBClient


class Writer:
    # Parent class for all the writer classes
    name = ""
    type = ""

    def __init__(self, wname, wtype):
        self.name = wname
        self.type = wtype


class InfluxDBWriter(Writer):
    # Writer class for InfluxDB destination
    host = "localhost"
    port = 8086
    dbuser = "root"
    dbpassword = "root"
    dbname = "example"
    conn = None

    def __init__(self, wname, wconfig):
        super().__init__(wname, "influxdb")
        self.host = wconfig.get("host", self.host)
        self.port = wconfig.get("port", self.port)
        self.dbuser = wconfig.get("dbuser", self.dbuser)
        self.dbpassword = wconfig.get("dbpassword", self.dbpassword)
        self.dbname = wconfig.get("dbname", self.dbname)
        self.conn = InfluxDBClient(
            host=self.host,
            port=self.host,
            database=self.dbname,
            username=self.dbuser,
            password=self.dbpassword,
        )


class FileWriter(Writer):
    # Writer class for file destination
    def __init__(self, wname, wconfig):
        super().__init__(wname, "file")


class ThingspeakWriter(Writer):
    # Writer class for Thingspeak destination
    def __init__(self, wname, wconfig):
        super().__init__(wname, "thingspeak")


class Writers:
    # collection of writer classes
    # all_writers = {}
    writer_types = {
        "file": FileWriter,
        "influxdb": InfluxDBWriter,
        "thingspeak": ThingspeakWriter,
    }

    def addWriter(self, wname, wconfig):
        wtype = wconfig.get("type", None)
        if wtype in self.writer_types:
            new_writer = self.writer_types[wtype](wname, wconfig)
        if new_writer:
            self.all_writers[wname] = new_writer
            return new_writer
        else:
            return None

    def getWriter(self, wname):
        return self.all_writers.get[wname, None]
