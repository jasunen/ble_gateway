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
    while not config.QUIT_BLE_EVENT.is_set():
        # Do simulator stuff
        mesg = {}
        mesg["mac"] = random.choice(simulated_macs)
        mesg["decoder"] = random.choice(simulated_decoders)
        mesg["simutemp"] = round(random.randint(0, 400) / 10 - 20, 2)
        mesg["simuhumid"] = round(random.randint(0, 200) / 10 + 20, 2)
        config.Q.put(mesg)
        time.sleep(0.2)

    print("Closing simulator.")
