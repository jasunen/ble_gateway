SCANMODE = "SCAN"
GWMODE = "GATEWAY"

C_SEC_COMMON = "common"
C_SEC_SOURCES = "sources"
C_SEC_DESTINATIONS = "destinations"

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
        "scan": False,
        "allowmac": [],
        "showraw": False,
        "advertise": int(0),
        "url": "http://0.0.0.0/",
        "txpower": int(0),
        "device": int(0),
        "writeconfig": None,
        "no_messages_timeout": int(10),
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
            "destinations": ["default_file"],
            "interval": 3,
            # fields in fields_order will be first, other fields remain as is
            "fields_order": ["timestamp", "mac"],
        },
        # Mac addresses (as they are keys) will be converted to lowercase
        "DA:B6:F7:69:C3:45": {
            "decoders": ["ruuviraw"],
            # fields in fields_order will be first, other fields remain as is
            "fields_add": ["location=Ulkona"],  # list vs dict vs list of tuples??
        },
        # Optional source settings for "*" will be applied to packets
        # which are not matched to any defined mac address
        "*": {
            "decoders": ["all", "unknown"],
            # There is built-in destination called DROP which just discards
            # the packet and can be used in any source definition
            "destinations": ["DROP"],
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
        "DEFAULTS": {
            "fields_rename": ["peer=mac"],
            "fields_remove": ["tx_power"],
            "interval": 6,
        },
        "default_file": {"type": "file", "filename": "default_file.out", "batch": 2},
    },
}
