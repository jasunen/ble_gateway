import time
from multiprocessing import Queue

from ble_gateway import writers


# Run "writers" which take care of forwarding BLE messages to
# destinations defined in the configuration
def run_writers(config):
    # Instanciate all destination objects with proper configuration
    destinations = writers.Writers()
    destinations.add_writers(config.DESTINATIONS)

    # Loop reading Queue and processing messages
    max_wait = config.find_by_key("no_messages_timeout", 60)
    while True:
        try:
            mesg = config.Q.get(True, max_wait)
        except Queue.Empty:
            # Queue has been empty longer than max_wait
            # We'll break out from the loop, do clenup and return
            break

        # got message, let's process it
        timestamp = int(time.time() * 1000)  # timestamp in milliseconds
        print(timestamp, " - let's write", mesg)
        # When packet is received,
        # *** do per source modifications:
        # 1. Remove fields
        # 2. Rename fields
        # 3. Add fields
        # 4. Order fields
        # writers.Writer().remove_fields(mesg, fields_remove)
        # *** send packet to destinations

    # Breaking out of the loop
    # Clean-up, close handels and files if any and return
    return
