import queue

from ble_gateway import defs, helpers, writers

# from pprint import pprint


# Run_writers takes care of forwarding BLE messages to
# destinations defined in the configuration
def run_writers(config, writers_q):
    # Instanciate all destination objects with proper configuration
    # pprint(vars(config))
    SOURCES = list(config.SOURCES.keys())
    unknown_mac_config = config.SOURCES.get("*", {})
    destinations = writers.Writers()
    destinations.add_writers(config.DESTINATIONS)
    destinations.setup_routing(config.SOURCES)
    waitlist = writers.IntervalChecker(config.SOURCES)

    # Loop reading Queue and processing messages
    print("Starting run_writers loop.")
    my_timer = helpers.StopWatch()
    while True:
        try:
            mesg = writers_q.get_nowait()
        except queue.Empty:
            mesg = None

        if mesg and "mac" in mesg:  # got valid message, let's process it
            # print("Got message from", mesg["mac"])
            _now = my_timer.start()

            # When packet is received, check if associated mac has configuration
            # defined.
            mac = mesg["mac"]
            mconfig = {}
            if mac in SOURCES:
                mconfig = config.SOURCES[mac]
            elif unknown_mac_config:
                mconfig = unknown_mac_config

            # Check interval and discard if last sent time less than interval
            if waitlist.is_wait_over(mac, now=_now):
                # modify the packet as defined in configuration
                mesg["timestamp"] = _now  # timestamp the message
                mesg = writers.Writer().modify_packet(mesg, mconfig)

                # *** send modified packet to destinations object
                # print("{} - let's write {}".format(time.ctime(wait_start), mesg))
                destinations.send(mesg)

                # Finally delete message as not needed
                del mesg

            my_timer.split()

        # No valid message to process, let's do other stuff
        if mesg == defs.STOPMESSAGE:
            print("STOP message received in writers_process.")
            break

    # Breaking out of the loop
    # Clean-up, close handels and files if any and return
    print("Exiting run_writers loop!")
    print("{} valid messages received.".format(my_timer.get_count()))
    print(
        "Average time for writing a message was {} usecs.".format(
            my_timer.get_average() * 1000 * 1000
        )
    )
    print(
        "Max time for writing a message was {} usecs.".format(
            my_timer.MAX_SPLIT * 1000 * 1000
        )
    )
    destinations.close()
    return
