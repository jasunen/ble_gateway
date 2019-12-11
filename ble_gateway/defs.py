import sys

STOPMESSAGE = "STOP"
SCANMODE = "SCAN"
GWMODE = "GATEWAY"

C_SEC_COMMON = "common"
C_SEC_SOURCES = "sources"
C_SEC_DESTINATIONS = "destinations"

if sys.platform == "darwin":
    address = "/var/run/syslog"
    facility = "local1"
elif sys.platform == "linux":
    address = "/dev/log"
    facility = "local0"
else:
    address = ("localhost", 514)
    facility = "local0"

LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "detailed": {
            "class": "logging.Formatter",
            "format": "%(asctime)s %(processName)-10s \
            %(name)-15s.%(funcName)s: %(levelname)-8s %(message)s",
        },
        "syslog": {
            "class": "logging.Formatter",
            "format": "%(processName)-10s.%(name)-15s.\
            %(funcName)s: %(message)s",
        },
    },
    "handlers": {
        "file": {
            "class": "logging.FileHandler",
            "filename": "ble_gateway.log",
            "level": "ERROR",
            "mode": "a",
            "formatter": "detailed",
        },
        "syslog": {
            "class": "logging.handlers.SysLogHandler",
            "address": address,
            "facility": facility,
            "level": "INFO",
            "formatter": "syslog",
        },
    },
    "root": {"level": "INFO", "handlers": ["file", "syslog"]},
}

DEFAULT_CONFIG = {
    # Keys are case insensitive
    # Actually when reading the configuration
    # all the keys are converted to lowercase
    # BUT values are case SENSITIVE, so be carefull
    # Configuration has following sections:
    # 'common', 'sources', 'destinations'
    #
    # COMMON section:
    #
    C_SEC_COMMON: {
        "device": int(0),
        "no_messages_timeout": int(10),
        "simulator": int(0),
        "max_mesgs": int(0),
        "log_to_console": False,
    },
    #
    # SOURCES section:
    #
    C_SEC_SOURCES: {
        # Settings defined in source DEFAULTS are applied first
        # to all other defined sources. Additional settings
        # defined for a particular source will override settings
        # inherited from DEFAULTS
        "DEFAULTS": {
            "interval": 3,
            # fields in fields_order will be first, other fields remain as is
        },
        # Optional source settings for "*" will be applied to packets
        # which are not matched to any defined mac address
        "*": {
            # There is built-in destination called DROP which just discards
            # the packet and can be used in any source definition
            "destinations": ["DROP"]
        },
    },
    #
    # DESTINATIONS section:
    #
    C_SEC_DESTINATIONS: {
        # Settings defined in destination DEFAULTS are applied first
        # to all defined destinations. Additional settings
        # defined for a particular destination will override settings
        # inherited from DEFAULTS
        "DEFAULTS": {}
    },
}
