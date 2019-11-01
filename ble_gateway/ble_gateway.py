import asyncio

import aioblescan as aiobs
from aioblescan.plugins import EddyStone
from ble_gateway import decode


def is_mac_in_list(mac, macs):
    if macs:
        for x in mac:
            if x.val in macs:
                return True
        return False
    else:
        return False


def add_packet_info(mesg, ev):
    # Add additional packet info
    for key in ['rssi', 'peer', 'tx_power']:
        info = ev.retrieve(key)
        if info and not mesg[key]:
            if key == 'peer':
                key = 'mac'
            mesg[key] = info[-1].val


# Define and run ble scanner asyncio loop
def run_ble(_config):

    # Callback process to handle data received from BLE
    # ---------------------------------------------------
    def callback_data_handler(data):
        # data = byte array of raw data received

        ev = aiobs.HCI_Event()
        ev.decode(data)

        # mac = list of mac addresses of the Packet (should be only one..),
        # object type aioblescan.MACaddr
        mac = ev.retrieve("peer")
        if _config['allowmac'] and not is_mac_in_list(mac, _config['allowmac']):
            return

        # Are we in SCAN mode or normal gateway mode
        if _config["scan"] and not is_mac_in_list(mac, _config['seen_macs'].keys()):
            # Do the scan mode stuff
            mesg = decode.run_decoders(_config['decode'], ev)

            if mesg or not _config['decode']:
                # Add extra info if decoding ok or we do not want decoding
                add_packet_info(mesg, ev)
                if not mesg:
                    mesg['decode'] = 'Unknown'
                _config['seen_macs'][mesg['mac']] = mesg['decode']
        else:
            # Do the gateway stuff
            # Add message to queue
            print("Gateway mode not yet implemented")

        if _config["showraw"]:
            print("Raw data: {}".format(ev.raw_data))

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
        return 0
