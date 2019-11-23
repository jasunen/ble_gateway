#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os
import queue
import sys
from multiprocessing import Event, Process, Queue
from time import sleep

from ble_gateway import config_management, decode, defs, helpers, run_ble, run_writers


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
        "-G",
        "--gateway",
        action="store_const",
        const=defs.GWMODE,
        dest="mode",
        help="Start in Gateway mode. Forwards messages to destinations \
        (writers) specified in the configuration file. \
        ",
    )
    parser.add_argument(
        "-S",
        "--scan",
        action="store_const",
        const=defs.SCANMODE,
        dest="mode",
        help="Start in Scan mode. Listen to broadcasts and just \
        collect mac addresses. \
        Disables forwarding of messages to any destinations specified \
        in the configuration file \
        (other than built-in 'SCAN' destination). \
        With --decode option tries to identify and decode messages. \
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
    parser.add_argument(
        "--simulator",
        metavar="N",
        type=int,
        default=defaults_dict[defs.C_SEC_COMMON].get("simulator"),
        help="Use simulated messages instead of real bluetooth hardware.\
        Generate N messgaes and exit.",
    )
    parser.add_argument(
        "--max_mesgs",
        metavar="N",
        type=int,
        default=defaults_dict[defs.C_SEC_COMMON].get("max_mesgs"),
        help="Receive max N messgaes and exit.",
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

    # Create configuration object with built-in default configuration parameters
    config = config_management.Configuration()

    # Parse command line arguments first time just to get configfile
    args = parse_command_line(config.get_config_dict())
    # Read config file and merge to built-in defaults
    d = config.load_configfile(args.configfile)
    if d:
        config.update_config(d, True)

    # Command line parameters override defaults and configuration file
    # so we parse command line parameters again using configuration
    # from configfile as new defaults
    args = vars(parse_command_line(config.get_config_dict()))
    # removing options which are 'none'
    for arg in list(args.keys()):
        if not args[arg]:
            args.pop(arg)
    # merge command line arguments into current configuration's 'common' section
    config.update_config({defs.C_SEC_COMMON: args}, True)

    if "writeconfig" in args:
        config.write_configfile(args["writeconfig"])
        return 0

    config.print()

    # Setup communication channels for subprocesses
    decoder_q = Queue()
    writers_q = Queue()
    QUIT_BLE_EVENT = Event()

    # Setup writers subprocess
    writers_process = Process(target=run_writers.run_writers, args=(config, writers_q))

    # Setup BLE subprocess (either simulator or real hardware)
    if config.SIMULATOR:
        # Run BLE simulator instead of real hardware
        from ble_gateway import ble_simulator

        ble_process = Process(
            target=ble_simulator.run_simulator, args=(config, QUIT_BLE_EVENT, decoder_q)
        )
    else:
        # Setup real BLE process
        ble_process = Process(
            target=run_ble.run_ble, args=(config.DEVICE, QUIT_BLE_EVENT, decoder_q)
        )

    print("--------- Running in {} mode ------------".format(config.MODE))
    ble_process.start()
    writers_process.start()

    decoder = decode.Decoder()
    if config.MODE == defs.SCANMODE:
        decoder.enable_fixed_decoders(config.DECODE)
    else:
        decoder.enable_per_mac_decoders(config.SOURCES)

    # Main loop here -- implementing event/signal handler to break out of it??
    # If no messages received from BLE_process for >no_messgae_timeout seconds
    # we'll break out from the loop, do clenup and exit main loop
    my_timer = helpers.StopWatch(config.find_by_key("no_messages_timeout", 60))
    # MAIN LOOP START -----------------------------------------------------------
    while writers_process.is_alive() and ble_process.is_alive():
        # DECODE START ---------------------------------------------
        # Read decoder queue
        try:
            data = decoder_q.get_nowait()
        except queue.Empty:
            data = None
            if my_timer.is_timeout():
                print(
                    "Time out! No messages received from BLE for",
                    my_timer.get_timeout(),
                    "seconds.",
                )
                break

        if data:  # got data, let's decode it
            my_timer.start()  # Reset wait timer

            if data == defs.STOPMESSAGE:
                print("STOP message received from ble_process.")
                break
            mesg = decoder.run(data)
            if mesg and (not config.ALLOWED_MACS or mesg["mac"] in config.ALLOWED_MACS):
                # Send decoded message to writers
                writers_q.put(mesg)
                if config.SHOWRAW:
                    print("{} - Raw data: {}".format(mesg["mac"], data))

            my_timer.split()

            if config.MAX_MESGS and config.MAX_MESGS <= my_timer.get_count():
                print("Max message limit reached!")
                break

        # DECODE STOP ---------------------------------------------
    # MAIN LOOP STOP -----------------------------------------------------------

    # Stop subprocesses and cleanup
    print("Closing main.")
    print("{} messages received for decode.".format(my_timer.get_count()))
    print(
        "Average time for decoding a message was {} usecs.".format(
            my_timer.get_average() * 1000 * 1000
        )
    )
    print(
        "Max time for decoding a message was {} usecs.".format(
            my_timer.MAX_SPLIT * 1000 * 1000
        )
    )
    QUIT_BLE_EVENT.set()
    writers_q.put(defs.STOPMESSAGE)
    sleep(1)
    while not decoder_q.empty():
        decoder_q.get(block=True, timeout=0.05)
    while not writers_q.empty():
        writers_q.get(block=True, timeout=0.05)
    ble_process.join()
    writers_process.join()

    exit_code = config.SIMULATOR
    if config.MAX_MESGS:
        exit_code = config.MAX_MESGS
    return exit_code


if __name__ == "__main__":
    exit_code = main()
    while exit_code == 0:
        print("Restarting main() !!")
        exit_code = main()
    print("Exiting with code ({})".format(exit_code))
    sys.exit(exit_code)
