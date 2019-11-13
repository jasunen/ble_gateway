import random
import time

from ble_gateway import decode, helpers


def random_mac():
    return "%02x:%02x:%02x:%02x:%02x:%02x" % (
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255),
    )


def run_simulator(config):
    simulated_macs = []
    for mac in list(config.SOURCES.keys()):
        if helpers.check_and_format_mac(mac):
            simulated_macs.append(mac)
    for i in range(2):
        simulated_macs.append(random_mac())
    simulated_decoders = list(decode.Decoder.all_decoders)

    print("Entering ble_simulator loop.")
    try:
        while True:
            # Do simulator stuff
            mesg = {}
            mesg['mac'] = random.choice(simulated_macs)
            mesg['decoder'] = random.choice(simulated_decoders)
            config.Q.put(mesg)
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\n\nKeyboard interrupt!")
    finally:
        print("Closing simulator.")
