import time
from multiprocessing import Queue

from ble_gateway import writers


def modify_packet(mesg, mconfig):
    # *** do per source modifications:
    # 1. Remove fields
    writers.Writer().remove_fields(mesg, mconfig.get("fields_remove"), [])
    # 2. Rename fields
    writers.Writer().rename_fields(mesg, mconfig.get("fields_rename"), [])
    # 3. Add fields
    writers.Writer().add_fields(mesg, mconfig.get("fields_add"), [])
    # 4. Order fields
    writers.Writer().add_fields(mesg, mconfig.get("fields_order"), [])


# Run "writers" which take care of forwarding BLE messages to
# destinations defined in the configuration
def run_writers(config):
    # Instanciate all destination objects with proper configuration
    destinations = writers.Writers()
    destinations.add_writers(config.DESTINATIONS)
    SOURCES = list(config.SOURCES.keys())
    unknown_mac_config = config.SOURCES.get("unknown", {})
    waitlist = writers.IntervalChecker()

    # Loop reading Queue and processing messages
    # If Queue has been empty longer than wait_max seconds
    # we'll break out from the loop, do clenup and return
    wait_max = config.find_by_key("no_messages_timeout", 10)
    wait_start = int(time.time())
    while wait_max > (int(time.time()) - wait_start):
        try:
            mesg = config.Q.get_nowait()
        except Queue.Empty:
            mesg = None

        if mesg:  # got message, let's process it
            wait_start = time.time()  # Reset wait timer
            timestamp = int(wait_start * 1000)  # timestamp in milliseconds
            wait_start = int(wait_start)

            # When packet is received, check if associated mac has configuration
            # defined.
            mac = mesg["mac"]
            mconfig = None
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
                modify_packet(mesg, mconfig)

                # *** send modified packet to destinations object
                destinations.send(mesg, mconfig)

        else:  # No message to process, let's do other stuff
            pass

    # Breaking out of the loop
    # Clean-up, close handels and files if any and return
    return
