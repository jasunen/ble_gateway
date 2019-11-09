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
        "advertise": 0,
        "url": "http://0.0.0.0/",
        "txpower": 0,
        "device": 0,
        "writeconfig": None,
        "no_messages_timeout": 600,
    },
    #
    # SOURCES section:
    #
    C_SEC_SOURCES: {
        # Settings defined in source _DEFAULTS_ are applied first
        # to all other defined sources. Additional settings
        # defined for a particular source will override settings
        # inherited from _DEFAULTS_
        "_DEFAULTS_": {
            "destinations": ["default_file"],
            "intervall": 10,
            # fields in fields_order will be first, other fields remain as is
            "fields_order": ["timestamp", "mac"],
            "tags": ["gateway=raspi4"],  # list vs dict vs list of tuples??
        },
        # Mac addresses (as they are keys) will be converted to lowercase
        "DA:B6:F7:69:C3:45": {
            "decoders": ["all", "unknown"],
            "destinations": ["default_file"],
            "intervall": 10,
            # fields in fields_order will be first, other fields remain as is
            "fields_order": ["timestamp", "mac"],
            "fields_add": ["gateway=raspi4"],  # list vs dict vs list of tuples??
        },
        # source settings for "_UNKNOWN_" will be applied to packets
        # which are not matched to any mac in "sources"
        "_UNKNOWN_": {
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
        # Settings defined in destination _DEFAULTS_ are applied first
        # to all defined destinations. Additional settings
        # defined for a particular destination will override settings
        # inherited from _DEFAULTS_
        "_DEFAULTS_": {"fields_rename": {"peer": "mac"}, "fields_remove": ["tx_power"]},
        "default_file": {"type": "file", "filename": "default_file.out"},
    },
}
