import asyncio

import aioblescan as aiobs
from aioblescan.plugins import EddyStone

from ble_gateway.ruuvitagraw import RuuviTagRaw


# Define and run ble scanner asyncio loop
def run_ble(_config):

    # Callback process to handle data received from BLE
    # ---------------------------------------------------
    def callback_data_handler(data):

        ev = aiobs.HCI_Event()
        mac = ev.retrieve("peer")
        xx = ev.decode(data)
        print("\nmac: " + mac + "\nxx: " + xx)
        xx = RuuviTagRaw().decode(ev)
        if xx:
            print("RuuviTag data {}".format(xx))

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
