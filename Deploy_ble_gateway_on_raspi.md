# Test ble_gateway on fresh Raspberry pi

Assumes Rasbian Buster Lite

## Requires
- locales
-- edit /etc/locale.gen (en_GB.UTF-8, fi_FI.UTF-8)
- git
- pipenv
- Raspberry pi is SLOW, especially zero -> increase pipenv timeout

```sh
sudo locale-gen
sudo apt-get install git
sudo apt-get install pipenv

# git globals
git config --global user.email "suominen.jani@gmail.com"  
git config --global user.name "jasunen"  

# clone repo
git clone https://jasunen:<PASSWORD>@github.com/jasunen/ble_gateway.git
# Enter project directory
cd <repo_name>

# Install dependencies
export PIPENV_TIMEOUT=700 # default timeout of 30s is far too low on raspi
pipenv install
```

## Testing the module
Using bluetooth device requires root access due RAW_SOCKET use but pipenv does not support sudoing.
Adding pi to "bluetooth" group deos not help and setcap does not work with scripts (??)
Some discussion in:
- https://stackoverflow.com/questions/37287026/bluez-library-access-as-non-root-user
- https://stackoverflow.com/questions/36701640/how-do-i-execute-pybluez-samples-using-bluez5-library-as-normal-user-without-su
- https://unix.stackexchange.com/questions/96106/bluetooth-le-scan-as-non-root
- https://github.com/ev3dev/ev3dev/issues/274
- https://github.com/zer0n1/python-icmp-non-root

Current solution is to start python in virtualenv directly with sudo.
i.e. sudo ~/.virtualenvs/ble_gateway-VBqUUIZs/bin/python -m ble_gateway

Run make_run_script.sh the ble_gateway root directory. It will create script for running the module using sudo for python in virtualenv.

```sh
. make_run_script.sh
. run_ble.sh
```

# update from github
```sh
git stash # stash all local edits
git pull # pull from github repo
# update run script as above
```
