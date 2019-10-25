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
        "-C",
        "--configfile",
        type=str,
        default=os.path.join(os.path.dirname(__file__), "ble_gateway.config.yaml"),
        help="Configuration file to use. Default is ble_gateway.cofig.yaml in the module's directory",
    )
    parser.add_argument(
        "-e",
        "--eddy",
        action="store_true",
        default=False,
        help="Look specificaly for Eddystone messages.",
    )
    parser.add_argument(
        "-m",
        "--mac",
        type=check_mac,
        action="append",
        help="Look for these MAC addresses.",
    )
    parser.add_argument(
        "-r",
        "--ruuvi",
        action="store_true",
        default=False,
        help="Look only for Ruuvi tag Weather station messages",
    )
    parser.add_argument(
        "-p",
        "--pebble",
        action="store_true",
        default=False,
        help="Look only for Pebble Environment Monitor",
    )
    parser.add_argument(
        "-R",
        "--raw",
        action="store_true",
        default=False,
        help="Also show the raw data.",
    )
    parser.add_argument(
        "-a",
        "--advertise",
        type=int,
        default=0,
        help="Broadcast like an EddyStone Beacon. Set the interval between packet in millisec",
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
    parser.add_argument(
        "--write_config_to",
        type=str,
        metavar="FILE",
        default="",
        help="Write configuration to FILE or - to STDOUT",
    )


# EOF parse_cmd_line_arguments


def load_configfile(file, _config):
    # If file exists, returns the content (MUST BE YAML) as dict
    # and updates _config
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
        description="Gateway BLE advertised packets to database"
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

    if _opts.write_config_to:
        write_configfile(_opts.write_config_to, _config)

    print(_config)

    ble_gateway.run_ble(_config)


if __name__ == "__main__":
    main()
