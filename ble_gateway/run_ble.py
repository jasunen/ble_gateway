import asyncio
import time
from timeit import default_timer as timer

import aioblescan as aiobs
from aioblescan.plugins import EddyStone

from ble_gateway import decode, defs, helpers


def x_is_mac_in_list(mac_str, macs):
    if macs:
        if mac_str in macs:
            return True
        return False
    else:
        return False


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


# Define and run ble scanner asyncio loop
def run_ble(config):

    # TIMING
    config.TIMER_SEC = 0.0
    config.TIMER_COUNT = 0
    # ------------------------------

    decoder = decode.Decoder()
    if config.MODE == defs.SCANMODE:
        decoder.enable_fixed_decoders(config.DECODE)
    else:
        decoder.enable_per_mac_decoders(config.SOURCES)

    # Callback process to handle data received from BLE
    # ---------------------------------------------------
    def callback_data_handler(data):
        # data = byte array of raw data received

        # TIMING
        start_t = timer()
        # ------------------------------

        ev = aiobs.HCI_Event()
        ev.decode(data)

        mesg = packet_info(ev)
        if "mac" not in mesg:  # invalid packet if no mac (peer) address
            return

        if not config.allowed_mac(mesg["mac"]):
            return

        mesg.update(decoder.run(mesg["mac"], ev))

        # Add message to queue
        config.Q.put(mesg)

        if config.SHOWRAW:
            print("{} - Raw data: {}".format(mesg["mac"], ev.raw_data))

        # TIMING
        config.TIMER_SEC += timer() - start_t
        config.TIMER_COUNT += 1
        # ------------------------------

    # ---------------------------------------------------
    # EOF callback_data_handler

    if config.find_by_key("simulator", False):
        # Run BLE simulator instead of real hardware
        from ble_gateway import ble_simulator

        ble_simulator.run_simulator(config)

    else:
        hci_dev = config.find_by_key("device", None)
        if hci_dev is None:
            print("No device specified, exiting run_ble")
            return 1

        event_loop = asyncio.get_event_loop()

        # First create and configure a raw socket
        mysocket = aiobs.create_bt_socket(hci_dev)

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
            event_loop.run_forever()
        except KeyboardInterrupt:
            print("\n\n\nKeyboard interrupt!")
        finally:
            print("Closing ble event loop.")
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

    config.Q.put(config.STOPMESSAGE)
    time.sleep(5)
    print("Exiting run_ble.")
    return 0
    # EOF run_ble
