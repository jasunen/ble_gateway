# Setup logging
import logging

import aioblescan as aiobs
from aioblescan.plugins import BlueMaestro, EddyStone

from ble_gateway import helpers
from ble_gateway.ruuvitagraw import RuuviTagRaw
from ble_gateway.ruuvitagurl import RuuviTagUrl

logger = logging.getLogger(__name__)


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
        self.ev = aiobs.HCI_Event()

    def enable_fixed_decoders(self, decoders=[]):
        # if enabled, uses fixed decoders-list
        self.use_fixed_decoders = True
        logger.info("Setting fixed_decoders = {}".format(decoders))
        if "all" in decoders:
            self.fixed_decoders = list(self.all_decoders.keys())
        else:
            self.fixed_decoders = decoders

    def enable_per_mac_decoders(self, sources=[]):
        # Enable per mac decoders as defined in sources configuration
        self.use_fixed_decoders = False
        logger.info("Setting per_mac_decoders = {}".format(sources))
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
                return self.mac_decoders.get(mac, [])
            else:
                return self.mac_decoders.get("*", [])

    def run1(self, data):
        base_mesg = {"decoder": "none"}
        self.ev.__init__()
        self.ev.decode(data)
        mesg = packet_info(self.ev)
        return {**base_mesg, **mesg}

    def run2(self, data, base_mesg):
        decoders = self.get_decoders(base_mesg["mac"])

        # Try actually decode the message
        mesg = {}
        for decoder in decoders:
            func = self.all_decoders.get(decoder, None)
            if func:
                mesg = func(self.ev)
            if mesg:
                mesg["decoder"] = decoder
                return {**base_mesg, **mesg}

        return base_mesg
