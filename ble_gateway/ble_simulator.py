import random
from time import sleep

from ble_gateway import decode


def random_mac():
    return "%02x:%02x:%02x:%02x:%02x:%02x" % (
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255),
    )


def run_simulator(config, QUIT_BLE_EVENT, decoder_q):
    for i in range(2):
        config.SIMUMACS.append(random_mac())
    simulated_decoders = list(decode.Decoder.all_decoders)

    print("Entering ble_simulator loop.")
    print("Sim macs:", config.SIMUMACS)
    print("Sim decoders:", simulated_decoders)
    packetcount = 0
    while not QUIT_BLE_EVENT.is_set() and packetcount < config.SIMULATOR:
        # Do simulator stuff
        mesg = {}
        mesg["mac"] = random.choice(config.SIMUMACS)
        mesg["decoder"] = random.choice(simulated_decoders)
        mesg["simutemp"] = round(random.randint(0, 400) / 10 - 20, 2)
        mesg["simuhumid"] = round(random.randint(0, 200) / 10 + 20, 2)
        mesg["_simulated_data_"] = random.randint(0, 100)
        decoder_q.put(mesg)
        sleep(random.randint(5, 50) / 100)
        packetcount += 1

    print("Closing simulator.")
