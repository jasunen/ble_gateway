import asyncio
import datetime
from timeit import default_timer as timer

import aioblescan as aiobs
from aioblescan.plugins import EddyStone

from ble_gateway import decode


def is_mac_in_list(mac_str, macs):
    if macs:
        if mac_str in macs:
            return True
        return False
    else:
        return False


def add_packet_info(mesg, ev):
    # Add additional packet info
    for key in ["rssi", "peer", "tx_power"]:
        info = ev.retrieve(key)
        if info and not mesg.get(key, None):
            if key == "peer":
                key = "mac"
            mesg[key] = info[-1].val


# Define and run ble scanner asyncio loop
def run_ble(_config, _q):

    # TIMING
    _config["TIMER_SEC"] = 0.0
    _config["TIMER_COUNT"] = 0
    # ------------------------------

    allowed_macs = _config["allowmac"]
    source_macs = _config.get("sources", None)
    default_mac_config = source_macs.get("default", None)

    # Callback process to handle data received from BLE
    # ---------------------------------------------------
    def callback_data_handler(data):
        # data = byte array of raw data received

        # TIMING
        start_t = timer()
        # ------------------------------

        ev = aiobs.HCI_Event()
        ev.decode(data)

        # mac = list of mac addresses of the Packet (should be only one..),
        # object type aioblescan.MACaddr
        mac = ev.retrieve("peer")
        if not mac:
            return
        mac_str = mac[-1].val

        if allowed_macs and not is_mac_in_list(mac_str, allowed_macs):
            return

        # Are we in SCAN mode or normal gateway mode
        if _config["scan"]:
            # Do the scan mode stuff
            mesg = decode.run_decoders(_config["decode"], ev)

            if mesg or not _config["decode"]:
                # Add extra info if decoding ok or we do not want decoding
                if not mesg:
                    mesg = {}
                    mesg["decoder"] = "Unknown"
                add_packet_info(mesg, ev)
                if not is_mac_in_list(mac, _config["seen_macs"].keys()):
                    _config["seen_macs"][mesg["mac"]] = mesg["decoder"]
                print(datetime.now(), mac_str, mesg)
        else:
            # Do the gateway stuff
            # Get instructions what to do with the mac
            mac_config = source_macs.get(mac_str, None)
            mac_config = {**default_mac_config, **mac_config}
            if not mac_config:
                print("Don't know what to do with", mac_str)
                return

            mesg = decode.run_decoders(mac_config["decoder"], ev)
            if mesg:
                add_packet_info(mesg, ev)

            # Add message to queue
            _q.put(mesg)

        if _config["showraw"]:
            print("{} - Raw data: {}".format(mac[-1].val, ev.raw_data))

        # TIMING
        _config["TIMER_SEC"] += timer() - start_t
        _config["TIMER_COUNT"] += 1
        # ------------------------------

    # ---------------------------------------------------
    # EOF callback_data_handler

    event_loop = asyncio.get_event_loop()

    # First create and configure a raw socket
    mysocket = aiobs.create_bt_socket(_config["device"])

    # create a connection with the socket
    fac = event_loop._create_connection_transport(
        mysocket, aiobs.BLEScanRequester, None, None
    )

    # Start it
    conn, btctrl = event_loop.run_until_complete(fac)

    # Attach your processing (callback)
    btctrl.process = callback_data_handler

    # We can also send advertisements if needed
    if _config["advertise"]:
        command = aiobs.HCI_Cmd_LE_Advertise(enable=False)
        btctrl.send_command(command)
        command = aiobs.HCI_Cmd_LE_Set_Advertised_Params(
            interval_min=_config["advertise"], interval_max=_config["advertise"]
        )
        btctrl.send_command(command)
        if _config["url"]:
            myeddy = EddyStone(param=_config["url"])
        else:
            myeddy = EddyStone()
        if _config["txpower"]:
            myeddy.power = _config["txpower"]
        command = aiobs.HCI_Cmd_LE_Set_Advertised_Msg(msg=myeddy)
        btctrl.send_command(command)
        command = aiobs.HCI_Cmd_LE_Advertise(enable=True)
        btctrl.send_command(command)

    # Start BLE probe
    btctrl.send_scan_request()
    try:
        # event_loop.run_until_complete(coro)
        event_loop.run_forever()
    except KeyboardInterrupt:
        print("\n\n\nKeyboard interrupt!")
    finally:
        print("Closing event loop.")
        btctrl.stop_scan_request()
        command = aiobs.HCI_Cmd_LE_Advertise(enable=False)
        btctrl.send_command(command)
        conn.close()
        event_loop.close()

        # TIMING
        print(_config["TIMER_COUNT"], "calls.")
        print(
            1000 * 1000 * _config["TIMER_SEC"] / _config["TIMER_COUNT"],
            "usec in average per call.",
        )
        # ------------------------------

        return 0


# Run "writers" which take care of forwarding BLE messages to
# destinations defined in the configuration
def run_writers(_config, _q):
    pass
