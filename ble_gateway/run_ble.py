import asyncio

import aioblescan as aiobs

from ble_gateway import helpers


# Define and run ble scanner asyncio loop
def run_ble(hci_dev, QUIT_BLE_EVENT, decoder_q):

    # TIMING
    my_timer = helpers.StopWatch()
    # ------------------------------

    event_loop = asyncio.get_event_loop()

    # Callback process to handle data received from BLE
    # ---------------------------------------------------
    def callback_data_handler(data):
        # data = byte array of raw data received

        # TIMING
        my_timer.start()
        # ------------------------------

        if QUIT_BLE_EVENT.is_set():
            event_loop.stop()
        else:
            # Add message to queue
            decoder_q.put(data)

        # TIMING
        my_timer.split()
        # ------------------------------

    # ---------------------------------------------------
    # EOF callback_data_handler

    if int(hci_dev) < 0:
        print("No device specified, exiting run_ble")
        return 1

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

    # Start BLE probe
    btctrl.send_scan_request()
    try:
        event_loop.run_forever()
    except KeyboardInterrupt:
        print("\nKeyboard interrupt!")
    finally:
        print("Closing ble event loop.")
        btctrl.stop_scan_request()
        command = aiobs.HCI_Cmd_LE_Advertise(enable=False)
        btctrl.send_command(command)
        conn.close()
        event_loop.close()

        # TIMING
        print(my_timer.get_count(), "ble messages.")
        print(
            1000 * 1000 * my_timer.get_average(),
            "usec in average per message in run_ble.callback_data_handler().",
        )
        # ------------------------------

    print("Exiting run_ble.")
    return 0
    # EOF run_ble
