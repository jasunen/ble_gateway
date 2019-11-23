import aioblescan as aiobs
from aioblescan.plugins import BlueMaestro, EddyStone

from ble_gateway import helpers
from ble_gateway.ruuvitagraw import RuuviTagRaw
from ble_gateway.ruuvitagurl import RuuviTagUrl


def packet_info(ev):
    # Get basic packet info
    mesg = {}
    for key in ["rssi", "peer", "tx_power"]:
        info = ev.retrieve(key)
        if info:
            # ev.retrieve('peer') returns list of mac addresses of
            # the Packet (should be only one..)
            # peer object type is aioblescan.MACaddr
            if key == "peer":  # We use key 'mac' instead of 'peer', so rename
                key = "mac"
            mesg[key] = helpers._lowercase_all(info[-1].val)
    return mesg


class Decoder:
    all_decoders = {
        "pebble": BlueMaestro().decode,
        "ruuviraw": RuuviTagRaw().decode,
        "ruuviurl": RuuviTagUrl().decode,
        "eddy": EddyStone().decode,
    }

    def __init__(self):
        self.use_fixed_decoders = False
        self.fixed_decoders = []
        self.mac_decoders = {}

    def enable_fixed_decoders(self, decoders=[]):
        # if enabled, uses fixed decoders-list
        self.use_fixed_decoders = True
        print("Setting fixed_decoders = {}".format(decoders))
        if "all" in decoders:
            self.fixed_decoders = list(self.all_decoders.keys())
        else:
            self.fixed_decoders = decoders

    def enable_per_mac_decoders(self, sources=[]):
        # Enable per mac decoders as defined in sources configuration
        self.use_fixed_decoders = False
        print("Setting per_mac_decoders = {}".format(sources))
        for mac, mac_config in sources.items():
            _d = mac_config.get("decoders", [])
            if "all" in _d:
                self.mac_decoders[mac] = list(self.all_decoders.keys())
            else:
                self.mac_decoders[mac] = _d

    def get_decoders(self, mac):
        if self.use_fixed_decoders:
            return self.fixed_decoders
        else:
            if mac in self.mac_decoders:
                return self.mac_decoders.get(mac)
            else:
                return self.mac_decoders.get("*", None)

    def run(self, data, simulator=0):
        if simulator > 0:
            # data is from BLE simulator, just return the data
            return data

        base_mesg = {"decoder": "none"}
        ev = aiobs.HCI_Event()
        ev.decode(data)
        mesg = packet_info(ev)
        if "mac" not in mesg:  # invalid packet if no mac (peer) address
            return base_mesg

        decoders = self.get_decoders(mesg["mac"])
        if not decoders:
            return base_mesg

        # Try actually decode the message
        for decoder in decoders:
            func = self.all_decoders.get(decoder, None)
            if func:
                mesg = func(ev)
            if mesg:
                mesg["decoder"] = decoder
                return {**base_mesg, **mesg}

        return base_mesg
