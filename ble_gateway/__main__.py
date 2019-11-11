#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os
import sys
from multiprocessing import Process, Queue

from ble_gateway import config_management, defs, helpers, run_ble, run_writers


def define_cmd_line_arguments(parser, defaults_dict):
    # Add command line arguments to the parser

    # helper func to verify macaddress
    def verify_mac(val):
        mac = helpers.check_and_format_mac(val)
        if mac:
            return mac
        else:
            raise argparse.ArgumentTypeError("%s is not a MAC address" % val)

    #
    # !! Use lowercase and no whitespaces in parameter names !!
    #
    parser.add_argument(
        "-c",
        "--configfile",
        metavar="FILE",
        type=str,
        default=os.path.join(os.path.dirname(__file__), "ble_gateway.config.yaml"),
        help="Configuration file to use. Default is ble_gateway.cofig.yaml \
        in the module's directory. Use - for no configfile.",
    )
    parser.add_argument(
        "-w",
        "--writeconfig",
        type=str,
        default=defaults_dict[defs.C_SEC_COMMON].get("writeconfig"),
        metavar="FILE",
        help="Write configuration to FILE or \
        - to print out configuration and exit.",
    )
    parser.add_argument(
        "-m",
        "--allowmac",
        type=verify_mac,
        default=defaults_dict[defs.C_SEC_COMMON].get("allowmac"),
        action="append",
        help="Filter and process these MAC addresses only. \
        Can be combined with --scan to look for specific mac(s) only. \
        In Gateway mode forwards messages from specified mac(s) only. \
        Note that this overrides allowmac list in the configuration file, if any.",
    )
    parser.add_argument(
        "-S",
        "--scan",
        action="store_true",
        default=defaults_dict[defs.C_SEC_COMMON].get("scan"),
        help="Start in Scan mode. Listen to broadcasts and just \
        collect mac addresses. \
        Disables forwarding of messages to any destination (writers). \
        With --decode option tries to identify message type. \
        ",
    )
    parser.add_argument(
        "--decode",
        metavar="DECODER",
        action="append",
        default=defaults_dict[defs.C_SEC_COMMON].get("decoder"),
        choices=["all", "ruuviraw", "ruuviurl", "eddy", "pebble", "unknown"],
        help="Optional. Decoders to enable in Scan mode. \
        Has no effect if --scan not enabled. \
        'all' will try all decoders. If any decoders enabled \
        will only return macs with successfull decode. \
        'unknown' includes packets which are not decoded. \
        ",
    )
    parser.add_argument(
        "-r",
        "--showraw",
        action="store_true",
        default=defaults_dict[defs.C_SEC_COMMON].get("showraw"),
        help="Show raw data for each received packet regardless of mode running.",
    )
    parser.add_argument(
        "-a",
        "--advertise",
        type=int,
        default=defaults_dict[defs.C_SEC_COMMON].get("advertise"),
        help="Broadcast like an EddyStone Beacon. \
        Set the interval between packet in millisec",
    )
    parser.add_argument(
        "-u",
        "--url",
        type=str,
        default=defaults_dict[defs.C_SEC_COMMON].get("url"),
        help="When broadcasting like an EddyStone Beacon, set the url.",
    )
    parser.add_argument(
        "-t",
        "--txpower",
        default=defaults_dict[defs.C_SEC_COMMON].get("txpower"),
        type=int,
        help="When broadcasting like an EddyStone Beacon, set the Tx power",
    )
    parser.add_argument(
        "-D",
        "--device",
        type=int,
        default=defaults_dict[defs.C_SEC_COMMON].get("device"),
        help="Select the hciX device to use (default 0, i.e. hci0).",
    )


# EOF add_cmd_line_arguments


def parse_command_line(defaults_dict):
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="BLE Gateway - sends advertised packets to a database"
    )
    define_cmd_line_arguments(parser, defaults_dict)
    try:
        _opts = parser.parse_args()
    except Exception as e:
        parser.error("Error: " + str(e))
        sys.exit(1)
    return _opts


def main():

    # Create configuration object with default configuration parameters
    config = config_management.Configuration()

    # Parse command line arguments
    _opts = parse_command_line(config.get_config_dict())

    # Read config file and
    # merge command line arguments into current configuration
    config.load_configfile(_opts.configfile)

    # Command line parameters override defaults and configuration file
    _opts = parse_command_line(config.get_config_dict())
    config.update_config({defs.C_SEC_COMMON: vars(_opts)}, True)

    if _opts.writeconfig:
        config.write_configfile(_opts.writeconfig)
        return 0

    config.print()

    if config.SCANMODE:
        config.SEEN_MACS = {}
        print("--------- Running in SCAN mode ------------:")
        run_ble.run_ble(config)
        print("--------- Collected macs ------------:")
        for seen in config.SEEN_MACS.keys():
            print(seen, config.SEEN_MACS[seen])
    else:
        print("--------- Running in GATEWAY mode ------------:")
        config.Q = Queue()
        _p = Process(target=run_writers.run_writers, args=(config,))
        _p.start()
        run_ble.run_ble(config)
        _p.join()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
