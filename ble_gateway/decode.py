from aioblescan.plugins import BlueMaestro, EddyStone

from ble_gateway.ruuvitagraw import RuuviTagRaw
from ble_gateway.ruuvitagurl import RuuviTagUrl


def run_decoders(_d, ev):
    if not _d:
        return None

    all_decoders = {
        "pebble": BlueMaestro().decode,
        "ruuviraw": RuuviTagRaw().decode,
        "ruuviurl": RuuviTagUrl().decode,
        "eddy": EddyStone().decode,
    }

    decoders = []
    if "all" in _d:
        decoders = list(all_decoders.keys())
    else:
        for decoder in _d:
            if decoder in all_decoders:
                decoders.append(decoder)
    if "unknown" in _d:
        decoders.append("unknown")

    # Try to identify the message
    xx = {}
    for decoder in decoders:
        if decoder == "unknown":
            return {"decoder": "unknown"}
        func = all_decoders.get(decoder, None)
        if func:
            xx = func(ev)
        if xx:
            xx["decoder"] = decoder
            return xx

    return None
