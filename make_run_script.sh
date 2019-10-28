#!/usr/bin/env bash

# Expecting BASH
# To run tun this type:
# . make_ble_run.sh

VIRTPYTHON="$(pipenv run which python)"
RUN_BLE="run_ble.sh"
echo "sudo ${VIRTPYTHON} -m ble_gateway \$*" > $RUN_BLE

echo "Created $RUN_BLE:"
cat $RUN_BLE
echo $'\nNow type \n.'
echo "$RUN_BLE [args]"
echo "to run module as sudo"
