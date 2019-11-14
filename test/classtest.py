import sys
from pprint import pprint

import writers

# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, "/home/jani/Projects/ble_gateway/ble_gateway")


C_SEC_COMMON = "common"
C_SEC_SOURCES = "sources"
C_SEC_DESTINATIONS = "destinations"

DEFAULT_CONFIG = {
    C_SEC_COMMON: {
        "scan": False,
        "allowmac": [],
        "showraw": False,
        "advertise": int(0),
        "url": "http://0.0.0.0/",
        "txpower": int(0),
        "device": int(0),
        "writeconfig": None,
        "no_messages_timeout": int(600),
    },
    C_SEC_SOURCES: {
        "DEFAULTS": {
            "destinations": ["default_file"],
            "interval": 10,
            "fields_order": ["timestamp", "mac"],
        },
        "DA:B6:F7:69:C3:45": {
            "decoders": ["ruuviraw"],
            "fields_add": ["location=Ulkona"],  # list vs dict vs list of tuples??
        },
        "*": {"decoders": ["all", "unknown"], "destinations": ["DROP"]},
    },
    C_SEC_DESTINATIONS: {
        "DEFAULTS": {
            "fields_rename": ["peer=mac"],
            "fields_remove": ["tx_power"],
            "interval": 20,
        },
        "influx_test": {
            "type": "influxdb",
            "host": "somehost",
            "port": 8086,
            "database": "test_db",
            "username": "user1234",
            "password": "mypassu",
            "batch": 15,
            "tags": ["location", "mac"],
            "fields_remove": ["decoder"],
        },
        "default_file": {"type": "file", "filename": "default_file.out"},
    },
}


destinations = writers.Writers()
destinations.add_writers(DEFAULT_CONFIG[C_SEC_DESTINATIONS])
destinations.setup_routing(DEFAULT_CONFIG[C_SEC_SOURCES])
