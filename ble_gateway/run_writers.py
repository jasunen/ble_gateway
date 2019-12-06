# Setup logging
import logging
import logging.handlers
from queue import Empty as QueueEmpty

from ble_gateway import defs, helpers, writers

logger = logging.getLogger(__name__)


# Run_writers takes care of forwarding BLE messages to
# destinations defined in the configuration
def run_writers(config, writers_q, log_q):
    # For multiprocess logging pass log_q to subprocess and
    # add following line to subprocess startup function
    logging.getLogger("").handlers = []
    logging.getLogger("").addHandler(logging.handlers.QueueHandler(log_q))

    # Instanciate all destination objects with proper configuration
    SOURCES = list(config.SOURCES.keys())
    unknown_mac_config = config.SOURCES.get("*", {})
    destinations = writers.Writers()
    destinations.add_writers(config.DESTINATIONS)
    destinations.setup_routing(config.SOURCES)
    waitlist = writers.IntervalChecker(config.SOURCES)

    # Loop reading Queue and processing messages
    logger.info("Starting run_writers loop.")
    my_timer = helpers.StopWatch()
    while True:
        try:
            mesg = writers_q.get_nowait()
        except QueueEmpty:
            mesg = None

        if mesg:  # got a message, let's process it
            # Checking for STOP message
            if mesg == defs.STOPMESSAGE:
                logger.info("STOP message received in writers_process.")
                break

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
                try:
                    destinations.send(mesg)
                except Exception:
                    # Let's catch any errors
                    logger.exception("Writers failing - exiting run_writers:")
                    break

            my_timer.split()

        # Message processed, let's do other stuff

    # Breaking out of the loop
    # Clean-up, close handels and files if any and return
    destinations.close()

    logger.info("Exiting run_writers loop!")
    logger.info("{} valid messages received.".format(my_timer.get_count()))
    logger.info(
        "Average time for writing a message was {:.4f} ms.".format(
            my_timer.get_average() * 1000
        )
    )
    logger.info(
        "Max time for writing a message was {:.4f} ms.".format(
            my_timer.MAX_SPLIT * 1000
        )
    )
    return
