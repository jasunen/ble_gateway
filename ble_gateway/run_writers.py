import queue
import time
from pprint import pprint

from ble_gateway import writers


# Run "writers" which take care of forwarding BLE messages to
# destinations defined in the configuration
def run_writers(config):
    # Instanciate all destination objects with proper configuration
    # pprint(vars(config))
    SOURCES = list(config.SOURCES.keys())
    unknown_mac_config = config.SOURCES.get("*", {})
    destinations = writers.Writers()
    destinations.add_writers(config.DESTINATIONS)
    destinations.setup_routing(config.SOURCES)
    waitlist = writers.IntervalChecker(config.SOURCES)

    # Loop reading Queue and processing messages
    # If Queue has been empty longer than wait_max seconds
    # we'll break out from the loop, do clenup and return
    wait_max = config.find_by_key("no_messages_timeout", 10)
    wait_start = time.time()
    print("Starting run_writers loop.")
    packet_counter = 0
    while True:
        try:
            mesg = config.Q.get_nowait()
        except queue.Empty:
            mesg = None

        if wait_max < (time.time() - wait_start):
            print("Time out in runwriter, no messages for", wait_max, "seconds.")
            break

        if mesg:  # got message, let's process it
            if mesg == config.STOPMESSAGE:
                print("STOP message received in run_writers.")
                break

            # print("Got message from", mesg["mac"])
            wait_start = time.time()  # Reset wait timer

            # When packet is received, check if associated mac has configuration
            # defined.
            mac = mesg["mac"]
            mconfig = {}
            if mac in SOURCES:
                mconfig = config.SOURCES[mac]
            elif unknown_mac_config:
                mconfig = unknown_mac_config

            # Check interval and discard if last sent time less than interval
            if waitlist.is_wait_over(mac, now=wait_start):
                # modify the packet as defined in configuration
                mesg["timestamp"] = wait_start  # timestamp the message
                mesg = writers.Writer().modify_packet(mesg, mconfig)

                # *** send modified packet to destinations object
                # print("{} - let's write {}".format(time.ctime(wait_start), mesg))
                packet_counter += 1
                destinations.send(mesg)

                # Finally delete message as not needed
                del mesg
        else:  # No message to process, let's do other stuff
            pass

    # Breaking out of the loop
    # Clean-up, close handels and files if any and return
    print("Exiting run_writers loop!")
    destinations.close()
    config.quit_event.set()
    return
