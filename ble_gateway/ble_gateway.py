import asyncio

import aioblescan as aiobs
from aioblescan.plugins import EddyStone

from ble_gateway import ruuvitagraw


# Define and run ble scanner asyncio loop
def run_ble(_config):

    # Process to handle data received from BLE
    def callback_data_handler(data):

        ev = aiobs.HCI_Event()
        xx = ev.decode(data)
        #        print("Raw data: {}".format(ev.raw_data))
        xx = ruuvitagraw().decode(ev)
        if xx:
            print("Weather info {}".format(xx))

    #        else:
    #            ev.show(0)

    # EOF callback_data_handler

    event_loop = asyncio.get_event_loop()

    # First create and configure a raw socket
    mysocket = aiobs.create_bt_socket(_config["device"])

    # create a connection with the raw socket
    # This used to work but now requires a STREAM socket.
    # fac=event_loop.create_connection(aiobs.BLEScanRequester,sock=mysocket)
    # Thanks to martensjacobs for this fix
    fac = event_loop._create_connection_transport(
        mysocket, aiobs.BLEScanRequester, None, None
    )
    # Start it
    conn, btctrl = event_loop.run_until_complete(fac)
    # Attach your processing
    btctrl.process = callback_data_handler

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

    # Probe
    btctrl.send_scan_request()
    try:
        # event_loop.run_until_complete(coro)
        event_loop.run_forever()
    except KeyboardInterrupt:
        print("keyboard interrupt")
    finally:
        print("closing event loop")
        btctrl.stop_scan_request()
        command = aiobs.HCI_Cmd_LE_Advertise(enable=False)
        btctrl.send_command(command)
        conn.close()
        event_loop.close()
        return 0
