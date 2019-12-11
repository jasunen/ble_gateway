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

# Run on reboot
Create a script which loops following:
- runs ble_gateway module using above run_ble.sh script
- on exit checks network connectivity
- if no network: reboot if uptime > 20 minutes (to avoid boot loops)
- if uptime < 20 minutes: wait 3 minutes and reset networking
```sh
#!/bin/bash

while true; do
	cd /home/pi/ble_gateway
	date
	echo STARTING run_ble
	. run_ble.sh
	date
	echo run_ble exiting
	ping -c4 raspi1 > /dev/null

	if [ $? != 0 ]; then
	echo NO NETWORK DETECTED
	read -d. uptime_seconds < /proc/uptime

	if (( $uptime_seconds > 20*60 )); then
		date
		echo REBOOTING after $uptime_seconds seconds of uptime
		sudo /sbin/shutdown -r now
	fi
	echo Not rebooting yet, uptime $uptime_seconds seconds, trying network reset first!
  sleep 180
	sudo service networking restart
	sudo ifconfig wlan0 down
	sleep 10
	sudo ifconfig wlan0 up
	else
	echo Network fine!
	fi

	echo Restarting ble_gateway!
	sleep 10
done```

User pi crontab:
```sh
# Add following line to crontab
@reboot sleep 10 && /home/pi/ble_gateway_reboot.sh >> $HOME/ble_gateway_reboot.log 2>&1
```
