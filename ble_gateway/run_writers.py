import time
import queue
from pprint import pprint

from ble_gateway import writers


def modify_packet(mesg, mconfig):
    # *** do per source modifications:
    # 1. Remove fields
    mesg = writers.Writer().remove_fields(mesg, mconfig.get("fields_remove", []))
    # 2. Rename fields
    mesg = writers.Writer().rename_fields(mesg, mconfig.get("fields_rename", []))
    # 3. Add fields
    mesg = writers.Writer().add_fields(mesg, mconfig.get("fields_add", []))
    # 4. Order fields
    mesg = writers.Writer().order_fields(mesg, mconfig.get("fields_order", []))

    return mesg


# Run "writers" which take care of forwarding BLE messages to
# destinations defined in the configuration
def run_writers(config):
    # Instanciate all destination objects with proper configuration
    pprint(vars(config))
    SOURCES = list(config.SOURCES.keys())
    unknown_mac_config = config.SOURCES.get("*", {})
    destinations = writers.Writers(config.SOURCES)
    destinations.add_writers(config.DESTINATIONS)
    waitlist = writers.IntervalChecker()

    # Loop reading Queue and processing messages
    # If Queue has been empty longer than wait_max seconds
    # we'll break out from the loop, do clenup and return
    wait_max = config.find_by_key("no_messages_timeout", 10)
    wait_start = int(time.time())
    print("Starting run_writers loop.")
    while wait_max > (int(time.time()) - wait_start):
        try:
            mesg = config.Q.get_nowait()
        except queue.Empty:
            mesg = None

        if mesg:  # got message, let's process it
            print("Got message from", mesg['mac'])
            wait_start = time.time()  # Reset wait timer
            timestamp = int(wait_start * 1000)  # timestamp in milliseconds
            wait_start = int(wait_start)

            # When packet is received, check if associated mac has configuration
            # defined.
            mac = mesg["mac"]
            mconfig = {}
            if mac in SOURCES:
                mconfig = config.SOURCES[mac]
            elif unknown_mac_config:
                mconfig = unknown_mac_config

            interval = int(mconfig.get("interval", 0))
            # Check interval and discard if last sent time less than interval
            if waitlist.is_wait_over(mac, interval, wait_start):
                # modify the packet as defined in configuration
                print(timestamp, " - let's write", mesg)
                mesg["timestamp"] = timestamp
                mesg = modify_packet(mesg, mconfig)

                # *** send modified packet to destinations object
                destinations.send(mesg)

        else:  # No message to process, let's do other stuff
            pass

    # Breaking out of the loop
    # Clean-up, close handels and files if any and return
    print("Exiting run_writers loop.")
    return
