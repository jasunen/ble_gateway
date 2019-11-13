from aioblescan.plugins import BlueMaestro, EddyStone

from ble_gateway.ruuvitagraw import RuuviTagRaw
from ble_gateway.ruuvitagurl import RuuviTagUrl


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

    def enable_fixed_decoders(self, decoders=None):
        # if enabled, uses fixed decoders-list
        self.use_fixed_decoders = True
        if decoders is not None:
            self.fixed_decoders = decoders

    def enable_per_mac_decoders(self, sources=None):
        # Enable per mac decoders as defined in sources configuration
        self.use_fixed_decoders = False
        if sources is not None:
            for mac, mac_config in sources.items():
                _d = mac_config.get('decoders', [])
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
                return self.mac_decoders.get('*', None)

    def run(self, mac, ev):
        base_mesg = {'decoder': 'none'}
        decoders = self.get_decoders(mac)
        if not decoders:
            return base_mesg

        # Try actually decode the message
        mesg = {}
        for decoder in decoders:
            func = self.all_decoders.get(decoder, None)
            if func:
                mesg = func(ev)
            if mesg:
                mesg["decoder"] = decoder
                return {**base_mesg, **mesg}

        return base_mesg
