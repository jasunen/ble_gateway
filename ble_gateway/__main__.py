#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os
import re
import sys

import yaml
from benedict import benedict

from ble_gateway import ble_gateway


# Parse command line arguments
def parse_cmd_line_arguments(parser):
    def check_mac(val):
        try:
            if re.match(
                "[0-9a-f]{2}([-:])[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", val.lower()
            ):
                return val.lower()
        except Exception as e:
            print("Error: " + str(e))
        raise argparse.ArgumentTypeError("%s is not a MAC address" % val)

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
        metavar="FILE",
        default="",
        help="Write configuration to FILE or \
        - to print out configuration and exit.",
    )
    parser.add_argument(
        "-m",
        "--allowmac",
        type=check_mac,
        action="append",
        help="Filter and process these MAC addresses only. \
        Can be combined with --scan to look for specific mac(s).",
    )
    parser.add_argument(
        "-S",
        "--scan",
        action="store_true",
        default=False,
        help="Start in Scan mode. Listen for broadcasts and \
        collect mac addresses. \
        Disables forwarding of messages to any destination (writers). \
        Without --decode option tries not to identify message type. \
        ",
    )
    parser.add_argument(
        "--decode",
        metavar="DECODER",
        action="append",
        choices=["all", "ruuviraw", "ruuviurl", "eddy", "pebble"],
        help="Optional. Decoders to enable in Scan mode. \
        Has no effect if --scan not enabled. \
        'all' will try all decoders. If any decoders enabled \
        will only return macs with successfull decode. \
        ",
    )
    parser.add_argument(
        "-r",
        "--showraw",
        action="store_true",
        default=False,
        help="Show raw data for each received packet regardless of mode running.",
    )
    parser.add_argument(
        "-a",
        "--advertise",
        type=int,
        default=0,
        help="Broadcast like an EddyStone Beacon. \
        Set the interval between packet in millisec",
    )
    parser.add_argument(
        "-u",
        "--url",
        type=str,
        default="",
        help="When broadcasting like an EddyStone Beacon, set the url.",
    )
    parser.add_argument(
        "-t",
        "--txpower",
        type=int,
        default=0,
        help="When broadcasting like an EddyStone Beacon, set the Tx power",
    )
    parser.add_argument(
        "-D",
        "--device",
        type=int,
        default=0,
        help="Select the hciX device to use (default 0, i.e. hci0).",
    )


# EOF parse_cmd_line_arguments


def load_configfile(file, _config):
    # If file exists, returns the content (MUST BE YAML) as dict
    # and updates _config
    if file == "-":
        return {}
    if os.path.isfile(file):
        with open(file) as f:
            print("Reading configfile:", file)
            _read = yaml.load(f, Loader=yaml.FullLoader)
        _config.update(_read)
        return _read
    else:
        print("No configfile found:", file)
        return {}  # empty dict if file not found


def write_configfile(file, _config):
    print("Writing configfile:", file)
    _out = {}
    _out.update(_config)
    if file == "-":
        print(yaml.dump(_out))
    else:
        with open(file, "w") as f:
            yaml.dump(_out, f)


def main():
    # set default configuration parameters
    _config = benedict(keypath_separator=None)

    # parse command line arguments
    parser = argparse.ArgumentParser(
        description="BLE Gateway - sends advertised packets to a database"
    )
    parse_cmd_line_arguments(parser)
    try:
        _opts = parser.parse_args()
    except Exception as e:
        parser.error("Error: " + str(e))
        sys.exit()

    load_configfile(_opts.configfile, _config)

    # merge command line arguments into final configuration
    _config.update(vars(_opts))

    if _opts.writeconfig:
        write_configfile(_opts.writeconfig, _config)
        return 0

    print(_config)

    if _config["scan"]:
        _config['seen_macs'] = {}

    ble_gateway.run_ble(_config)

    if _config["scan"]:
        print("--------- Collected macs ------------:")
    for seen in _config['seen_macs'].keys():
        print(seen, _config['seen_macs'][seen])


if __name__ == "__main__":
    main()
