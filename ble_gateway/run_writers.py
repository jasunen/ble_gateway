import time
from multiprocessing import Queue


# Run "writers" which take care of forwarding BLE messages to
# destinations defined in the configuration
def run_writers(_config, _q):
    # Instanciate all destination objects with proper configuration

    while True:
        try:
            mesg = _q.get(True, _config["no_messages_timeout"])
        except Queue.Empty:
            # Queue has been empty longer than "no_message_timeout"
            # We'll break out from the loop, do clenup and return
            break

        # got message, let's process it
        timestamp = int(time.time() * 1000)  # timestamp in milliseconds
        print(timestamp, " - let's write", mesg)

    # Breaking out of the loop
    # Clean-up, close handels and files if any and return
    return
