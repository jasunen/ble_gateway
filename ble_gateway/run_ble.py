import asyncio
import datetime
from timeit import default_timer as timer

import aioblescan as aiobs
from aioblescan.plugins import EddyStone

from ble_gateway import decode, helpers


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
        # We use name 'mac' instead of 'peer'
        if key == "peer":
            key = "mac"
        if info and not mesg.get(key, None):
            mesg[key] = helpers._lowercase(info[-1].val)


# Define and run ble scanner asyncio loop
def run_ble(config):

    # TIMING
    config.TIMER_SEC = 0.0
    config.TIMER_COUNT = 0
    # ------------------------------

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

        if config.ALLOWED_MACS and not is_mac_in_list(mac_str, config.ALLOWED_MACS):
            return

        # Are we in SCAN mode or normal gateway mode
        if config.SCANMODE:
            # Do the scan mode stuff
            mesg = decode.run_decoders(config.DECODE, ev)

            if mesg or not config.DECODE:
                # Add extra info if decoding ok or we do not want decoding
                if not mesg:
                    mesg = {}
                    mesg["decoder"] = "unknown"
                add_packet_info(mesg, ev)
                if not is_mac_in_list(mac, config.SEEN_MACS.keys()):
                    config.SEEN_MACS[mesg["mac"]] = mesg["decoder"]
                print(datetime.now(), mac_str, mesg)
        else:
            # Do the gateway stuff
            # Get instructions what to do with the mac
            mac_config = config.SOURCE_MACS.get(mac_str, None)
            if not mac_config:
                print("Don't know what to do with", mac_str)
                return

            mesg = decode.run_decoders(mac_config["decoder"], ev)
            if mesg:
                add_packet_info(mesg, ev)
                # Add message to queue
                config.Q.put(mesg)
            else:
                print(mac_str, "was regocnized but not able to decode!!")

        if config.SHOWRAW:
            print("{} - Raw data: {}".format(mac[-1].val, ev.raw_data))

        # TIMING
        config.TIMER_SEC += timer() - start_t
        config.TIMER_COUNT += 1
        # ------------------------------

    # ---------------------------------------------------
    # EOF callback_data_handler

    event_loop = asyncio.get_event_loop()

    # First create and configure a raw socket
    mysocket = aiobs.create_bt_socket(config.find_by_key("device", None))

    # create a connection with the socket
    fac = event_loop._create_connection_transport(
        mysocket, aiobs.BLEScanRequester, None, None
    )

    # Start it
    conn, btctrl = event_loop.run_until_complete(fac)

    # Attach your processing (callback)
    btctrl.process = callback_data_handler

    # We can also send advertisements if needed
    if config.find_by_key("advertise", None):
        command = aiobs.HCI_Cmd_LE_Advertise(enable=False)
        btctrl.send_command(command)
        command = aiobs.HCI_Cmd_LE_Set_Advertised_Params(
            interval_min=config.find_by_key("advertise", None),
            interval_max=config.find_by_key("advertise", None),
        )
        btctrl.send_command(command)
        if config.find_by_key("url", None):
            myeddy = EddyStone(param=config.find_by_key("url", None))
        else:
            myeddy = EddyStone()
        if config.find_by_key("txpower", None):
            myeddy.power = config.find_by_key("txpower", None)
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
        print(config.TIMER_COUNT, "calls.")
        print(
            1000 * 1000 * config.TIMER_SEC / config.TIMER_COUNT,
            "usec in average per call.",
        )
        # ------------------------------

        return 0
